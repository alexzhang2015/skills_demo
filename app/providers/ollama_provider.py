"""
Ollama Provider

支持本地部署的开源模型
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


class OllamaProvider(BaseLLMProvider):
    """Ollama 本地模型 Provider"""

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return "llama3.3"

    @property
    def supported_models(self) -> list[str]:
        # Ollama 支持的模型取决于本地安装
        return [
            "llama3.3",
            "llama3.2",
            "llama3.1",
            "qwen2.5",
            "qwen2.5-coder",
            "deepseek-r1",
            "deepseek-coder-v2",
            "mistral",
            "mixtral",
            "codellama",
            "phi3",
            "gemma2",
        ]

    def _init_client(self):
        """初始化 Ollama 客户端"""
        if self._client is not None:
            return

        try:
            import ollama
        except ImportError:
            raise ImportError("请安装 ollama: pip install ollama")

        # Ollama 默认连接本地服务
        base_url = self.base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

        self._client = ollama.Client(host=base_url)

    def convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        """转换为 Ollama 工具格式（兼容 OpenAI 格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in tools
        ]

    def convert_messages(self, messages: list[Message]) -> list[dict]:
        """转换消息格式"""
        converted = []

        for msg in messages:
            role = msg.role.value if isinstance(msg.role, MessageRole) else msg.role

            if role == "tool":
                # Ollama 工具响应格式
                converted.append({
                    "role": "tool",
                    "content": msg.content,
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
            "messages": converted_messages,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }

        if tools:
            request_params["tools"] = self.convert_tools(tools)

        response = self._client.chat(**request_params)

        # 解析响应
        content = response.get("message", {}).get("content", "")
        tool_calls = []

        # Ollama 工具调用
        message_tool_calls = response.get("message", {}).get("tool_calls", [])
        for i, tc in enumerate(message_tool_calls):
            func = tc.get("function", {})
            tool_calls.append(ToolCall(
                id=f"ollama_{func.get('name', '')}_{i}",
                name=func.get("name", ""),
                arguments=func.get("arguments", {})
            ))

        # 确定停止原因
        stop_reason = "end_turn"
        if tool_calls:
            stop_reason = "tool_use"
        elif response.get("done_reason") == "length":
            stop_reason = "max_tokens"

        # 获取 usage
        usage = {}
        if "prompt_eval_count" in response:
            usage["input_tokens"] = response.get("prompt_eval_count", 0)
        if "eval_count" in response:
            usage["output_tokens"] = response.get("eval_count", 0)

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

        converted_messages = self.convert_messages(messages)

        request_params = {
            "model": self.model,
            "messages": converted_messages,
            "stream": True,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }

        if tools:
            request_params["tools"] = self.convert_tools(tools)

        full_content = ""
        tool_calls = []
        final_response = None

        stream = self._client.chat(**request_params)

        for chunk in stream:
            if chunk.get("message", {}).get("content"):
                text = chunk["message"]["content"]
                full_content += text
                yield text

            # 收集工具调用
            message_tool_calls = chunk.get("message", {}).get("tool_calls", [])
            for i, tc in enumerate(message_tool_calls):
                func = tc.get("function", {})
                tool_calls.append(ToolCall(
                    id=f"ollama_{func.get('name', '')}_{i}",
                    name=func.get("name", ""),
                    arguments=func.get("arguments", {})
                ))

            if chunk.get("done"):
                final_response = chunk

        stop_reason = "end_turn"
        if tool_calls:
            stop_reason = "tool_use"

        usage = {}
        if final_response:
            if "prompt_eval_count" in final_response:
                usage["input_tokens"] = final_response.get("prompt_eval_count", 0)
            if "eval_count" in final_response:
                usage["output_tokens"] = final_response.get("eval_count", 0)

        return LLMResponse(
            content=full_content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=self.model,
            usage=usage,
            raw_response=final_response
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

    def list_local_models(self) -> list[str]:
        """列出本地已安装的模型"""
        self._init_client()
        try:
            response = self._client.list()
            return [m.get("name", "") for m in response.get("models", [])]
        except Exception:
            return []

    def pull_model(self, model_name: str) -> bool:
        """拉取模型"""
        self._init_client()
        try:
            self._client.pull(model_name)
            return True
        except Exception:
            return False
