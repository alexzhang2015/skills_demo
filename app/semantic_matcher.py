"""
语义匹配模块
使用 embedding 实现用户输入与 Skill description 的语义匹配
"""
import os
import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class MatchResult:
    """匹配结果"""
    skill_name: str
    description: str
    score: float  # 相似度分数 0-1
    confidence: str  # high, medium, low


class SemanticMatcher:
    """
    语义匹配器
    支持多种 embedding 后端：
    - Voyage AI (默认，推荐用于生产)
    - OpenAI
    - 本地简单匹配 (fallback)
    """

    def __init__(self, backend: str = "auto"):
        """
        初始化匹配器

        Args:
            backend: "voyage", "openai", "local", "auto"
                     auto 会按优先级尝试可用的后端
        """
        self.backend = backend
        self._client = None
        self._embeddings_cache: dict[str, np.ndarray] = {}

        self._init_backend()

    def _init_backend(self):
        """初始化 embedding 后端"""
        if self.backend == "auto":
            # 按优先级尝试
            if os.environ.get("VOYAGE_API_KEY"):
                self.backend = "voyage"
            elif os.environ.get("OPENAI_API_KEY"):
                self.backend = "openai"
            else:
                self.backend = "local"
                print("Warning: No embedding API key found, using local fallback matcher")

        if self.backend == "voyage":
            try:
                import voyageai
                self._client = voyageai.Client()
            except ImportError:
                print("Warning: voyageai not installed, falling back to local")
                self.backend = "local"
        elif self.backend == "openai":
            try:
                import openai
                self._client = openai.OpenAI()
            except ImportError:
                print("Warning: openai not installed, falling back to local")
                self.backend = "local"

    def _get_embedding(self, text: str) -> np.ndarray:
        """获取文本的 embedding 向量"""
        # 检查缓存
        cache_key = f"{self.backend}:{text[:100]}"
        if cache_key in self._embeddings_cache:
            return self._embeddings_cache[cache_key]

        if self.backend == "voyage":
            result = self._client.embed([text], model="voyage-2")
            embedding = np.array(result.embeddings[0])
        elif self.backend == "openai":
            result = self._client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            embedding = np.array(result.data[0].embedding)
        else:
            # 本地简单匹配：使用词袋模型 + TF-IDF 风格
            embedding = self._local_embedding(text)

        self._embeddings_cache[cache_key] = embedding
        return embedding

    def _local_embedding(self, text: str) -> np.ndarray:
        """
        本地简单 embedding（不需要 API）
        使用字符 n-gram 和词频特征
        """
        text = text.lower()
        words = text.split()

        # 创建一个简单的特征向量
        # 1. 字符 n-gram 频率
        char_ngrams = {}
        for n in [2, 3]:
            for i in range(len(text) - n + 1):
                ngram = text[i:i+n]
                char_ngrams[ngram] = char_ngrams.get(ngram, 0) + 1

        # 2. 词频
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 3. 关键词检测
        keywords = [
            "file", "read", "write", "create", "delete", "list",
            "code", "test", "run", "build", "deploy", "git",
            "commit", "push", "pull", "merge", "branch",
            "search", "find", "grep", "replace", "edit",
            "format", "lint", "check", "validate", "analyze",
            "generate", "summarize", "explain", "document",
            "api", "request", "response", "data", "json",
            "error", "debug", "fix", "bug", "issue"
        ]

        # 构建固定维度的向量
        dim = 128
        vector = np.zeros(dim)

        # 填充特征
        for i, kw in enumerate(keywords[:dim//2]):
            if kw in text:
                vector[i] = text.count(kw) / (len(text) + 1)

        # 添加一些统计特征
        vector[dim//2] = len(words) / 100
        vector[dim//2 + 1] = len(text) / 500
        vector[dim//2 + 2] = len(set(words)) / (len(words) + 1)

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot / (norm1 * norm2))

    def match(
        self,
        query: str,
        skills: list[tuple[str, str]],  # [(name, description), ...]
        threshold: float = 0.3
    ) -> list[MatchResult]:
        """
        匹配用户查询与 Skills

        Args:
            query: 用户输入
            skills: Skill 列表，每项为 (name, description)
            threshold: 相似度阈值

        Returns:
            匹配结果列表，按分数降序排列
        """
        if not skills:
            return []

        query_embedding = self._get_embedding(query)
        results = []

        for name, description in skills:
            # 组合 name 和 description 进行匹配
            skill_text = f"{name}: {description}"
            skill_embedding = self._get_embedding(skill_text)

            score = self._cosine_similarity(query_embedding, skill_embedding)

            if score >= threshold:
                # 确定置信度级别
                if score >= 0.7:
                    confidence = "high"
                elif score >= 0.5:
                    confidence = "medium"
                else:
                    confidence = "low"

                results.append(MatchResult(
                    skill_name=name,
                    description=description,
                    score=score,
                    confidence=confidence
                ))

        # 按分数降序排列
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def find_best_match(
        self,
        query: str,
        skills: list[tuple[str, str]],
        min_score: float = 0.4
    ) -> Optional[MatchResult]:
        """
        找到最佳匹配的 Skill

        Args:
            query: 用户输入
            skills: Skill 列表
            min_score: 最低分数要求

        Returns:
            最佳匹配结果，如果没有满足条件的则返回 None
        """
        matches = self.match(query, skills, threshold=min_score)
        return matches[0] if matches else None

    def clear_cache(self):
        """清除 embedding 缓存"""
        self._embeddings_cache.clear()


class KeywordMatcher:
    """
    关键词匹配器（简单快速的 fallback）
    用于在语义匹配之前快速筛选
    """

    def __init__(self):
        self.keyword_weights = {
            # 动作词
            "create": 2.0, "generate": 2.0, "make": 1.5,
            "read": 2.0, "get": 1.5, "fetch": 1.5, "load": 1.5,
            "write": 2.0, "save": 1.5, "update": 1.5,
            "delete": 2.0, "remove": 1.5,
            "search": 2.0, "find": 2.0, "grep": 2.0,
            "run": 2.0, "execute": 2.0, "start": 1.5,
            "test": 2.0, "check": 1.5, "validate": 1.5,
            "format": 1.5, "lint": 1.5,
            "commit": 2.0, "push": 1.5, "pull": 1.5,
            "summarize": 2.0, "explain": 2.0,
            # 对象词
            "file": 1.5, "code": 1.5, "text": 1.0,
            "git": 2.0, "branch": 1.5,
            "api": 1.5, "request": 1.0,
            "error": 1.5, "bug": 1.5,
        }

    def extract_keywords(self, text: str) -> set[str]:
        """提取文本中的关键词"""
        words = text.lower().split()
        return set(w for w in words if w in self.keyword_weights)

    def quick_match(
        self,
        query: str,
        skills: list[tuple[str, str]]
    ) -> list[tuple[str, str, float]]:
        """
        快速关键词匹配

        Returns:
            [(name, description, score), ...] 按分数降序
        """
        query_keywords = self.extract_keywords(query)

        if not query_keywords:
            return [(name, desc, 0.1) for name, desc in skills]

        results = []
        for name, description in skills:
            skill_text = f"{name} {description}"
            skill_keywords = self.extract_keywords(skill_text)

            # 计算交集的加权分数
            common = query_keywords & skill_keywords
            if common:
                score = sum(self.keyword_weights.get(k, 1.0) for k in common)
                score = score / (len(query_keywords) + 1)  # 归一化
            else:
                score = 0.0

            results.append((name, description, score))

        results.sort(key=lambda x: x[2], reverse=True)
        return results
