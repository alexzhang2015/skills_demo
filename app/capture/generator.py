"""
SKILL.md 生成器

从录制的操作序列自动生成 SKILL.md 文件
"""

import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

from .recorder import RecordingSession, RecordedAction, ActionType


@dataclass
class ExtractedParameter:
    """提取的参数"""
    name: str
    param_type: str  # string, number, date, enum, array
    description: str
    required: bool = True
    default: Optional[Any] = None
    example: Optional[Any] = None
    options: List[str] = field(default_factory=list)  # for enum type

    def to_yaml(self) -> str:
        """转换为 YAML 格式"""
        lines = [
            f"  - name: {self.name}",
            f"    type: {self.param_type}",
            f"    required: {str(self.required).lower()}",
            f"    description: {self.description}",
        ]
        if self.default is not None:
            lines.append(f"    default: {self.default}")
        if self.example is not None:
            lines.append(f'    example: "{self.example}"')
        if self.options:
            lines.append(f"    options: [{', '.join(self.options)}]")
        return "\n".join(lines)


@dataclass
class GeneratedStep:
    """生成的步骤"""
    step_number: int
    title: str
    description: str
    actions: List[str]  # Markdown 格式的操作描述
    code_block: Optional[str] = None  # 代码块
    notes: List[str] = field(default_factory=list)  # 注意事项

    def to_markdown(self) -> str:
        """转换为 Markdown"""
        lines = [f"### Step {self.step_number}: {self.title}", ""]

        if self.description:
            lines.append(self.description)
            lines.append("")

        if self.actions:
            lines.append("```")
            for action in self.actions:
                lines.append(action)
            lines.append("```")
            lines.append("")

        if self.notes:
            lines.append("**注意：**")
            for note in self.notes:
                lines.append(f"- {note}")
            lines.append("")

        return "\n".join(lines)


@dataclass
class GeneratedSkill:
    """生成的 Skill"""
    name: str
    description: str
    version: str = "1.0"
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # 输入参数
    parameters: List[ExtractedParameter] = field(default_factory=list)

    # 步骤
    steps: List[GeneratedStep] = field(default_factory=list)

    # 前置条件和常见问题
    prerequisites: List[str] = field(default_factory=list)
    faqs: List[Dict[str, str]] = field(default_factory=list)

    # 工具列表
    allowed_tools: List[str] = field(default_factory=list)

    # 元数据
    source_recording_id: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_skill_md(self) -> str:
        """生成 SKILL.md 内容"""
        lines = []

        # YAML Frontmatter
        lines.append("---")
        lines.append(f"name: {self.name}")
        lines.append(f"description: |")
        for line in self.description.split("\n"):
            lines.append(f"  {line}")

        if self.allowed_tools:
            lines.append("allowed-tools:")
            for tool in self.allowed_tools:
                lines.append(f"  - {tool}")

        lines.append(f'version: "{self.version}"')

        if self.category:
            lines.append(f"category: {self.category}")

        if self.tags:
            lines.append(f"tags: [{', '.join(self.tags)}]")

        # 输入参数
        if self.parameters:
            lines.append("")
            lines.append("inputs:")
            for param in self.parameters:
                lines.append(param.to_yaml())

        lines.append("---")
        lines.append("")

        # 标题
        lines.append(f"# {self.name.replace('-', ' ').title()}")
        lines.append("")

        # 场景说明
        lines.append("## 场景说明")
        lines.append("")
        lines.append(self.description)
        lines.append("")

        # 前置条件
        if self.prerequisites:
            lines.append("## 前置条件")
            lines.append("")
            for prereq in self.prerequisites:
                lines.append(f"- {prereq}")
            lines.append("")

        # 执行步骤
        lines.append("## 执行步骤")
        lines.append("")
        for step in self.steps:
            lines.append(step.to_markdown())

        # 常见问题
        if self.faqs:
            lines.append("## 常见问题处理")
            lines.append("")
            for i, faq in enumerate(self.faqs, 1):
                lines.append(f"### Q{i}: {faq['question']}")
                lines.append(f"- 原因：{faq.get('cause', '待补充')}")
                lines.append(f"- 解决：{faq.get('solution', '待补充')}")
                lines.append("")

        # 元数据
        lines.append("## 变更记录")
        lines.append("")
        lines.append("| 版本 | 日期 | 变更说明 | 作者 |")
        lines.append("|------|------|---------|------|")
        lines.append(f"| {self.version} | {self.generated_at.strftime('%Y-%m')} | 从录制生成 | - |")
        lines.append("")

        return "\n".join(lines)


