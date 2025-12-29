"""
Claude Skills 执行引擎
接入 Claude API，支持真正的工具调用
"""
import os
import uuid
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Generator
from dataclasses import dataclass, field

from dotenv import load_dotenv
import anthropic

# Load .env file
load_dotenv()

# Clear SOCKS proxy to avoid httpx issues
if os.environ.get("ALL_PROXY", "").startswith("socks"):
    os.environ.pop("ALL_PROXY", None)

from .models import (
    Skill,
    SkillCreate,
    SkillUpdate,
    ExecutionResult,
    ExecutionStep,
    SkillStatus,
)
from .skill_parser import SkillParser, SkillLoader, ParsedSkill, SkillMetadata
from .tools import ToolExecutor, get_tool_definitions, ToolResult
from .semantic_matcher import SemanticMatcher, KeywordMatcher, MatchResult


@dataclass
class SkillMatch:
    """技能匹配结果"""
    skill: ParsedSkill
    score: float
    confidence: str
    triggered_by: str  # "semantic" or "keyword" or "exact"


class ClaudeSkillsEngine:
    """
    Claude Skills 执行引擎

    Features:
    - Claude API 集成：使用 Claude 解析和执行指令
    - 工具调用：支持 Bash、Read、Write 等工具
    - 语义触发：自动匹配用户输入和 Skill
    - 渐进式加载：按需加载 Skill 内容
    - SKILL.md 格式：支持标准格式
    """

    def __init__(
        self,
        skills_dir: str = None,
        api_key: str = None,
        model: str = "claude-sonnet-4-20250514",
        working_dir: str = None
    ):
        # Claude API 客户端
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.client = None
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

        # 工作目录
        self.working_dir = working_dir or os.getcwd()

        # Skills 目录和加载器
        self.skills_dir = Path(skills_dir) if skills_dir else Path(self.working_dir) / "skills"
        self.loader = SkillLoader(self.skills_dir)
        self.parser = SkillParser()

        # 语义匹配器
        self.semantic_matcher = SemanticMatcher(backend="auto")
        self.keyword_matcher = KeywordMatcher()

        # 内存存储（用于 Web UI 创建的 Skills）
        self._memory_skills: dict[str, ParsedSkill] = {}
        self._executions: dict[str, ExecutionResult] = {}

        # 初始化
        self._init_skills()

    def _init_skills(self):
        """初始化 Skills"""
        # 确保 skills 目录存在
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        # Level 1: 加载所有 Skill 元数据
        self.loader.load_all_metadata()

        # 如果没有文件系统 Skills，创建示例 Skills
        if not self.loader.list_skills() and not self._memory_skills:
            self._create_demo_skills()

    def _create_demo_skills(self):
        """创建示例 Skills"""
        demo_skills = [
            {
                "name": "file-reader",
                "description": "Read and analyze file contents. Use when user wants to view, read, or understand file contents.",
                "content": """# File Reader

## Instructions

When the user wants to read or analyze a file:

1. Use the `read` tool to get the file contents
2. Analyze the content based on user's request
3. Provide a summary or the requested information

## Examples

User: "Show me the contents of config.json"
Action: Read the file and display its contents

User: "What's in the README?"
Action: Read README.md and summarize the key points
"""
            },
            {
                "name": "code-runner",
                "description": "Execute code and shell commands. Use when user wants to run scripts, commands, or code.",
                "content": """# Code Runner

## Instructions

When the user wants to run code or commands:

1. Understand what the user wants to execute
2. Use the `bash` tool to run the command
3. Report the results, including any errors

## Safety

- Never run destructive commands without confirmation
- Validate command inputs
- Set reasonable timeouts

## Examples

User: "Run the tests"
Action: Execute `pytest` or the project's test command

User: "List all Python files"
Action: Run `find . -name "*.py"` or use glob tool
"""
            },
            {
                "name": "git-helper",
                "description": "Help with git operations. Use for commits, branches, status, diffs, and other git tasks.",
                "content": """# Git Helper

## Instructions

Help users with git operations:

1. For status: Run `git status` to show current state
2. For commits: Stage changes and create descriptive commits
3. For branches: Help create, switch, or manage branches
4. For diffs: Show relevant diffs

## Commit Message Format

- Use conventional commit format when appropriate
- Keep subject line under 50 characters
- Add body for complex changes

## Examples

User: "What changed?"
Action: Run `git status` and `git diff`

User: "Commit these changes"
Action: Stage changes and create a commit with a good message
"""
            },
        ]

        for skill_data in demo_skills:
            content = f"""---
name: {skill_data['name']}
description: {skill_data['description']}
---

{skill_data['content']}"""

            skill = self.parser.parse_content(content, skill_data['name'])
            self._memory_skills[skill_data['name']] = skill

    # ==================== Skill 管理 ====================

    def get_all_skills(self) -> list[Skill]:
        """获取所有 Skills（兼容旧 API）"""
        skills = []

        # 文件系统 Skills
        for name in self.loader.list_skills():
            metadata = self.loader.get_metadata(name)
            if metadata:
                skills.append(Skill(
                    id=name,
                    name=name,
                    description=metadata.description,
                    prompt=f"[SKILL.md file at {self.skills_dir / name}]"
                ))

        # 内存 Skills
        for name, skill in self._memory_skills.items():
            skills.append(Skill(
                id=name,
                name=name,
                description=skill.description,
                prompt=skill.instructions.content if skill.instructions else ""
            ))

        return skills

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取单个 Skill"""
        # 先检查内存
        if skill_id in self._memory_skills:
            skill = self._memory_skills[skill_id]
            return Skill(
                id=skill_id,
                name=skill.name,
                description=skill.description,
                prompt=skill.instructions.content if skill.instructions else ""
            )

        # 检查文件系统
        parsed = self.loader.load_skill(skill_id)
        if parsed:
            return Skill(
                id=skill_id,
                name=parsed.name,
                description=parsed.description,
                prompt=parsed.instructions.content if parsed.instructions else ""
            )

        return None

    def create_skill(self, skill_data: SkillCreate) -> Skill:
        """创建新 Skill"""
        # 构建 SKILL.md 格式内容
        content = f"""---
