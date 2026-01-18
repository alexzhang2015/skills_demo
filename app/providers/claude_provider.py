"""
Claude (Anthropic) Provider

支持 Claude 系列模型
"""

import os
from typing import Optional, Generator, Any

from .base import (
    BaseLLMProvider,
    LLMResponse,
    ToolCall,
    ToolDefinition,
    Message,
    MessageRole,
)


class ClaudeProvider(BaseLLMProvider):
    """Claude API Provider"""

    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"

    @property
    def supported_models(self) -> list[str]:
        return [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def _init_client(self):
        """初始化 Anthropic 客户端"""
        if self._client is not None:
            return

        try:
            import anthropic
        except ImportError:
            raise ImportError("请安装 anthropic: pip install anthropic")

        api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("需要设置 ANTHROPIC_API_KEY")

        self._client = anthropic.Anthropic(api_key=api_key)

    def convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        """转换为 Claude 工具格式"""
        return [tool.to_claude_format() for tool in tools]

    def convert_messages(self, messages: list[Message]) -> tuple[str, list[dict]]:
        """
        转换消息格式

        Claude API 需要单独的 system 参数
        Returns: (system_prompt, messages)
        """
        system_prompt = ""
        converted_messages = []

        for msg in messages:
            role = msg.role.value if isinstance(msg.role, MessageRole) else msg.role

            if role == "system":
                system_prompt = msg.content
            elif role == "tool":
                # Claude 使用 tool_result 格式
                converted_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content
                    }]
                })
            else:
                converted_messages.append({
                    "role": role,
                    "content": msg.content
                })

        return system_prompt, converted_messages

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """同步聊天"""
        self._init_client()

        system_prompt, converted_messages = self.convert_messages(messages)

        # 构建请求参数
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": converted_messages,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        if tools:
            request_params["tools"] = self.convert_tools(tools)

        # 调用 API
        response = self._client.messages.create(**request_params)

        # 解析响应
        content = ""
        tool_calls = []

        for block in response.content:
            if hasattr(block, "text"):
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall.from_claude_format(block))

        # 确定停止原因
        stop_reason = "end_turn"
        if response.stop_reason == "tool_use":
            stop_reason = "tool_use"
        elif response.stop_reason == "max_tokens":
            stop_reason = "max_tokens"

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw_response=response
        )

    def stream_chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, LLMResponse]:
        """流式聊天"""
        self._init_client()

        system_prompt, converted_messages = self.convert_messages(messages)

        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": converted_messages,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        if tools:
            request_params["tools"] = self.convert_tools(tools)

        # 流式调用
        full_content = ""
        tool_calls = []
        final_response = None

        with self._client.messages.stream(**request_params) as stream:
            for text in stream.text_stream:
                full_content += text
                yield text

            final_response = stream.get_final_message()

        # 解析工具调用
        if final_response:
            for block in final_response.content:
                if block.type == "tool_use":
                    tool_calls.append(ToolCall.from_claude_format(block))

        stop_reason = "end_turn"
        if final_response and final_response.stop_reason == "tool_use":
            stop_reason = "tool_use"

        return LLMResponse(
            content=full_content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=self.model,
            usage={
                "input_tokens": final_response.usage.input_tokens if final_response else 0,
                "output_tokens": final_response.usage.output_tokens if final_response else 0,
            },
            raw_response=final_response
        )

    def add_tool_result(
        self,
        messages: list[Message],
        tool_call: ToolCall,
        result: str
    ) -> list[Message]:
        """添加工具调用结果到消息列表"""
        messages.append(Message(
            role=MessageRole.TOOL,
            content=result,
            tool_call_id=tool_call.id
        ))
        return messages
