"""
Skill 优化器

对生成的 Skill 进行参数化、泛化和增强
"""

import re
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Set

from .generator import GeneratedSkill, ExtractedParameter, GeneratedStep


@dataclass
class RefineOptions:
    """优化选项"""
    # 参数化
    parameterize: bool = True           # 是否参数化
    extract_variables: bool = True       # 提取变量
    add_default_values: bool = True      # 添加默认值

    # 泛化
    generalize_selectors: bool = True    # 泛化选择器
    add_fallback_selectors: bool = True  # 添加备选选择器
    make_steps_reusable: bool = True     # 使步骤可复用

    # 增强
    add_error_handling: bool = True      # 添加错误处理
    add_retry_logic: bool = True         # 添加重试逻辑
    add_logging: bool = True             # 添加日志
    add_assertions: bool = True          # 添加断言

    # 文档
    add_examples: bool = True            # 添加示例
    add_faqs: bool = True                # 添加常见问题


@dataclass
class RefineResult:
    """优化结果"""
    skill: GeneratedSkill
    changes_made: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class SkillRefiner:
    """
    Skill 优化器

    功能：
    - 参数化：提取变量，替换硬编码值
    - 泛化：使用更稳定的选择器，添加容错
    - 增强：添加错误处理、重试、日志
    - 文档：添加示例、常见问题
    """

    # 常见的硬编码模式
    HARDCODED_PATTERNS = {
        "price": r"\d+\.?\d*\s*(元|¥|\$)?",
        "date": r"\d{4}[-/]\d{2}[-/]\d{2}",
        "datetime": r"\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}",
        "phone": r"1[3-9]\d{9}",
        "email": r"[\w.-]+@[\w.-]+\.\w+",
        "url": r"https?://[\w./\-?=&]+",
        "id": r"[A-Z]{2,4}[-_]?\d{4,}",
    }

    # 不稳定的选择器模式
    UNSTABLE_SELECTOR_PATTERNS = [
        r"\[class\*='_\w+'\]",        # 动态生成的类名
        r":nth-child\(\d+\)",          # 位置选择器
        r"\[style=",                   # 样式选择器
        r"#\d+",                       # 数字 ID
    ]

    # 常见错误场景
    COMMON_ERROR_SCENARIOS = [
        {"trigger": "网络超时", "solution": "等待 5 秒后重试"},
        {"trigger": "元素不存在", "solution": "检查页面是否完全加载"},
        {"trigger": "权限不足", "solution": "确认用户权限"},
    ]

    def __init__(self):
        pass

    def refine(
        self,
        skill: GeneratedSkill,
        options: RefineOptions = None
    ) -> RefineResult:
        """
        优化 Skill

        Args:
            skill: 待优化的 Skill
            options: 优化选项

        Returns:
            RefineResult
        """
        options = options or RefineOptions()
        result = RefineResult(skill=skill)

        # 1. 参数化
        if options.parameterize:
            self._parameterize(skill, result)

        # 2. 泛化
        if options.generalize_selectors:
            self._generalize_selectors(skill, result)

        # 3. 添加错误处理
        if options.add_error_handling:
            self._add_error_handling(skill, result)

        # 4. 添加重试逻辑
        if options.add_retry_logic:
            self._add_retry_logic(skill, result)

        # 5. 添加文档
        if options.add_examples:
            self._add_examples(skill, result)

        if options.add_faqs:
            self._add_faqs(skill, result)

        return result

    def _parameterize(self, skill: GeneratedSkill, result: RefineResult):
        """参数化处理"""
        existing_params = {p.name for p in skill.parameters}

        for step in skill.steps:
            for i, action in enumerate(step.actions):
                # 检查硬编码值
                for param_name, pattern in self.HARDCODED_PATTERNS.items():
                    matches = re.findall(pattern, action)
                    if matches:
                        # 替换为参数引用
                        for match in matches:
                            param_ref = f"${{{param_name}}}"
                            step.actions[i] = action.replace(match, param_ref)

                        # 添加参数定义
                        if param_name not in existing_params:
                            existing_params.add(param_name)
                            skill.parameters.append(ExtractedParameter(
                                name=param_name,
                                param_type=self._infer_param_type(param_name),
                                description=self._get_param_description(param_name),
                                example=matches[0],
                            ))
                            result.changes_made.append(f"添加参数: {param_name}")

    def _infer_param_type(self, param_name: str) -> str:
        """推断参数类型"""
        type_map = {
            "price": "number",
            "date": "date",
            "datetime": "datetime",
            "phone": "string",
            "email": "string",
            "url": "string",
            "id": "string",
        }
        return type_map.get(param_name, "string")

    def _get_param_description(self, param_name: str) -> str:
        """获取参数描述"""
        desc_map = {
            "price": "价格（数字）",
            "date": "日期（YYYY-MM-DD）",
            "datetime": "日期时间（YYYY-MM-DD HH:mm）",
            "phone": "手机号",
            "email": "邮箱地址",
            "url": "URL 地址",
            "id": "编号/ID",
        }
        return desc_map.get(param_name, param_name)

    def _generalize_selectors(self, skill: GeneratedSkill, result: RefineResult):
        """泛化选择器"""
        for step in skill.steps:
            for i, action in enumerate(step.actions):
                # 检查不稳定的选择器
                for pattern in self.UNSTABLE_SELECTOR_PATTERNS:
                    if re.search(pattern, action):
                        result.warnings.append(
                            f"步骤 {step.step_number} 包含不稳定的选择器: {pattern}"
                        )
                        result.suggestions.append(
                            f"建议使用 data-testid 或 role 选择器替代"
                        )

    def _add_error_handling(self, skill: GeneratedSkill, result: RefineResult):
        """添加错误处理"""
        # 在步骤中添加错误处理注释
        for step in skill.steps:
            # 检查是否有可能失败的操作
            has_network_op = any(
                "导航" in a or "提交" in a or "保存" in a
                for a in step.actions
            )

            if has_network_op and not step.notes:
                step.notes.append("如果操作超时，请检查网络连接后重试")
                result.changes_made.append(f"步骤 {step.step_number}: 添加错误处理提示")

    def _add_retry_logic(self, skill: GeneratedSkill, result: RefineResult):
        """添加重试逻辑"""
        # 在元数据中添加重试配置
        if "retry" not in skill.tags:
            skill.tags.append("支持重试")
            result.changes_made.append("添加重试支持标签")

    def _add_examples(self, skill: GeneratedSkill, result: RefineResult):
        """添加使用示例"""
        if skill.parameters:
            # 在描述中添加示例
            example_lines = ["\n\n**使用示例：**\n"]
            example_lines.append("```yaml")
            for param in skill.parameters:
                if param.example:
                    example_lines.append(f"{param.name}: {param.example}")
                elif param.default is not None:
                    example_lines.append(f"{param.name}: {param.default}")
                else:
                    example_lines.append(f"{param.name}: <待填写>")
            example_lines.append("```")

            skill.description += "\n".join(example_lines)
            result.changes_made.append("添加使用示例")

    def _add_faqs(self, skill: GeneratedSkill, result: RefineResult):
        """添加常见问题"""
        if not skill.faqs:
            skill.faqs = [
                {
                    "question": "操作超时怎么办？",
                    "cause": "网络延迟或页面加载慢",
                    "solution": "检查网络连接，等待几秒后重试",
                },
                {
                    "question": "找不到元素怎么办？",
                    "cause": "页面结构变更或元素未加载",
                    "solution": "刷新页面，确认元素是否存在",
                },
            ]
            result.changes_made.append("添加常见问题")

    def validate(self, skill: GeneratedSkill) -> List[str]:
        """验证 Skill 质量"""
        issues = []

        # 检查必填字段
        if not skill.name:
            issues.append("缺少 Skill 名称")
        if not skill.description:
            issues.append("缺少 Skill 描述")
        if not skill.steps:
            issues.append("缺少执行步骤")

        # 检查参数
        for param in skill.parameters:
            if not param.description:
                issues.append(f"参数 '{param.name}' 缺少描述")
            if param.required and param.default is None and not param.example:
                issues.append(f"必填参数 '{param.name}' 缺少示例值")

        # 检查步骤
        for step in skill.steps:
            if not step.title:
                issues.append(f"步骤 {step.step_number} 缺少标题")
            if not step.actions:
                issues.append(f"步骤 {step.step_number} 缺少操作")

        return issues

    def suggest_improvements(self, skill: GeneratedSkill) -> List[str]:
        """建议改进"""
        suggestions = []

        # 参数建议
        if len(skill.parameters) > 5:
            suggestions.append("参数较多，考虑分组或简化")

        # 步骤建议
        if len(skill.steps) > 10:
            suggestions.append("步骤较多，考虑拆分为多个 Skill")

        # 描述建议
        if len(skill.description) < 50:
            suggestions.append("描述过短，建议添加更多使用场景说明")

        # 工具建议
        if not skill.allowed_tools:
            suggestions.append("未指定允许的工具，建议明确工具列表")

        return suggestions


# 全局优化器实例
_refiner: Optional[SkillRefiner] = None


def get_refiner() -> SkillRefiner:
    """获取优化器实例"""
    global _refiner
    if _refiner is None:
        _refiner = SkillRefiner()
    return _refiner
