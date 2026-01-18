"""
LLM Provider 基类

定义统一的 LLM 接口，支持多模型切换
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Generator, Any
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """统一消息格式"""
    role: MessageRole
    content: str
    name: Optional[str] = None  # 用于 tool 消息
    tool_call_id: Optional[str] = None  # 用于 tool result


@dataclass
class ToolDefinition:
    """统一工具定义格式"""
    name: str
    description: str
    parameters: dict  # JSON Schema 格式

    def to_claude_format(self) -> dict:
        """转换为 Claude API 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }

    def to_openai_format(self) -> dict:
        """转换为 OpenAI API 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def to_gemini_format(self) -> dict:
        """转换为 Gemini API 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


@dataclass
class ToolCall:
    """统一工具调用格式"""
    id: str
    name: str
    arguments: dict

    @classmethod
    def from_claude_format(cls, block: Any) -> "ToolCall":
        """从 Claude 响应解析"""
        return cls(
            id=block.id,
            name=block.name,
            arguments=block.input if hasattr(block, 'input') else {}
        )

    @classmethod
    def from_openai_format(cls, tool_call: Any) -> "ToolCall":
        """从 OpenAI 响应解析"""
        import json
        return cls(
            id=tool_call.id,
            name=tool_call.function.name,
            arguments=json.loads(tool_call.function.arguments)
        )


@dataclass
class LLMResponse:
    """统一 LLM 响应格式"""
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"  # end_turn, tool_use, max_tokens, error
    model: str = ""
    usage: dict = field(default_factory=dict)
    raw_response: Any = None  # 原始响应，用于调试

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseLLMProvider(ABC):
    """
    LLM Provider 抽象基类

    所有具体的 Provider 实现都需要继承此类并实现抽象方法
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        self.api_key = api_key
        self.model = model or self.default_model
        self.base_url = base_url
        self.config = kwargs
        self._client = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 名称"""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """默认模型"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """支持的模型列表"""
        pass

    @abstractmethod
    def _init_client(self):
        """初始化 API 客户端"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        同步聊天接口

        Args:
            messages: 消息列表
            tools: 可用工具列表
            max_tokens: 最大生成 token 数
            temperature: 温度参数

        Returns:
            LLMResponse: 统一响应格式
        """
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, LLMResponse]:
        """
        流式聊天接口

        Args:
            messages: 消息列表
            tools: 可用工具列表
            max_tokens: 最大生成 token 数
            temperature: 温度参数

        Yields:
            str: 流式文本片段

        Returns:
            LLMResponse: 最终完整响应
        """
        pass

    def convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        """
        将统一工具定义转换为 Provider 特定格式

        子类可以覆盖此方法
        """
        return [t.to_claude_format() for t in tools]

    def convert_messages(self, messages: list[Message]) -> list[dict]:
        """
        将统一消息格式转换为 Provider 特定格式

        子类可以覆盖此方法
        """
        result = []
        for msg in messages:
            converted = {
                "role": msg.role.value if isinstance(msg.role, MessageRole) else msg.role,
                "content": msg.content
            }
            if msg.name:
                converted["name"] = msg.name
            if msg.tool_call_id:
                converted["tool_call_id"] = msg.tool_call_id
            result.append(converted)
        return result

    def is_available(self) -> bool:
        """检查 Provider 是否可用"""
        try:
            self._init_client()
            return self._client is not None
        except Exception:
            return False

    def get_model_info(self) -> dict:
        """获取当前模型信息"""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "supported_models": self.supported_models,
            "available": self.is_available()
        }
