"""
向量存储

提供 Skill 的向量化存储和语义搜索能力
"""

import os
import json
import hashlib
import numpy as np
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple


@dataclass
class VectorEntry:
    """向量条目"""
    entry_id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchMatch:
    """搜索匹配结果"""
    entry_id: str
    content: str
    score: float  # 相似度分数 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingProvider:
    """
    Embedding 提供者抽象

    支持多种 Embedding 后端
    """

    def __init__(self, backend: str = "auto"):
        self.backend = backend
        self._client = None
        self._init_backend()

    def _init_backend(self):
        """初始化后端"""
        if self.backend == "auto":
            # 按优先级尝试
            if os.environ.get("VOYAGE_API_KEY"):
                self.backend = "voyage"
            elif os.environ.get("OPENAI_API_KEY"):
                self.backend = "openai"
            else:
                self.backend = "local"

        if self.backend == "voyage":
            try:
                import voyageai
                self._client = voyageai.Client()
            except ImportError:
                self.backend = "local"

        elif self.backend == "openai":
            try:
                import openai
                self._client = openai.OpenAI()
            except ImportError:
                self.backend = "local"

    def embed(self, texts: List[str]) -> List[np.ndarray]:
        """生成 embedding"""
        if self.backend == "voyage":
            result = self._client.embed(texts, model="voyage-2")
            return [np.array(e) for e in result.embeddings]

        elif self.backend == "openai":
            result = self._client.embeddings.create(
                input=texts,
                model="text-embedding-3-small"
            )
            return [np.array(e.embedding) for e in result.data]

        else:
            # 本地简单 embedding
            return [self._local_embedding(text) for text in texts]

    def _local_embedding(self, text: str) -> np.ndarray:
        """本地简单 embedding"""
        text = text.lower()
        words = text.split()

        # 关键词列表
        keywords = [
            "file", "read", "write", "create", "delete", "list",
            "code", "test", "run", "build", "deploy", "git",
            "commit", "push", "pull", "merge", "branch",
            "search", "find", "grep", "replace", "edit",
            "format", "lint", "check", "validate", "analyze",
            "generate", "summarize", "explain", "document",
            "api", "request", "response", "data", "json",
            "error", "debug", "fix", "bug", "issue",
            "product", "price", "order", "customer", "inventory",
            "pos", "app", "web", "mobile", "backend",
        ]

        # 构建特征向量
        dim = 256
        vector = np.zeros(dim)

        # 关键词特征
        for i, kw in enumerate(keywords[:dim // 2]):
            if kw in text:
                vector[i] = text.count(kw) / (len(text) + 1)

        # 统计特征
        vector[dim // 2] = len(words) / 100
        vector[dim // 2 + 1] = len(text) / 500
        vector[dim // 2 + 2] = len(set(words)) / (len(words) + 1) if words else 0

        # 字符 n-gram 哈希特征
        for n in [2, 3]:
            for i in range(len(text) - n + 1):
                ngram = text[i:i + n]
                hash_idx = hash(ngram) % (dim // 4) + dim // 2 + 10
                if hash_idx < dim:
                    vector[hash_idx] += 1

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector


class VectorStore:
    """
    向量存储

    功能：
    - 存储文本和向量
    - 语义相似度搜索
    - 持久化到文件
    """

    def __init__(
        self,
        storage_path: str = None,
        embedding_backend: str = "auto"
    ):
        self.storage_path = Path(storage_path) if storage_path else Path("data/vectors")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._embedding_provider = EmbeddingProvider(embedding_backend)
        self._entries: Dict[str, VectorEntry] = {}
        self._vectors: Optional[np.ndarray] = None
        self._entry_ids: List[str] = []

        # 加载已有数据
        self._load()

    def _load(self):
        """加载数据"""
        index_file = self.storage_path / "index.json"
        vectors_file = self.storage_path / "vectors.npy"

        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for item in data.get("entries", []):
                    entry_id = item["entry_id"]
                    self._entries[entry_id] = VectorEntry(
                        entry_id=entry_id,
                        content=item["content"],
                        embedding=np.array([]),  # 延迟加载
                        metadata=item.get("metadata", {}),
                    )
                    self._entry_ids.append(entry_id)

                if vectors_file.exists():
                    self._vectors = np.load(vectors_file)

            except Exception as e:
                print(f"Warning: Failed to load vector store: {e}")

    def _save(self):
        """保存数据"""
        index_file = self.storage_path / "index.json"
        vectors_file = self.storage_path / "vectors.npy"

        # 保存索引
        data = {
            "updated_at": datetime.utcnow().isoformat(),
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "content": e.content,
                    "metadata": e.metadata,
                }
                for e in self._entries.values()
            ]
        }
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存向量
        if self._vectors is not None:
            np.save(vectors_file, self._vectors)

    def add(
        self,
        content: str,
        entry_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加条目

        Args:
            content: 文本内容
            entry_id: 条目 ID（可选，自动生成）
            metadata: 元数据

        Returns:
            条目 ID
        """
        # 生成 ID
        if not entry_id:
            entry_id = hashlib.md5(content.encode()).hexdigest()[:12]

        # 生成 embedding
        embeddings = self._embedding_provider.embed([content])
        embedding = embeddings[0]

        # 创建条目
        entry = VectorEntry(
            entry_id=entry_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
        )

        # 更新内存
        self._entries[entry_id] = entry

        if entry_id not in self._entry_ids:
            self._entry_ids.append(entry_id)

        # 更新向量矩阵
        if self._vectors is None:
            self._vectors = embedding.reshape(1, -1)
        else:
            # 检查是否是更新
            try:
                idx = self._entry_ids.index(entry_id)
                self._vectors[idx] = embedding
            except ValueError:
                self._vectors = np.vstack([self._vectors, embedding])

        # 保存
        self._save()

        return entry_id

    def add_batch(
        self,
        items: List[Tuple[str, str, Dict[str, Any]]]  # [(content, entry_id, metadata), ...]
    ) -> List[str]:
        """批量添加"""
        contents = [item[0] for item in items]

        # 批量生成 embedding
        embeddings = self._embedding_provider.embed(contents)

        entry_ids = []
        for i, (content, entry_id, metadata) in enumerate(items):
            if not entry_id:
                entry_id = hashlib.md5(content.encode()).hexdigest()[:12]

            entry = VectorEntry(
                entry_id=entry_id,
                content=content,
                embedding=embeddings[i],
                metadata=metadata or {},
            )

            self._entries[entry_id] = entry
            if entry_id not in self._entry_ids:
                self._entry_ids.append(entry_id)

            entry_ids.append(entry_id)

        # 重建向量矩阵
        self._rebuild_vectors()
        self._save()

        return entry_ids

    def _rebuild_vectors(self):
        """重建向量矩阵"""
        if not self._entries:
            self._vectors = None
            return

        vectors = []
        for entry_id in self._entry_ids:
            if entry_id in self._entries:
                vectors.append(self._entries[entry_id].embedding)

        self._vectors = np.vstack(vectors) if vectors else None

    def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.3
    ) -> List[SearchMatch]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值

        Returns:
            匹配结果列表
        """
        if self._vectors is None or len(self._entries) == 0:
            return []

        # 生成查询 embedding
        query_embedding = self._embedding_provider.embed([query])[0]

        # 计算余弦相似度
        scores = self._cosine_similarity(query_embedding, self._vectors)

        # 排序并过滤
        indices = np.argsort(scores)[::-1]
        results = []

        for idx in indices[:top_k]:
            score = scores[idx]
            if score < threshold:
                break

            entry_id = self._entry_ids[idx]
            entry = self._entries.get(entry_id)

            if entry:
                results.append(SearchMatch(
                    entry_id=entry_id,
                    content=entry.content,
                    score=float(score),
                    metadata=entry.metadata,
                ))

        return results

    def _cosine_similarity(
        self,
        query: np.ndarray,
        vectors: np.ndarray
    ) -> np.ndarray:
        """计算余弦相似度"""
        query_norm = np.linalg.norm(query)
        vectors_norm = np.linalg.norm(vectors, axis=1)

        # 避免除零
        vectors_norm = np.where(vectors_norm == 0, 1e-10, vectors_norm)

        dot_products = np.dot(vectors, query)
        similarities = dot_products / (vectors_norm * query_norm)

        return similarities

    def delete(self, entry_id: str) -> bool:
        """删除条目"""
        if entry_id not in self._entries:
            return False

        del self._entries[entry_id]

        if entry_id in self._entry_ids:
            self._entry_ids.remove(entry_id)

        self._rebuild_vectors()
        self._save()

        return True

    def get(self, entry_id: str) -> Optional[VectorEntry]:
        """获取条目"""
        return self._entries.get(entry_id)

    def count(self) -> int:
        """获取条目数量"""
        return len(self._entries)

    def clear(self):
        """清空存储"""
        self._entries.clear()
        self._entry_ids.clear()
        self._vectors = None
        self._save()


class SkillVectorStore(VectorStore):
    """
    Skill 向量存储

    专门用于 Skill 的向量化存储和 RAG 检索
    """

    def add_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        content: str,
        category: str = None,
        tags: List[str] = None
    ) -> str:
        """
        添加 Skill 到向量存储

        Args:
            skill_id: Skill ID
            name: 名称
            description: 描述
            content: 完整内容
            category: 分类
            tags: 标签

        Returns:
            条目 ID
        """
        # 构建索引文本（组合名称、描述、标签）
        index_text = f"{name}\n{description}"
        if tags:
            index_text += f"\n{' '.join(tags)}"

        metadata = {
            "skill_id": skill_id,
            "name": name,
            "description": description,
            "category": category,
            "tags": tags or [],
            "type": "skill",
        }

        return self.add(index_text, entry_id=skill_id, metadata=metadata)

    def search_skills(
        self,
        query: str,
        top_k: int = 5,
        category: str = None
    ) -> List[SearchMatch]:
        """
        搜索相关 Skill

        Args:
            query: 查询文本
            top_k: 返回数量
            category: 过滤分类

        Returns:
            匹配的 Skill 列表
        """
        results = self.search(query, top_k=top_k * 2, threshold=0.2)

        # 过滤非 Skill 条目
        results = [r for r in results if r.metadata.get("type") == "skill"]

        # 按分类过滤
        if category:
            results = [r for r in results if r.metadata.get("category") == category]

        return results[:top_k]

    def find_similar_skills(
        self,
        skill_id: str,
        top_k: int = 5
    ) -> List[SearchMatch]:
        """查找相似 Skill"""
        entry = self.get(skill_id)
        if not entry:
            return []

        results = self.search(entry.content, top_k=top_k + 1)

        # 排除自身
        return [r for r in results if r.entry_id != skill_id][:top_k]


# 全局实例
_vector_store: Optional[SkillVectorStore] = None


def get_vector_store(storage_path: str = None) -> SkillVectorStore:
    """获取向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = SkillVectorStore(storage_path)
    return _vector_store
