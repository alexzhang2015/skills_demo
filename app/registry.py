import uuid
from datetime import datetime
from typing import Optional

from .models import Skill, SkillCreate, SkillUpdate


class SkillRegistry:
    """
    技能注册表 - 管理技能的CRUD操作
    """

    def __init__(self):
        self.skills: dict[str, Skill] = {}

    def create(self, skill_data: SkillCreate) -> Skill:
        """创建新技能"""
        skill_id = str(uuid.uuid4())[:8]
        skill = Skill(
            id=skill_id,
            name=skill_data.name,
            description=skill_data.description,
            prompt=skill_data.prompt,
            category=skill_data.category,
            requires_approval=skill_data.requires_approval,
            affected_systems=skill_data.affected_systems,
        )
        self.skills[skill_id] = skill
        return skill

    def get(self, skill_id: str) -> Optional[Skill]:
        """通过ID或名称获取技能"""
        if skill_id in self.skills:
            return self.skills[skill_id]
        for skill in self.skills.values():
            if skill.name == skill_id:
                return skill
        return None

    def get_all(self) -> list[Skill]:
        """获取所有技能"""
        return list(self.skills.values())

    def update(self, skill_id: str, update_data: SkillUpdate) -> Optional[Skill]:
        """更新技能"""
        skill = self.skills.get(skill_id)
        if not skill:
            return None

        if update_data.name is not None:
            skill.name = update_data.name
        if update_data.description is not None:
            skill.description = update_data.description
        if update_data.prompt is not None:
            skill.prompt = update_data.prompt
        if update_data.category is not None:
            skill.category = update_data.category
        if update_data.requires_approval is not None:
            skill.requires_approval = update_data.requires_approval
        if update_data.affected_systems is not None:
            skill.affected_systems = update_data.affected_systems
        skill.updated_at = datetime.now()
        return skill

    def delete(self, skill_id: str) -> bool:
        """删除技能"""
        if skill_id in self.skills:
            del self.skills[skill_id]
            return True
        return False
