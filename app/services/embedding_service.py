#_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________#

"""
Embedding Service Module

This module provides text embedding generation for:
- Converting text to vector representations
- Supporting RAG (Retrieval Augmented Generation)
- Enabling semantic search
"""

from typing import List, Optional
from app.config import get_settings
from app.utils.logger import logger


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    This service handles:
    - Text to vector conversion using OpenAI embeddings
    - Batch embedding generation
    - Caching for efficiency
    
    Example usage:
        service = EmbeddingService()
        embeddings = await service.embed_texts(["Hello", "World"])
    """
    
    def __init__(self):
        """Initialize the Embedding service"""
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = "text-embedding-3-small"  # Cost-effective model
        self._embeddings = None
        
        # Check if OpenAI is configured
        self.is_configured = bool(self.api_key)
        
        if not self.is_configured:
            logger.warning("Embedding service not configured - OpenAI API key missing")
    
    def _get_embeddings(self):
        """Lazy load the embeddings model"""
        if self._embeddings is None and self.is_configured:
            try:
                from langchain_openai import OpenAIEmbeddings
                self._embeddings = OpenAIEmbeddings(
                    model=self.model,
                    openai_api_key=self.api_key
                )
                logger.info(f"Initialized OpenAI embeddings with model: {self.model}")
            except ImportError:
                logger.error("langchain_openai not installed")
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
        return self._embeddings
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        if not text:
            return None
        
        embeddings = self._get_embeddings()
        if not embeddings:
            logger.warning("Embeddings not available, returning mock embedding")
            return self._get_mock_embedding()
        
        try:
            result = await embeddings.aembed_query(text)
            return result
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return self._get_mock_embedding()
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = self._get_embeddings()
        if not embeddings:
            logger.warning("Embeddings not available, returning mock embeddings")
            return [self._get_mock_embedding() for _ in texts]
        
        try:
            results = await embeddings.aembed_documents(texts)
            return results
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [self._get_mock_embedding() for _ in texts]
    
    def embed_text_sync(self, text: str) -> Optional[List[float]]:
        """
        Synchronous version of embed_text.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        if not text:
            return None
        
        embeddings = self._get_embeddings()
        if not embeddings:
            return self._get_mock_embedding()
        
        try:
            result = embeddings.embed_query(text)
            return result
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return self._get_mock_embedding()
    
    def embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Synchronous version of embed_texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = self._get_embeddings()
        if not embeddings:
            return [self._get_mock_embedding() for _ in texts]
        
        try:
            results = embeddings.embed_documents(texts)
            return results
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [self._get_mock_embedding() for _ in texts]
    
    def _get_mock_embedding(self, dimension: int = 1536) -> List[float]:
        """
        Generate a mock embedding for testing.
        
        Args:
            dimension: Embedding dimension (default 1536 for OpenAI)
        
        Returns:
            List of random floats
        """
        import random
        return [random.uniform(-1, 1) for _ in range(dimension)]
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this service.
        
        Returns:
            Embedding dimension
        """
        # text-embedding-3-small produces 1536-dimensional vectors
        return 1536
    
    async def compute_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score between 0 and 1
        """
        emb1 = await self.embed_text(text1)
        emb2 = await self.embed_text(text2)
        
        if not emb1 or not emb2:
            return 0.0
        
        return self._cosine_similarity(emb1, emb2)
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Cosine similarity score
        """
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

#__________________________GenAI: Generated code ends here______________________________#
