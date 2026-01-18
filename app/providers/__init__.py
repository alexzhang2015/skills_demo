"""
LLM Provider 抽象层

支持多种大模型接入：
- Claude (Anthropic)
- OpenAI (GPT-4, GPT-3.5)
- Google Gemini
- Ollama (本地模型)
"""

from .base import BaseLLMProvider, LLMResponse, ToolCall, ToolDefinition, Message
from .factory import ProviderFactory, get_provider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "ToolCall",
    "ToolDefinition",
    "Message",
    "ProviderFactory",
    "get_provider",
    "ClaudeProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "OllamaProvider",
]