name: {skill_data.name}
description: {skill_data.description}
---

{skill_data.prompt}
"""
        skill = self.parser.parse_content(content, skill_data.name)
        self._memory_skills[skill_data.name] = skill

        return Skill(
            id=skill_data.name,
            name=skill_data.name,
            description=skill_data.description,
            prompt=skill_data.prompt
        )

    def update_skill(self, skill_id: str, update_data: SkillUpdate) -> Optional[Skill]:
        """更新 Skill"""
        if skill_id not in self._memory_skills:
            return None

        skill = self._memory_skills[skill_id]

        # 更新元数据
        if update_data.name is not None:
            skill.metadata.name = update_data.name
        if update_data.description is not None:
            skill.metadata.description = update_data.description
        if update_data.prompt is not None and skill.instructions:
            skill.instructions.content = update_data.prompt

        return self.get_skill(skill_id)

    def delete_skill(self, skill_id: str) -> bool:
        """删除 Skill"""
        if skill_id in self._memory_skills:
            del self._memory_skills[skill_id]
            return True
        return False

    # ==================== 语义匹配 ====================

    def match_skills(self, query: str, top_k: int = 3) -> list[SkillMatch]:
        """
        根据用户输入匹配 Skills

        Args:
            query: 用户输入
            top_k: 返回最多 k 个匹配

        Returns:
            匹配的 Skills 列表
        """
        # 收集所有 Skill 的元数据
        skill_list = []

        for name in self.loader.list_skills():
            metadata = self.loader.get_metadata(name)
            if metadata:
                skill_list.append((name, metadata.description))

        for name, skill in self._memory_skills.items():
            skill_list.append((name, skill.description))

        if not skill_list:
            return []

        # 1. 先用关键词快速筛选
        keyword_results = self.keyword_matcher.quick_match(query, skill_list)

        # 2. 对前 N 个候选进行语义匹配
        candidates = keyword_results[:min(10, len(keyword_results))]
        semantic_results = self.semantic_matcher.match(
            query,
            [(name, desc) for name, desc, _ in candidates],
            threshold=0.3
        )

        # 3. 构建最终结果
        matches = []
        for result in semantic_results[:top_k]:
            # Level 2: 加载完整 Skill
            skill = self._load_full_skill(result.skill_name)
            if skill:
                matches.append(SkillMatch(
                    skill=skill,
                    score=result.score,
                    confidence=result.confidence,
                    triggered_by="semantic"
                ))

        return matches

    def _load_full_skill(self, skill_name: str) -> Optional[ParsedSkill]:
        """加载完整 Skill（Level 2）"""
        if skill_name in self._memory_skills:
            return self._memory_skills[skill_name]
        return self.loader.load_skill(skill_name)

    # ==================== 执行引擎 ====================

    def execute_skill(
        self,
        skill_id: str,
        args: Optional[str] = None,
        stream: bool = False
    ) -> ExecutionResult:
        """
        执行 Skill

        Args:
            skill_id: Skill ID/名称
            args: 用户输入参数
            stream: 是否使用流式输出

        Returns:
            执行结果
        """
        execution_id = str(uuid.uuid4())[:8]
        started_at = datetime.now()

        # 创建执行结果
        result = ExecutionResult(
            execution_id=execution_id,
            skill_id=skill_id,
            skill_name=skill_id,
            status=SkillStatus.RUNNING,
            input_args=args,
            started_at=started_at,
        )

        # Level 2: 加载完整 Skill
        skill = self._load_full_skill(skill_id)
        if not skill:
            result.status = SkillStatus.ERROR
            result.error = f"Skill '{skill_id}' not found"
            return result

        result.skill_name = skill.name

        # 获取允许的工具
        allowed_tools = skill.metadata.allowed_tools if skill.metadata.allowed_tools else None

        # 如果有 Claude API，使用 Claude 执行
        if self.client:
            try:
                result = self._execute_with_claude(
                    skill, args, result, allowed_tools
                )
            except Exception as e:
                result.status = SkillStatus.ERROR
                result.error = f"Claude API error: {str(e)}"
        else:
            # 回退到简单执行
            result = self._execute_simple(skill, args, result)

        result.completed_at = datetime.now()
        result.total_duration_ms = (result.completed_at - started_at).total_seconds() * 1000

        self._executions[execution_id] = result
        return result

    def _execute_with_claude(
        self,
        skill: ParsedSkill,
        user_input: Optional[str],
        result: ExecutionResult,
        allowed_tools: list[str] = None
    ) -> ExecutionResult:
        """使用 Claude API 执行 Skill"""
        # 构建系统提示
        system_prompt = f"""You are executing a skill called "{skill.name}".

