"""
Google Gemini Provider

支持 Gemini 系列模型
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


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider"""

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.0-flash"

    @property
    def supported_models(self) -> list[str]:
        return [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ]

    def _init_client(self):
        """初始化 Gemini 客户端"""
        if self._client is not None:
            return

        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("请安装 google-generativeai: pip install google-generativeai")

        api_key = self.api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("需要设置 GOOGLE_API_KEY 或 GEMINI_API_KEY")

        genai.configure(api_key=api_key)
        self._client = genai
        self._model_client = genai.GenerativeModel(self.model)

    def convert_tools(self, tools: list[ToolDefinition]) -> list:
        """转换为 Gemini 工具格式"""
        try:
            from google.generativeai.types import FunctionDeclaration, Tool
        except ImportError:
            return []

        function_declarations = []
        for tool in tools:
            # Gemini 使用 FunctionDeclaration
            fd = FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters
            )
            function_declarations.append(fd)

        return [Tool(function_declarations=function_declarations)]

    def convert_messages(self, messages: list[Message]) -> tuple[Optional[str], list[dict]]:
        """
        转换消息格式

        Gemini 使用不同的消息结构
        Returns: (system_instruction, contents)
        """
        system_instruction = None
        contents = []

        for msg in messages:
            role = msg.role.value if isinstance(msg.role, MessageRole) else msg.role

            if role == "system":
                system_instruction = msg.content
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})
            elif role == "tool":
                # Gemini 工具响应格式
                contents.append({
                    "role": "function",
                    "parts": [{
                        "function_response": {
                            "name": msg.name,
                            "response": {"result": msg.content}
                        }
                    }]
                })

        return system_instruction, contents

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

        system_instruction, contents = self.convert_messages(messages)

        # 创建模型实例（可能带 system instruction）
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        model_kwargs = {"generation_config": generation_config}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction

        if tools:
            model_kwargs["tools"] = self.convert_tools(tools)

        model = self._client.GenerativeModel(self.model, **model_kwargs)

        # 发起请求
        response = model.generate_content(contents)

        # 解析响应
        content = ""
        tool_calls = []

        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "text"):
                    content = part.text
                elif hasattr(part, "function_call"):
                    fc = part.function_call
                    tool_calls.append(ToolCall(
                        id=f"gemini_{fc.name}_{id(fc)}",
                        name=fc.name,
                        arguments=dict(fc.args)
                    ))

        # 确定停止原因
        stop_reason = "end_turn"
        if tool_calls:
            stop_reason = "tool_use"
        elif response.candidates and response.candidates[0].finish_reason:
            finish_reason = response.candidates[0].finish_reason
            if str(finish_reason) == "MAX_TOKENS":
                stop_reason = "max_tokens"

        # 获取 usage
        usage = {}
        if hasattr(response, "usage_metadata"):
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=self.model,
            usage=usage,
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

        system_instruction, contents = self.convert_messages(messages)

        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        model_kwargs = {"generation_config": generation_config}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction

        if tools:
            model_kwargs["tools"] = self.convert_tools(tools)

        model = self._client.GenerativeModel(self.model, **model_kwargs)

        full_content = ""
        tool_calls = []

        response = model.generate_content(contents, stream=True)

        for chunk in response:
            if chunk.text:
                full_content += chunk.text
                yield chunk.text

        # 处理工具调用（Gemini 流式中工具调用可能在最后）
        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "function_call"):
                    fc = part.function_call
                    tool_calls.append(ToolCall(
                        id=f"gemini_{fc.name}_{id(fc)}",
                        name=fc.name,
                        arguments=dict(fc.args)
                    ))

        stop_reason = "end_turn"
        if tool_calls:
            stop_reason = "tool_use"

        return LLMResponse(
            content=full_content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=self.model,
            usage={},
            raw_response=response
        )

    def add_tool_result(
        self,
        messages: list[Message],
        tool_call: ToolCall,
        result: str
    ) -> list[Message]:
        """添加工具调用结果"""
        messages.append(Message(
            role=MessageRole.TOOL,
            content=result,
            tool_call_id=tool_call.id,
            name=tool_call.name
        ))
        return messages
