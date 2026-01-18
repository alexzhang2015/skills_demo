"""
Provider 工厂

统一管理和创建 LLM Provider 实例
"""

import os
from typing import Optional, Type

from .base import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider


# Provider 注册表
PROVIDER_REGISTRY: dict[str, Type[BaseLLMProvider]] = {
    "claude": ClaudeProvider,
    "anthropic": ClaudeProvider,  # 别名
    "openai": OpenAIProvider,
    "gpt": OpenAIProvider,  # 别名
    "gemini": GeminiProvider,
    "google": GeminiProvider,  # 别名
    "ollama": OllamaProvider,
    "local": OllamaProvider,  # 别名
}

# 默认配置
DEFAULT_PROVIDER = os.environ.get("DEFAULT_LLM_PROVIDER", "claude")
DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.3",
}


class ProviderFactory:
    """
    Provider 工厂类

    负责创建和管理 LLM Provider 实例
    支持通过环境变量配置默认 Provider
    """

    _instances: dict[str, BaseLLMProvider] = {}

    @classmethod
    def create(
        cls,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        创建 Provider 实例

        Args:
            provider_name: Provider 名称 (claude, openai, gemini, ollama)
            model: 模型名称
            api_key: API Key
            base_url: 自定义 API 地址
            **kwargs: 其他配置

        Returns:
            BaseLLMProvider 实例
        """
        # 确定 Provider
        provider_name = provider_name or DEFAULT_PROVIDER
        provider_name = provider_name.lower()

        if provider_name not in PROVIDER_REGISTRY:
            available = list(PROVIDER_REGISTRY.keys())
            raise ValueError(f"不支持的 Provider: {provider_name}，可用: {available}")

        # 获取 Provider 类
        provider_class = PROVIDER_REGISTRY[provider_name]

        # 确定模型
        if not model:
            # 从环境变量获取或使用默认值
            env_key = f"{provider_name.upper()}_MODEL"
            model = os.environ.get(env_key) or DEFAULT_MODELS.get(provider_name)

        # 创建实例
        provider = provider_class(
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs
        )

        return provider

    @classmethod
    def get_or_create(
        cls,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        获取或创建 Provider 实例（单例模式）

        对于同一 provider_name，返回缓存的实例
        """
        provider_name = provider_name or DEFAULT_PROVIDER
        provider_name = provider_name.lower()

        if provider_name not in cls._instances:
            cls._instances[provider_name] = cls.create(provider_name, **kwargs)

        return cls._instances[provider_name]

    @classmethod
    def clear_cache(cls):
        """清除缓存的实例"""
        cls._instances.clear()

    @classmethod
    def list_providers(cls) -> list[str]:
        """列出所有可用的 Provider"""
        # 去重（因为有别名）
        unique_providers = set()
        for name, provider_class in PROVIDER_REGISTRY.items():
            unique_providers.add(provider_class.provider_name.fget(None) if hasattr(provider_class.provider_name, 'fget') else name)
        return ["claude", "openai", "gemini", "ollama"]

    @classmethod
    def get_available_providers(cls) -> list[dict]:
        """获取所有可用的 Provider 及其状态"""
        result = []
        for provider_name in cls.list_providers():
            try:
                provider = cls.create(provider_name)
                available = provider.is_available()
                result.append({
                    "name": provider_name,
                    "available": available,
                    "default_model": provider.default_model,
                    "supported_models": provider.supported_models,
                })
            except Exception as e:
                result.append({
                    "name": provider_name,
                    "available": False,
                    "error": str(e),
                })
        return result

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """注册自定义 Provider"""
        PROVIDER_REGISTRY[name.lower()] = provider_class


def get_provider(
    provider_name: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """
    便捷函数：获取 Provider 实例

    Args:
        provider_name: Provider 名称，默认从环境变量 DEFAULT_LLM_PROVIDER 获取
        **kwargs: 传递给 Provider 的参数

    Returns:
        BaseLLMProvider 实例

    Example:
        >>> provider = get_provider()  # 使用默认 Provider
        >>> provider = get_provider("openai", model="gpt-4o")
        >>> response = provider.chat([Message(role="user", content="Hello")])
    """
    return ProviderFactory.get_or_create(provider_name, **kwargs)


def set_default_provider(provider_name: str):
    """设置默认 Provider"""
    global DEFAULT_PROVIDER
    if provider_name.lower() not in PROVIDER_REGISTRY:
        raise ValueError(f"不支持的 Provider: {provider_name}")
    DEFAULT_PROVIDER = provider_name.lower()
    os.environ["DEFAULT_LLM_PROVIDER"] = provider_name.lower()
