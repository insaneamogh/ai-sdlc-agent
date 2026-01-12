"""
ChromaDB Vector Store Module

This module provides vector storage and retrieval using ChromaDB for:
- Storing Jira tickets, PRs, and code snippets
- Semantic search for similar content
- RAG (Retrieval Augmented Generation) support
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.config import get_settings
from app.utils.logger import logger


class Document(BaseModel):
    """Model for a document to store in vector DB"""
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    source_type: str = "unknown"  # jira, github_pr, code, test


class SearchResult(BaseModel):
    """Model for a search result"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source_type: str


class ChromaStore:
    """
    Vector store using ChromaDB for semantic search and RAG.
    
    This class handles:
    - Document storage with embeddings
    - Semantic similarity search
    - Filtering by metadata
    - Persistence to disk
    
    Example usage:
        store = ChromaStore()
        store.add_documents([doc1, doc2])
        results = store.search("authentication", limit=5)
    """
    
    def __init__(self, collection_name: str = "sdlc_documents"):
        """
        Initialize the ChromaDB store.
        
        Args:
            collection_name: Name of the collection to use
        """
        settings = get_settings()
        self.persist_directory = settings.chroma_persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embeddings = None
        
        logger.info(f"Initialized ChromaStore with collection: {collection_name}")
    
    def _get_client(self):
        """Lazy load the ChromaDB client"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                self._client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                ))
                logger.info("ChromaDB client initialized")
            except ImportError:
                logger.error("chromadb not installed")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
        return self._client
    
    def _get_collection(self):
        """Get or create the collection"""
        if self._collection is None:
            client = self._get_client()
            if client:
                try:
                    self._collection = client.get_or_create_collection(
                        name=self.collection_name,
                        metadata={"description": "SDLC documents for RAG"}
                    )
                    logger.info(f"Collection '{self.collection_name}' ready")
                except Exception as e:
                    logger.error(f"Failed to get collection: {e}")
        return self._collection
    
    def _get_embeddings(self):
        """Get the embedding function"""
        if self._embeddings is None:
            try:
                from app.services.embedding_service import EmbeddingService
                self._embeddings = EmbeddingService()
            except Exception as e:
                logger.error(f"Failed to initialize embeddings: {e}")
        return self._embeddings
    
    def add_documents(self, documents: List[Document]) -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
        
        Returns:
            True if successful
        """
        if not documents:
            return True
        
        collection = self._get_collection()
        embeddings_service = self._get_embeddings()
        
        if not collection:
            logger.warning("Collection not available, skipping add")
            return False
        
        try:
            # Generate embeddings
            texts = [doc.content for doc in documents]
            embeddings = embeddings_service.embed_texts_sync(texts) if embeddings_service else None
            
            # Prepare data for ChromaDB
            ids = [doc.id for doc in documents]
            metadatas = [
                {**doc.metadata, "source_type": doc.source_type}
                for doc in documents
            ]
            
            # Add to collection
            if embeddings:
                collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            else:
                collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def search(
        self,
        query: str,
        limit: int = 5,
        source_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            source_type: Filter by source type (jira, github_pr, code, test)
            filters: Additional metadata filters
        
        Returns:
            List of search results with scores
        """
        collection = self._get_collection()
        embeddings_service = self._get_embeddings()
        
        if not collection:
            logger.warning("Collection not available, returning empty results")
            return []
        
        try:
            # Build where clause for filtering
            where = {}
            if source_type:
                where["source_type"] = source_type
            if filters:
                where.update(filters)
            
            # Generate query embedding
            query_embedding = None
            if embeddings_service:
                query_embedding = embeddings_service.embed_text_sync(query)
            
            # Search
            if query_embedding:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=where if where else None
                )
            else:
                results = collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where if where else None
                )
            
            # Parse results
            search_results = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    search_results.append(SearchResult(
                        id=doc_id,
                        content=results["documents"][0][i] if results["documents"] else "",
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        score=1 - results["distances"][0][i] if results["distances"] else 0.0,
                        source_type=results["metadatas"][0][i].get("source_type", "unknown") if results["metadatas"] else "unknown"
                    ))
            
            logger.info(f"Search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_documents(self, ids: List[str]) -> bool:
        """
        Delete documents by ID.
        
        Args:
            ids: List of document IDs to delete
        
        Returns:
            True if successful
        """
        collection = self._get_collection()
        if not collection:
            return False
        
        try:
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document if found, None otherwise
        """
        collection = self._get_collection()
        if not collection:
            return None
        
        try:
            result = collection.get(ids=[doc_id])
            if result and result["ids"]:
                return Document(
                    id=result["ids"][0],
                    content=result["documents"][0] if result["documents"] else "",
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                    source_type=result["metadatas"][0].get("source_type", "unknown") if result["metadatas"] else "unknown"
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    def count(self) -> int:
        """
        Get the number of documents in the store.
        
        Returns:
            Document count
        """
        collection = self._get_collection()
        if not collection:
            return 0
        
        try:
            return collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    def clear(self) -> bool:
        """
        Clear all documents from the store.
        
        Returns:
            True if successful
        """
        client = self._get_client()
        if not client:
            return False
        
        try:
            client.delete_collection(self.collection_name)
            self._collection = None
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    # ===========================================
    # Convenience methods for specific content types
    # ===========================================
    
    def add_jira_ticket(
        self,
        ticket_id: str,
        title: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a Jira ticket to the store"""
        content = f"Title: {title}\n\nDescription: {description}"
        doc = Document(
            id=f"jira_{ticket_id}",
            content=content,
            metadata=metadata or {"ticket_id": ticket_id, "title": title},
            source_type="jira"
        )
        return self.add_documents([doc])
    
    def add_github_pr(
        self,
        pr_number: int,
        repo: str,
        title: str,
        description: str,
        diff: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a GitHub PR to the store"""
        content = f"PR #{pr_number}: {title}\n\nDescription: {description}"
        if diff:
            content += f"\n\nDiff:\n{diff[:2000]}"  # Limit diff size
        
        doc = Document(
            id=f"pr_{repo}_{pr_number}",
            content=content,
            metadata=metadata or {"pr_number": pr_number, "repo": repo, "title": title},
            source_type="github_pr"
        )
        return self.add_documents([doc])
    
    def add_code_snippet(
        self,
        file_path: str,
        content: str,
        language: str = "python",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a code snippet to the store"""
        doc = Document(
            id=f"code_{file_path.replace('/', '_')}",
            content=f"File: {file_path}\nLanguage: {language}\n\n{content}",
            metadata=metadata or {"file_path": file_path, "language": language},
            source_type="code"
        )
        return self.add_documents([doc])
    
    def search_similar_tickets(
        self,
        query: str,
        limit: int = 5
    ) -> List[SearchResult]:
        """Search for similar Jira tickets"""
        return self.search(query, limit=limit, source_type="jira")
    
    def search_similar_code(
        self,
        query: str,
        limit: int = 5,
        language: Optional[str] = None
    ) -> List[SearchResult]:
        """Search for similar code snippets"""
        filters = {"language": language} if language else None
        return self.search(query, limit=limit, source_type="code", filters=filters)
