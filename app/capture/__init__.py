"""
知识沉淀系统

支持从操作录制到 Skill 生成的完整流程：
1. Recorder - Chrome/Playwright 操作录制
2. Generator - SKILL.md 自动生成
3. Refiner - 参数化和泛化优化
4. Repository - 知识库管理
"""

from .recorder import (
    ActionRecorder,
    RecordedAction,
    RecordingSession,
    ActionType,
    get_recorder,
)
from .generator import (
    SkillGenerator,
    GeneratedSkill,
    get_generator,
)
from .refiner import (
    SkillRefiner,
    RefineOptions,
    get_refiner,
)
from .repository import (
    KnowledgeRepository,
    get_repository,
)

__all__ = [
    "ActionRecorder",
    "RecordedAction",
    "RecordingSession",
    "ActionType",
    "get_recorder",
    "SkillGenerator",
    "GeneratedSkill",
    "get_generator",
    "SkillRefiner",
    "RefineOptions",
    "get_refiner",
    "KnowledgeRepository",
    "get_repository",
]
