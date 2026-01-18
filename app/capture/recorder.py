"""
操作录制器

录制 Chrome/Playwright 浏览器操作，生成操作序列
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum


class ActionType(str, Enum):
    """操作类型"""
    # 导航
    NAVIGATE = "navigate"
    RELOAD = "reload"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"

    # 鼠标操作
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    HOVER = "hover"
    DRAG = "drag"

    # 键盘操作
    TYPE = "type"
    PRESS_KEY = "press_key"
    FILL = "fill"
    CLEAR = "clear"

    # 选择操作
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"

    # 等待操作
    WAIT_FOR_ELEMENT = "wait_for_element"
    WAIT_FOR_TEXT = "wait_for_text"
    WAIT_FOR_URL = "wait_for_url"
    WAIT_TIME = "wait_time"

    # 断言
    ASSERT_TEXT = "assert_text"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_VALUE = "assert_value"

    # 其他
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    UPLOAD_FILE = "upload_file"


@dataclass
class ElementSelector:
    """元素选择器"""
    # 主选择器
    selector: str
    selector_type: str = "css"  # css, xpath, text, role, test_id

    # 备选选择器（用于容错）
    fallback_selectors: List[str] = field(default_factory=list)

    # 元素信息（用于生成描述）
    tag_name: Optional[str] = None
    text_content: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)

    # 位置信息
    bounding_box: Optional[Dict[str, float]] = None

    def to_playwright_selector(self) -> str:
        """转换为 Playwright 选择器"""
        if self.selector_type == "css":
            return self.selector
        elif self.selector_type == "xpath":
            return f"xpath={self.selector}"
        elif self.selector_type == "text":
            return f"text={self.selector}"
        elif self.selector_type == "role":
            return f"role={self.selector}"
        elif self.selector_type == "test_id":
            return f"[data-testid='{self.selector}']"
        return self.selector

    def get_description(self) -> str:
        """获取元素描述"""
        parts = []

        if self.tag_name:
            parts.append(self.tag_name)

        if self.text_content:
            text = self.text_content[:30]
            if len(self.text_content) > 30:
                text += "..."
            parts.append(f"'{text}'")

        if self.attributes.get("id"):
            parts.append(f"#{self.attributes['id']}")

        if self.attributes.get("class"):
            classes = self.attributes["class"].split()[:2]
            parts.append(".".join(classes))

        return " ".join(parts) if parts else self.selector


@dataclass
class RecordedAction:
    """录制的操作"""
    action_id: str
    action_type: ActionType
    timestamp: datetime

    # 操作目标
    selector: Optional[ElementSelector] = None
    url: Optional[str] = None

    # 操作参数
    value: Optional[str] = None  # 输入值
    key: Optional[str] = None    # 按键
    options: Dict[str, Any] = field(default_factory=dict)

    # 页面信息
    page_url: Optional[str] = None
    page_title: Optional[str] = None

    # 截图
    screenshot_path: Optional[str] = None

    # 结果
    success: bool = True
    error: Optional[str] = None

    # 生成的代码（用于预览）
    generated_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "timestamp": self.timestamp.isoformat(),
            "selector": {
                "selector": self.selector.selector,
                "selector_type": self.selector.selector_type,
                "description": self.selector.get_description(),
            } if self.selector else None,
            "url": self.url,
            "value": self.value,
            "key": self.key,
            "options": self.options,
            "page_url": self.page_url,
            "page_title": self.page_title,
            "success": self.success,
            "error": self.error,
        }

    def get_description(self) -> str:
        """获取操作描述"""
        if self.action_type == ActionType.NAVIGATE:
            return f"导航到 {self.url}"
        elif self.action_type == ActionType.CLICK:
            target = self.selector.get_description() if self.selector else "元素"
            return f"点击 {target}"
        elif self.action_type == ActionType.TYPE:
            target = self.selector.get_description() if self.selector else "输入框"
            return f"在 {target} 输入 '{self.value}'"
        elif self.action_type == ActionType.FILL:
            target = self.selector.get_description() if self.selector else "输入框"
            return f"填写 {target} 为 '{self.value}'"
        elif self.action_type == ActionType.SELECT:
            target = self.selector.get_description() if self.selector else "下拉框"
            return f"在 {target} 选择 '{self.value}'"
        elif self.action_type == ActionType.PRESS_KEY:
            return f"按下 {self.key} 键"
        elif self.action_type == ActionType.WAIT_FOR_ELEMENT:
            target = self.selector.get_description() if self.selector else "元素"
            return f"等待 {target} 出现"
        elif self.action_type == ActionType.WAIT_FOR_TEXT:
            return f"等待文本 '{self.value}' 出现"
        elif self.action_type == ActionType.ASSERT_TEXT:
            return f"验证文本 '{self.value}' 存在"
        else:
            return f"{self.action_type.value}"


@dataclass
class RecordingSession:
    """录制会话"""
    session_id: str
    name: Optional[str] = None
    description: Optional[str] = None

    # 操作列表
    actions: List[RecordedAction] = field(default_factory=list)

    # 起始信息
    start_url: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)

    # 结束信息
    end_time: Optional[datetime] = None
    status: str = "recording"  # recording, completed, failed

    # 页面信息
    pages_visited: List[str] = field(default_factory=list)

    # 录制者
    recorded_by: Optional[str] = None

    # 元数据
    browser_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000

    @property
    def action_count(self) -> int:
        return len(self.actions)

    def add_action(self, action: RecordedAction):
        """添加操作"""
        self.actions.append(action)

        # 更新页面列表
        if action.page_url and action.page_url not in self.pages_visited:
            self.pages_visited.append(action.page_url)

    def complete(self):
        """完成录制"""
        self.end_time = datetime.utcnow()
        self.status = "completed"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "description": self.description,
            "actions": [a.to_dict() for a in self.actions],
            "start_url": self.start_url,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "action_count": self.action_count,
            "pages_visited": self.pages_visited,
            "recorded_by": self.recorded_by,
            "browser_info": self.browser_info,
            "metadata": self.metadata,
        }


class ActionRecorder:
    """
    操作录制器

    功能：
    - 创建和管理录制会话
    - 记录浏览器操作
    - 生成选择器
    - 导出录制数据
    """

    def __init__(self):
        self._sessions: Dict[str, RecordingSession] = {}
        self._current_session: Optional[RecordingSession] = None

    def start_session(
        self,
        name: str = None,
        start_url: str = None,
        recorded_by: str = None,
        **metadata
    ) -> RecordingSession:
        """开始录制会话"""
        session = RecordingSession(
            session_id=str(uuid.uuid4())[:12],
            name=name or f"Recording {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_url=start_url,
            recorded_by=recorded_by,
            metadata=metadata,
        )

        self._sessions[session.session_id] = session
        self._current_session = session

        return session

    def end_session(self, session_id: str = None) -> Optional[RecordingSession]:
        """结束录制会话"""
        session = self._get_session(session_id)
        if session:
            session.complete()
            if self._current_session and self._current_session.session_id == session.session_id:
                self._current_session = None
        return session

    def record_action(
        self,
        action_type: ActionType,
        selector: ElementSelector = None,
        url: str = None,
        value: str = None,
        key: str = None,
        page_url: str = None,
        page_title: str = None,
        session_id: str = None,
        **options
    ) -> RecordedAction:
        """记录操作"""
        session = self._get_session(session_id)
        if not session:
            raise ValueError("No active recording session")

        action = RecordedAction(
            action_id=str(uuid.uuid4())[:8],
            action_type=action_type,
            timestamp=datetime.utcnow(),
            selector=selector,
            url=url,
            value=value,
            key=key,
            page_url=page_url,
            page_title=page_title,
            options=options,
        )

        # 生成代码预览
        action.generated_code = self._generate_code(action)

        session.add_action(action)
        return action

    def _get_session(self, session_id: str = None) -> Optional[RecordingSession]:
        """获取会话"""
        if session_id:
            return self._sessions.get(session_id)
        return self._current_session

    def get_session(self, session_id: str) -> Optional[RecordingSession]:
        """获取会话"""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[RecordingSession]:
        """列出所有会话"""
        return list(self._sessions.values())

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _generate_code(self, action: RecordedAction) -> str:
        """为操作生成 Playwright 代码"""
        if action.action_type == ActionType.NAVIGATE:
            return f'await page.goto("{action.url}")'

        if action.action_type == ActionType.CLICK:
            selector = action.selector.to_playwright_selector() if action.selector else ""
            return f'await page.click("{selector}")'

        if action.action_type == ActionType.FILL:
            selector = action.selector.to_playwright_selector() if action.selector else ""
            return f'await page.fill("{selector}", "{action.value}")'

        if action.action_type == ActionType.TYPE:
            selector = action.selector.to_playwright_selector() if action.selector else ""
            return f'await page.type("{selector}", "{action.value}")'

        if action.action_type == ActionType.SELECT:
            selector = action.selector.to_playwright_selector() if action.selector else ""
            return f'await page.selectOption("{selector}", "{action.value}")'

        if action.action_type == ActionType.PRESS_KEY:
            return f'await page.keyboard.press("{action.key}")'

        if action.action_type == ActionType.WAIT_FOR_ELEMENT:
            selector = action.selector.to_playwright_selector() if action.selector else ""
            return f'await page.waitForSelector("{selector}")'

        if action.action_type == ActionType.WAIT_FOR_TEXT:
            return f'await page.waitForSelector("text={action.value}")'

        if action.action_type == ActionType.ASSERT_TEXT:
            return f'await expect(page.locator("text={action.value}")).toBeVisible()'

        return f"# {action.action_type.value}"

    # ==================== Playwright 集成 ====================

    def create_selector_from_element(
        self,
        element_info: Dict[str, Any]
    ) -> ElementSelector:
        """
        从元素信息创建选择器

        element_info 来自 Playwright 的 evaluate 或 DevTools
        """
        # 优先使用 test-id
        if element_info.get("testId"):
            return ElementSelector(
                selector=element_info["testId"],
                selector_type="test_id",
                tag_name=element_info.get("tagName"),
                text_content=element_info.get("textContent"),
                attributes=element_info.get("attributes", {}),
            )

        # 其次使用 id
        if element_info.get("id"):
            return ElementSelector(
                selector=f"#{element_info['id']}",
                selector_type="css",
                tag_name=element_info.get("tagName"),
                text_content=element_info.get("textContent"),
                attributes=element_info.get("attributes", {}),
            )

        # 使用 role + name
        if element_info.get("role") and element_info.get("name"):
            return ElementSelector(
                selector=f"{element_info['role']}[name='{element_info['name']}']",
                selector_type="role",
                tag_name=element_info.get("tagName"),
                text_content=element_info.get("textContent"),
                attributes=element_info.get("attributes", {}),
            )

        # 使用文本内容
        if element_info.get("textContent") and len(element_info["textContent"]) < 50:
            return ElementSelector(
                selector=element_info["textContent"],
                selector_type="text",
                tag_name=element_info.get("tagName"),
                text_content=element_info.get("textContent"),
                attributes=element_info.get("attributes", {}),
            )

        # 回退到 CSS 选择器
        css_selector = self._build_css_selector(element_info)
        return ElementSelector(
            selector=css_selector,
            selector_type="css",
            tag_name=element_info.get("tagName"),
            text_content=element_info.get("textContent"),
            attributes=element_info.get("attributes", {}),
        )

    def _build_css_selector(self, element_info: Dict[str, Any]) -> str:
        """构建 CSS 选择器"""
        tag = element_info.get("tagName", "").lower()
        attrs = element_info.get("attributes", {})

        parts = [tag] if tag else []

        # 添加类名
        if attrs.get("class"):
            classes = attrs["class"].split()[:2]
            for cls in classes:
                if cls and not cls.startswith("_"):  # 跳过动态类名
                    parts.append(f".{cls}")

        # 添加属性
        for attr in ["name", "type", "placeholder"]:
            if attrs.get(attr):
                parts.append(f'[{attr}="{attrs[attr]}"]')
                break

        return "".join(parts) if parts else "*"


# 全局录制器实例
_recorder: Optional[ActionRecorder] = None


def get_recorder() -> ActionRecorder:
    """获取录制器实例"""
    global _recorder
    if _recorder is None:
        _recorder = ActionRecorder()
    return _recorder
