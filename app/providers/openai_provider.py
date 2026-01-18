"""
OpenAI Provider

支持 GPT-4, GPT-3.5 等模型
"""

import os
import json
from typing import Optional, Generator, Any

from .base import (
    BaseLLMProvider,
    LLMResponse,
    ToolCall,
    ToolDefinition,
    Message,
    MessageRole,
)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider"""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    @property
    def supported_models(self) -> list[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ]

    def _init_client(self):
        """初始化 OpenAI 客户端"""
        if self._client is not None:
            return

        try:
            import openai
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

        api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("需要设置 OPENAI_API_KEY")

        client_kwargs = {"api_key": api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self._client = openai.OpenAI(**client_kwargs)

    def convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        """转换为 OpenAI 工具格式"""
        return [tool.to_openai_format() for tool in tools]

    def convert_messages(self, messages: list[Message]) -> list[dict]:
        """转换消息格式"""
        converted = []

        for msg in messages:
            role = msg.role.value if isinstance(msg.role, MessageRole) else msg.role

            if role == "tool":
                converted.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })
            else:
                converted.append({
                    "role": role,
                    "content": msg.content
                })

        return converted

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

        converted_messages = self.convert_messages(messages)

        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": converted_messages,
        }

        if tools:
            request_params["tools"] = self.convert_tools(tools)
            request_params["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**request_params)

        # 解析响应
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(ToolCall.from_openai_format(tc))

        # 确定停止原因
        stop_reason = "end_turn"
        if choice.finish_reason == "tool_calls":
            stop_reason = "tool_use"
        elif choice.finish_reason == "length":
            stop_reason = "max_tokens"

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
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

        converted_messages = self.convert_messages(messages)

        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": converted_messages,
            "stream": True,
        }

        if tools:
            request_params["tools"] = self.convert_tools(tools)
            request_params["tool_choice"] = "auto"

        full_content = ""
        tool_calls_data = {}  # 收集工具调用数据
        finish_reason = None

        stream = self._client.chat.completions.create(**request_params)

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # 收集文本内容
            if delta.content:
                full_content += delta.content
                yield delta.content

            # 收集工具调用（流式中分片传输）
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_data:
                        tool_calls_data[idx] = {
                            "id": tc.id or "",
                            "name": "",
                            "arguments": ""
                        }
                    if tc.id:
                        tool_calls_data[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_data[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_data[idx]["arguments"] += tc.function.arguments

            if chunk.choices[0].finish_reason:
                finish_reason = chunk.choices[0].finish_reason

        # 构建工具调用列表
        tool_calls = []
        for idx in sorted(tool_calls_data.keys()):
            tc_data = tool_calls_data[idx]
            try:
                arguments = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
            except json.JSONDecodeError:
                arguments = {}

            tool_calls.append(ToolCall(
                id=tc_data["id"],
                name=tc_data["name"],
                arguments=arguments
            ))

        stop_reason = "end_turn"
        if finish_reason == "tool_calls":
            stop_reason = "tool_use"
        elif finish_reason == "length":
            stop_reason = "max_tokens"

        return LLMResponse(
            content=full_content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=self.model,
            usage={},  # 流式模式下 OpenAI 不返回 usage
            raw_response=None
        )

    def add_tool_result(
        self,
        messages: list[Message],
        tool_call: ToolCall,
        result: str
    ) -> list[Message]:
        """添加工具调用结果"""
        # OpenAI 需要先添加 assistant 消息包含 tool_calls
        # 这里假设 assistant 消息已经在列表中
        messages.append(Message(
            role=MessageRole.TOOL,
            content=result,
            tool_call_id=tool_call.id,
            name=tool_call.name
        ))
        return messages
