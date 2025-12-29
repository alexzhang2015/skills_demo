"""
SKILL.md 格式解析器
支持 YAML frontmatter + Markdown 格式
"""
import re
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class SkillMetadata:
    """Level 1: 元数据（总是加载）"""
    name: str
    description: str
    allowed_tools: list[str] = field(default_factory=list)
    model: Optional[str] = None


@dataclass
class SkillInstructions:
    """Level 2: 指令内容（按需加载）"""
    content: str  # Markdown 内容
    sections: dict[str, str] = field(default_factory=dict)  # 分节内容


@dataclass
class SkillResources:
    """Level 3: 资源文件（动态加载）"""
    files: dict[str, str] = field(default_factory=dict)  # 文件名 -> 内容
    scripts: list[str] = field(default_factory=list)  # 脚本路径列表


@dataclass
class ParsedSkill:
    """完整解析的 Skill"""
    metadata: SkillMetadata
    instructions: Optional[SkillInstructions] = None
    resources: Optional[SkillResources] = None
    source_path: Optional[Path] = None

    @property
    def id(self) -> str:
        return self.metadata.name

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def description(self) -> str:
        return self.metadata.description


class SkillParser:
    """SKILL.md 文件解析器"""

    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL
    )

    SECTION_PATTERN = re.compile(
        r'^##\s+(.+)$',
        re.MULTILINE
    )

    def parse_file(self, skill_path: Path) -> ParsedSkill:
        """解析 SKILL.md 文件"""
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_path}")

        content = skill_md.read_text(encoding='utf-8')

        # 解析 YAML frontmatter 和 Markdown 内容
        metadata, markdown_content = self._parse_frontmatter(content)

        # 解析指令内容
        instructions = self._parse_instructions(markdown_content)

        # 扫描资源文件
        resources = self._scan_resources(skill_path)

        return ParsedSkill(
            metadata=metadata,
            instructions=instructions,
            resources=resources,
            source_path=skill_path
        )

    def parse_content(self, content: str, name: str = "unnamed") -> ParsedSkill:
        """直接解析 SKILL.md 内容字符串"""
        metadata, markdown_content = self._parse_frontmatter(content)

        # 如果没有 name，使用传入的默认值
        if not metadata.name:
            metadata.name = name

        instructions = self._parse_instructions(markdown_content)

        return ParsedSkill(
            metadata=metadata,
            instructions=instructions,
            resources=None
        )

    def _parse_frontmatter(self, content: str) -> tuple[SkillMetadata, str]:
        """解析 YAML frontmatter"""
        match = self.FRONTMATTER_PATTERN.match(content)

        if match:
            yaml_content = match.group(1)
            markdown_content = match.group(2)

            try:
                data = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML frontmatter: {e}")

            # 解析 allowed-tools
            allowed_tools = []
            if 'allowed-tools' in data:
                tools_str = data['allowed-tools']
                if isinstance(tools_str, str):
                    allowed_tools = [t.strip() for t in tools_str.split(',')]
                elif isinstance(tools_str, list):
                    allowed_tools = tools_str

            metadata = SkillMetadata(
                name=data.get('name', ''),
                description=data.get('description', ''),
                allowed_tools=allowed_tools,
                model=data.get('model')
            )
        else:
            # 没有 frontmatter，整个内容作为 markdown
            metadata = SkillMetadata(name='', description='')
            markdown_content = content

        return metadata, markdown_content

    def _parse_instructions(self, markdown: str) -> SkillInstructions:
        """解析 Markdown 指令内容"""
        sections = {}

        # 分割成各个 section
        parts = self.SECTION_PATTERN.split(markdown)

        # parts 格式: [前置内容, section1_title, section1_content, section2_title, ...]
        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    section_name = parts[i].strip().lower()
                    section_content = parts[i + 1].strip()
                    sections[section_name] = section_content

        return SkillInstructions(
            content=markdown.strip(),
            sections=sections
        )

    def _scan_resources(self, skill_path: Path) -> SkillResources:
        """扫描 Skill 目录中的资源文件"""
        resources = SkillResources()

        # 扫描 markdown 文件（排除 SKILL.md）
        for md_file in skill_path.glob("*.md"):
            if md_file.name != "SKILL.md":
                resources.files[md_file.name] = md_file.name  # 只存储文件名，按需加载内容

        # 扫描 scripts 目录
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.py"):
                resources.scripts.append(str(script.relative_to(skill_path)))

        return resources


class SkillLoader:
    """
    渐进式 Skill 加载器

    Level 1: 元数据 - 启动时加载所有 Skill 的 name 和 description
    Level 2: 指令 - Skill 被触发时加载完整 SKILL.md 内容
    Level 3: 资源 - 执行时按需加载参考文档和脚本
    """

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.parser = SkillParser()
        self._metadata_cache: dict[str, SkillMetadata] = {}
        self._skills_cache: dict[str, ParsedSkill] = {}

    def load_all_metadata(self) -> list[SkillMetadata]:
        """
        Level 1: 加载所有 Skill 的元数据
        这是最轻量的加载，只读取 YAML frontmatter
        """
        self._metadata_cache.clear()

        if not self.skills_dir.exists():
            return []

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        content = skill_md.read_text(encoding='utf-8')
                        metadata, _ = self.parser._parse_frontmatter(content)
                        if metadata.name:
                            self._metadata_cache[metadata.name] = metadata
                    except Exception as e:
                        print(f"Warning: Failed to load metadata from {skill_dir}: {e}")

        return list(self._metadata_cache.values())

    def load_skill(self, skill_name: str) -> Optional[ParsedSkill]:
        """
        Level 2: 加载完整 Skill（元数据 + 指令）
        当 Skill 被触发时调用
        """
        if skill_name in self._skills_cache:
            return self._skills_cache[skill_name]

        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            return None

        try:
            skill = self.parser.parse_file(skill_dir)
            self._skills_cache[skill_name] = skill
            return skill
        except Exception as e:
            print(f"Warning: Failed to load skill {skill_name}: {e}")
            return None

    def load_resource(self, skill_name: str, resource_name: str) -> Optional[str]:
        """
        Level 3: 加载资源文件内容
        执行时按需调用
        """
        skill_dir = self.skills_dir / skill_name
        resource_path = skill_dir / resource_name

        if resource_path.exists():
            return resource_path.read_text(encoding='utf-8')
        return None

    def get_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """获取缓存的元数据"""
        return self._metadata_cache.get(skill_name)

    def list_skills(self) -> list[str]:
        """列出所有可用的 Skill 名称"""
        return list(self._metadata_cache.keys())
