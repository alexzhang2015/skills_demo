"""
知识库管理

管理 Skill 文件存储、版本控制、搜索
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

from .generator import GeneratedSkill


@dataclass
class SkillEntry:
    """知识库中的 Skill 条目"""
    skill_id: str
    name: str
    description: str
    version: str
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # 路径
    file_path: str = ""
    directory: str = ""

    # 内容
    content: Optional[str] = None

    # 统计
    execution_count: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0

    # 来源
    source: str = "manual"  # manual, recorded, generated
    source_recording_id: Optional[str] = None

    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "tags": self.tags,
            "file_path": self.file_path,
            "execution_count": self.execution_count,
            "success_rate": self.success_rate,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SearchResult:
    """搜索结果"""
    entry: SkillEntry
    score: float
    matched_fields: List[str]


class KnowledgeRepository:
    """
    知识库管理器

    功能：
    - Skill 文件存储和版本管理
    - 元数据索引
    - 全文搜索
    - 统计信息
    """

    def __init__(
        self,
        base_dir: str = None,
        index_file: str = "index.json"
    ):
        self.base_dir = Path(base_dir) if base_dir else Path(".claude/skills")
        self.index_file = self.base_dir / index_file

        # 内存索引
        self._entries: Dict[str, SkillEntry] = {}

        # 确保目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 加载索引
        self._load_index()

    def _load_index(self):
        """加载索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get("entries", []):
                        entry = SkillEntry(
                            skill_id=item["skill_id"],
                            name=item["name"],
                            description=item.get("description", ""),
                            version=item.get("version", "1.0"),
                            category=item.get("category"),
                            tags=item.get("tags", []),
                            file_path=item.get("file_path", ""),
                            directory=item.get("directory", ""),
                            execution_count=item.get("execution_count", 0),
                            success_rate=item.get("success_rate", 0.0),
                            avg_duration_ms=item.get("avg_duration_ms", 0.0),
                            source=item.get("source", "manual"),
                        )
                        self._entries[entry.skill_id] = entry
            except Exception as e:
                print(f"Warning: Failed to load index: {e}")

        # 扫描文件系统补充索引
        self._scan_filesystem()

    def _scan_filesystem(self):
        """扫描文件系统"""
        for skill_dir in self.base_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    skill_id = skill_dir.name
                    if skill_id not in self._entries:
                        # 解析 SKILL.md 添加到索引
                        try:
                            entry = self._parse_skill_file(skill_md)
                            if entry:
                                self._entries[entry.skill_id] = entry
                        except Exception:
                            pass

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillEntry]:
        """解析 SKILL.md 文件"""
        content = file_path.read_text(encoding='utf-8')

        # 简单解析 frontmatter
        name = ""
        description = ""
        tags = []
        category = None

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]

                # 提取 name
                name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip()

                # 提取 description
                desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
                if desc_match:
                    description = desc_match.group(1).strip()

                # 提取 category
                cat_match = re.search(r"^category:\s*(.+)$", frontmatter, re.MULTILINE)
                if cat_match:
                    category = cat_match.group(1).strip()

                # 提取 tags
                tags_match = re.search(r"^tags:\s*\[(.+)\]$", frontmatter, re.MULTILINE)
                if tags_match:
                    tags = [t.strip() for t in tags_match.group(1).split(",")]

        skill_id = file_path.parent.name

        return SkillEntry(
            skill_id=skill_id,
            name=name or skill_id,
            description=description,
            version="1.0",
            category=category,
            tags=tags,
            file_path=str(file_path),
            directory=str(file_path.parent),
            content=content,
            source="file",
        )

    def _save_index(self):
        """保存索引"""
        data = {
            "updated_at": datetime.utcnow().isoformat(),
            "entries": [e.to_dict() for e in self._entries.values()]
        }
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_skill(
        self,
        skill: GeneratedSkill,
        overwrite: bool = False
    ) -> SkillEntry:
        """
        保存 Skill 到知识库

        Args:
            skill: 要保存的 Skill
            overwrite: 是否覆盖已存在的

        Returns:
            SkillEntry
        """
        skill_id = skill.name
        skill_dir = self.base_dir / skill_id

        # 检查是否存在
        if skill_dir.exists() and not overwrite:
            raise ValueError(f"Skill '{skill_id}' already exists")

        # 创建目录
        skill_dir.mkdir(parents=True, exist_ok=True)

        # 生成内容
        content = skill.to_skill_md()

        # 保存 SKILL.md
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content, encoding='utf-8')

        # 创建索引条目
        entry = SkillEntry(
            skill_id=skill_id,
            name=skill.name,
            description=skill.description,
            version=skill.version,
            category=skill.category,
            tags=skill.tags,
            file_path=str(skill_file),
            directory=str(skill_dir),
            content=content,
            source="generated",
            source_recording_id=skill.source_recording_id,
        )

        self._entries[skill_id] = entry
        self._save_index()

        return entry

    def get_skill(self, skill_id: str) -> Optional[SkillEntry]:
        """获取 Skill"""
        entry = self._entries.get(skill_id)
        if entry and not entry.content:
            # 懒加载内容
            if entry.file_path and os.path.exists(entry.file_path):
                entry.content = Path(entry.file_path).read_text(encoding='utf-8')
        return entry

    def list_skills(
        self,
        category: str = None,
        tags: List[str] = None,
        source: str = None
    ) -> List[SkillEntry]:
        """列出 Skills"""
        entries = list(self._entries.values())

        if category:
            entries = [e for e in entries if e.category == category]

        if tags:
            entries = [e for e in entries if any(t in e.tags for t in tags)]

        if source:
            entries = [e for e in entries if e.source == source]

        return sorted(entries, key=lambda e: e.name)

    def search(
        self,
        query: str,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        搜索 Skills

        简单的文本匹配搜索，后续可以扩展为向量搜索
        """
        query_lower = query.lower()
        results = []

        for entry in self._entries.values():
            score = 0.0
            matched_fields = []

            # 名称匹配
            if query_lower in entry.name.lower():
                score += 10.0
                matched_fields.append("name")

            # 描述匹配
            if query_lower in entry.description.lower():
                score += 5.0
                matched_fields.append("description")

            # 标签匹配
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 3.0
                    matched_fields.append(f"tag:{tag}")

            # 分类匹配
            if entry.category and query_lower in entry.category.lower():
                score += 2.0
                matched_fields.append("category")

            if score > 0:
                results.append(SearchResult(
                    entry=entry,
                    score=score,
                    matched_fields=matched_fields
                ))

        # 按分数排序
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def delete_skill(self, skill_id: str) -> bool:
        """删除 Skill"""
        entry = self._entries.get(skill_id)
        if not entry:
            return False

        # 删除文件
        if entry.directory and os.path.exists(entry.directory):
            import shutil
            shutil.rmtree(entry.directory)

        # 从索引移除
        del self._entries[skill_id]
        self._save_index()

        return True

    def update_stats(
        self,
        skill_id: str,
        success: bool,
        duration_ms: float
    ):
        """更新执行统计"""
        entry = self._entries.get(skill_id)
        if entry:
            entry.execution_count += 1

            # 更新成功率（滑动平均）
            if entry.execution_count == 1:
                entry.success_rate = 1.0 if success else 0.0
            else:
                alpha = 0.1
                entry.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * entry.success_rate

            # 更新平均耗时
            if entry.avg_duration_ms == 0:
                entry.avg_duration_ms = duration_ms
            else:
                entry.avg_duration_ms = 0.9 * entry.avg_duration_ms + 0.1 * duration_ms

            entry.updated_at = datetime.utcnow()
            self._save_index()

    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计"""
        entries = list(self._entries.values())

        return {
            "total_skills": len(entries),
            "by_category": self._group_count(entries, lambda e: e.category or "未分类"),
            "by_source": self._group_count(entries, lambda e: e.source),
            "total_executions": sum(e.execution_count for e in entries),
            "avg_success_rate": (
                sum(e.success_rate for e in entries if e.execution_count > 0) /
                len([e for e in entries if e.execution_count > 0])
                if any(e.execution_count > 0 for e in entries) else 0
            ),
        }

    def _group_count(self, entries: List[SkillEntry], key_func) -> Dict[str, int]:
        """分组计数"""
        counts = {}
        for entry in entries:
            key = key_func(entry)
            counts[key] = counts.get(key, 0) + 1
        return counts


# 需要导入 re
import re


# 全局知识库实例
_repository: Optional[KnowledgeRepository] = None


def get_repository(base_dir: str = None) -> KnowledgeRepository:
    """获取知识库实例"""
    global _repository
    if _repository is None:
        _repository = KnowledgeRepository(base_dir)
    return _repository