{skill.instructions.content if skill.instructions else "No specific instructions."}

Follow the instructions above to help the user. Use the available tools when needed.
Be concise and focused on completing the task."""

        # 构建用户消息
        user_message = user_input or "Execute this skill."

        # 获取工具定义
        tools = get_tool_definitions(allowed_tools)

        # 工具执行器
        tool_executor = ToolExecutor(
            working_dir=self.working_dir,
            allowed_tools=allowed_tools
        )

        # 调用 Claude API
        messages = [{"role": "user", "content": user_message}]
        step_id = 0

        while True:
            step_id += 1
            step_start = time.time()

            # 添加执行步骤
            step = ExecutionStep(
                step_id=step_id,
                action="Calling Claude API",
                detail="Processing request...",
                status=SkillStatus.RUNNING,
            )
            result.steps.append(step)

            # 调用 Claude
            response = self.client.messages.create(
                model=skill.metadata.model or self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=tools if tools else None,
                messages=messages
            )

            step.duration_ms = (time.time() - step_start) * 1000

            # 处理响应
            if response.stop_reason == "end_turn":
                # 完成执行
                step.action = "Claude response"
                step.status = SkillStatus.SUCCESS

                # 提取最终结果
                for block in response.content:
                    if hasattr(block, 'text'):
                        step.detail = block.text[:200] + "..." if len(block.text) > 200 else block.text
                        result.final_result = block.text
                        break

                result.status = SkillStatus.SUCCESS
                break

            elif response.stop_reason == "tool_use":
                # 需要执行工具
                assistant_message = {"role": "assistant", "content": response.content}
                messages.append(assistant_message)

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        step.action = f"Tool: {tool_name}"
                        step.detail = json.dumps(tool_input)[:200]

                        # 执行工具
                        tool_result = tool_executor.execute(tool_name, tool_input)

                        step.result = tool_result.output[:500] if tool_result.output else tool_result.error
                        step.status = SkillStatus.SUCCESS if tool_result.success else SkillStatus.ERROR

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result.output if tool_result.success else f"Error: {tool_result.error}"
                        })

                        # 添加新步骤记录工具结果
                        step_id += 1
                        tool_step = ExecutionStep(
                            step_id=step_id,
                            action=f"Tool result: {tool_name}",
                            detail=tool_result.output[:200] if tool_result.output else "",
                            status=SkillStatus.SUCCESS if tool_result.success else SkillStatus.ERROR,
                            result=tool_result.output[:500] if tool_result.output else tool_result.error,
                            duration_ms=tool_result.duration_ms
                        )
                        result.steps.append(tool_step)

                messages.append({"role": "user", "content": tool_results})

            else:
                # 其他停止原因
                step.status = SkillStatus.ERROR
                step.detail = f"Unexpected stop reason: {response.stop_reason}"
                result.status = SkillStatus.ERROR
                result.error = f"Unexpected stop reason: {response.stop_reason}"
                break

            # 防止无限循环
            if step_id > 20:
                result.status = SkillStatus.ERROR
                result.error = "Exceeded maximum steps (20)"
                break

        return result

    def _execute_simple(
        self,
        skill: ParsedSkill,
        user_input: Optional[str],
        result: ExecutionResult
    ) -> ExecutionResult:
        """简单执行（不使用 Claude API）"""
        step = ExecutionStep(
            step_id=1,
            action="Simple execution",
            detail=f"Executing skill: {skill.name}",
            status=SkillStatus.RUNNING,
        )
        result.steps.append(step)

        # 模拟执行
        time.sleep(0.1)

        step.status = SkillStatus.SUCCESS
        step.result = f"Skill '{skill.name}' executed with input: {user_input or 'none'}"
        step.duration_ms = 100

        result.final_result = f"""Skill: {skill.name}
Description: {skill.description}
Input: {user_input or 'none'}

Note: Claude API not configured. Set ANTHROPIC_API_KEY for full functionality."""

        result.status = SkillStatus.SUCCESS
        return result

    # ==================== 执行历史 ====================

    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """获取执行记录"""
        return self._executions.get(execution_id)

    def get_all_executions(self) -> list[ExecutionResult]:
        """获取所有执行记录"""
        return list(self._executions.values())


# 全局引擎实例
engine: Optional[ClaudeSkillsEngine] = None


def get_engine() -> ClaudeSkillsEngine:
    """获取或创建引擎实例"""
    global engine
    if engine is None:
        engine = ClaudeSkillsEngine()
    return engine