class SkillGenerator:
    """
    SKILL.md 生成器

    功能：
    - 分析录制的操作序列
    - 提取参数和变量
    - 生成结构化的步骤
    - 输出 SKILL.md 格式
    """

    # 参数提取模式
    PARAM_PATTERNS = {
        "price": (r"\d+\.?\d*", "number", "价格"),
        "date": (r"\d{4}[-/]\d{2}[-/]\d{2}", "date", "日期"),
        "sku": (r"SKU[\w-]+", "string", "SKU编码"),
        "name": (r"[\u4e00-\u9fa5]{2,20}", "string", "名称"),
        "phone": (r"1[3-9]\d{9}", "string", "手机号"),
        "email": (r"[\w.-]+@[\w.-]+", "string", "邮箱"),
    }

    # 步骤合并规则
    MERGE_RULES = {
        # 连续的填充操作合并为表单填写
        "form_fill": [ActionType.FILL, ActionType.TYPE, ActionType.SELECT],
        # 导航 + 等待合并
        "navigation": [ActionType.NAVIGATE, ActionType.WAIT_FOR_ELEMENT],
    }

    def __init__(self):
        pass

    def generate(
        self,
        recording: RecordingSession,
        skill_name: str = None,
        category: str = None,
        **options
    ) -> GeneratedSkill:
        """
        从录制生成 Skill

        Args:
            recording: 录制会话
            skill_name: Skill 名称（可选，自动生成）
            category: 分类
            **options: 其他选项

        Returns:
            GeneratedSkill
        """
        # 生成名称
        if not skill_name:
            skill_name = self._generate_name(recording)

        # 提取参数
        parameters = self._extract_parameters(recording.actions)

        # 生成步骤
        steps = self._generate_steps(recording.actions)

        # 提取工具列表
        allowed_tools = self._extract_tools(recording.actions)

        # 生成描述
        description = self._generate_description(recording, steps)

        # 推断前置条件
        prerequisites = self._infer_prerequisites(recording)

        # 生成标签
        tags = self._generate_tags(recording, category)

        return GeneratedSkill(
            name=skill_name,
            description=description,
            category=category,
            tags=tags,
            parameters=parameters,
            steps=steps,
            prerequisites=prerequisites,
            allowed_tools=allowed_tools,
            source_recording_id=recording.session_id,
        )

    def _generate_name(self, recording: RecordingSession) -> str:
        """生成 Skill 名称"""
        if recording.name:
            # 转换为 kebab-case
            name = recording.name.lower()
            name = re.sub(r"[^\w\s-]", "", name)
            name = re.sub(r"[\s_]+", "-", name)
            return name

        # 从 URL 推断
        if recording.start_url:
            # 提取路径中的关键词
            path = recording.start_url.split("/")[-1]
            if path and not path.startswith("?"):
                return path.split("?")[0].replace("_", "-")

        return f"recorded-skill-{recording.session_id[:6]}"

    def _extract_parameters(self, actions: List[RecordedAction]) -> List[ExtractedParameter]:
        """提取参数"""
        parameters = []
        seen_params = set()

        for action in actions:
            if action.action_type not in (ActionType.FILL, ActionType.TYPE, ActionType.SELECT):
                continue

            if not action.value:
                continue

            # 检查值是否匹配参数模式
            for param_name, (pattern, param_type, desc) in self.PARAM_PATTERNS.items():
                if re.search(pattern, action.value):
                    if param_name not in seen_params:
                        seen_params.add(param_name)
                        parameters.append(ExtractedParameter(
                            name=param_name,
                            param_type=param_type,
                            description=desc,
                            example=action.value,
                        ))
                    break
            else:
                # 从元素信息推断参数
                if action.selector:
                    param = self._infer_param_from_selector(action)
                    if param and param.name not in seen_params:
                        seen_params.add(param.name)
                        parameters.append(param)

        return parameters

    def _infer_param_from_selector(self, action: RecordedAction) -> Optional[ExtractedParameter]:
        """从选择器推断参数"""
        selector = action.selector
        if not selector:
            return None

        # 从属性推断
        attrs = selector.attributes
        name = attrs.get("name") or attrs.get("id") or attrs.get("placeholder", "")

        if not name:
            return None

        # 转换为参数名
        param_name = name.lower().replace("-", "_").replace(" ", "_")
        param_name = re.sub(r"[^\w]", "", param_name)

        if not param_name:
            return None

        # 推断类型
        input_type = attrs.get("type", "text")
        if input_type == "number":
            param_type = "number"
        elif input_type == "date":
            param_type = "date"
        elif input_type == "email":
            param_type = "string"
        else:
            param_type = "string"

        return ExtractedParameter(
            name=param_name,
            param_type=param_type,
            description=attrs.get("placeholder") or name,
            example=action.value,
        )

    def _generate_steps(self, actions: List[RecordedAction]) -> List[GeneratedStep]:
        """生成步骤"""
        steps = []
        current_step_actions = []
        current_page = None
        step_number = 0

        for action in actions:
            # 页面切换时创建新步骤
            if action.page_url and action.page_url != current_page:
                if current_step_actions:
                    step_number += 1
                    steps.append(self._create_step(step_number, current_step_actions, current_page))
                    current_step_actions = []
                current_page = action.page_url

            current_step_actions.append(action)

            # 某些操作后创建新步骤
            if action.action_type in (ActionType.CLICK,) and "submit" in str(action.selector).lower():
                step_number += 1
                steps.append(self._create_step(step_number, current_step_actions, current_page))
                current_step_actions = []

        # 处理剩余操作
        if current_step_actions:
            step_number += 1
            steps.append(self._create_step(step_number, current_step_actions, current_page))

        return steps

    def _create_step(
        self,
        step_number: int,
        actions: List[RecordedAction],
        page_url: str = None
    ) -> GeneratedStep:
        """创建步骤"""
        # 生成标题
        title = self._generate_step_title(actions, page_url)

        # 生成描述
        description = self._generate_step_description(actions)

        # 生成操作列表
        action_lines = []
        for i, action in enumerate(actions, 1):
            action_lines.append(f"{i}. {action.get_description()}")

        return GeneratedStep(
            step_number=step_number,
            title=title,
            description=description,
            actions=action_lines,
        )

    def _generate_step_title(self, actions: List[RecordedAction], page_url: str = None) -> str:
        """生成步骤标题"""
        # 从 URL 推断
        if page_url:
            path_parts = page_url.split("/")
            for part in reversed(path_parts):
                if part and not part.startswith("?") and not part.isdigit():
                    # 转换为标题
                    title = part.replace("-", " ").replace("_", " ").title()
                    return title

        # 从操作推断
        if actions:
            first_action = actions[0]
            if first_action.action_type == ActionType.NAVIGATE:
                return "打开页面"
            elif first_action.action_type == ActionType.FILL:
                return "填写表单"
            elif first_action.action_type == ActionType.CLICK:
                target = first_action.selector.get_description() if first_action.selector else ""
                return f"点击 {target}"

        return "执行操作"

    def _generate_step_description(self, actions: List[RecordedAction]) -> str:
        """生成步骤描述"""
        action_types = [a.action_type for a in actions]

        fill_count = action_types.count(ActionType.FILL) + action_types.count(ActionType.TYPE)
        click_count = action_types.count(ActionType.CLICK)

        if fill_count > 2:
            return "在此页面填写以下信息："
        elif click_count > 0:
            return "执行以下操作："

        return ""

    def _extract_tools(self, actions: List[RecordedAction]) -> List[str]:
        """提取需要的工具"""
        tools = set()

        for action in actions:
            if action.action_type in (ActionType.NAVIGATE, ActionType.CLICK, ActionType.FILL):
                tools.add("mcp__playwright__browser_navigate")
                tools.add("mcp__playwright__browser_click")
                tools.add("mcp__playwright__browser_fill")
                tools.add("mcp__playwright__browser_snapshot")
                break

        return sorted(list(tools))

    def _generate_description(self, recording: RecordingSession, steps: List[GeneratedStep]) -> str:
        """生成 Skill 描述"""
        parts = []

        if recording.description:
            parts.append(recording.description)
        else:
            step_count = len(steps)
            page_count = len(recording.pages_visited)
            parts.append(f"自动化执行 {step_count} 个步骤，涉及 {page_count} 个页面。")

        # 添加触发条件
        if recording.start_url:
            domain = recording.start_url.split("/")[2] if "//" in recording.start_url else ""
            if domain:
                parts.append(f"适用于 {domain} 相关操作。")

        return "\n".join(parts)

    def _infer_prerequisites(self, recording: RecordingSession) -> List[str]:
        """推断前置条件"""
        prerequisites = []

        # 检查是否需要登录
        if recording.pages_visited:
            for url in recording.pages_visited:
                if "login" in url.lower() or "signin" in url.lower():
                    prerequisites.append("已登录相关系统")
                    break

        # 检查浏览器要求
        if recording.browser_info:
            browser = recording.browser_info.get("browserType", "")
            if browser:
                prerequisites.append(f"使用 {browser} 浏览器")

        return prerequisites

    def _generate_tags(self, recording: RecordingSession, category: str = None) -> List[str]:
        """生成标签"""
        tags = []

        if category:
            tags.append(category)

        # 从 URL 推断
        if recording.start_url:
            url_lower = recording.start_url.lower()
            if "pos" in url_lower:
                tags.append("POS")
            if "erp" in url_lower or "admin" in url_lower:
                tags.append("后台")
            if "app" in url_lower or "mobile" in url_lower:
                tags.append("App")

        tags.append("自动生成")

        return tags


# 全局生成器实例
_generator: Optional[SkillGenerator] = None


def get_generator() -> SkillGenerator:
    """获取生成器实例"""
    global _generator
    if _generator is None:
        _generator = SkillGenerator()
    return _generator
