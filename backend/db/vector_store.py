from typing import Dict, List, Any, Optional
import numpy as np
import logging
from backend.ai_model.embedder import Embedder, FaissIndex
from backend.ai_model.rag_utils import chunk_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """A vector store for efficient similarity search of text chunks using FAISS.
    
    This class handles the indexing and querying of text chunks with their vector
    representations, allowing for efficient similarity searches.
    """
    
    def __init__(self, dim: int):
        """Initialize the VectorStore with a specific embedding dimension.
        
        Args:
            dim: The dimensionality of the embeddings to be stored.
        """
        self.dim = dim
        self.embedder = Embedder()
        self.index = FaissIndex(dim)
        logger.info(f"Initialized VectorStore with dimension: {dim}")

    def index_news(self, news_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """Index a news article by chunking and embedding its text.
        
        Args:
            news_id: Unique identifier for the news article.
            text: The full text content of the news article.
            metadata: Additional metadata to store with each chunk.
            
        Returns:
            None
        """
        try:
            # Chunk the text into smaller pieces
            chunks = chunk_text(text)
            if not chunks:
                logger.warning(f"No valid chunks created for news_id: {news_id}")
                return
                
            # Generate embeddings for each chunk
            embs = self.embedder.embed(chunks)
            if len(embs) == 0:
                logger.warning(f"No embeddings generated for news_id: {news_id}")
                return
                
            # Prepare metadata for each chunk
            metas = []
            for i, (chunk, emb) in enumerate(zip(chunks, embs)):
                chunk_meta = metadata.copy()
                chunk_meta.update({
                    "news_id": news_id,
                    "chunk_id": f"{news_id}_{i}",
                    "chunk": chunk,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
                metas.append(chunk_meta)
            
            # Add to the index
            self.index.add(embs.astype(np.float32), metas)
            logger.debug(f"Indexed {len(chunks)} chunks for news_id: {news_id}")
            
        except Exception as e:
            logger.error(f"Error indexing news {news_id}: {str(e)}")
            raise

    def query(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar text chunks to the query.
        
        Args:
            text: The query text to search for.
            top_k: The number of most similar results to return.
            
        Returns:
            A list of dictionaries containing the search results with 'score' and 'meta' keys.
            Returns an empty list if no results are found or an error occurs.
        """
        try:
            if not text.strip():
                logger.warning("Empty query text provided")
                return []
                
            # Get embedding for the query
            query_emb = self.embedder.embed([text])
            if query_emb is None or len(query_emb) == 0:
                logger.warning("Failed to generate query embedding")
                return []
                
            # Search the index
            results = self.index.search(query_emb, top_k=top_k)
            return results[0] if results else []
            
        except Exception as e:
            logger.error(f"Error during query: {str(e)}")
            return []
            
    def save_index(self, filepath: str) -> bool:
        """Save the FAISS index to disk.
        
        Args:
            filepath: Path where to save the index.
            
        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            # In a real implementation, you would save both the FAISS index
            # and the associated metadata to disk
            logger.info(f"Saving index to {filepath}")
            # Implementation would go here
            return True
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            return False
            
    @classmethod
    def load_index(cls, filepath: str) -> Optional['VectorStore']:
        """Load a FAISS index from disk.
        
        Args:
            filepath: Path to the saved index.
            
        Returns:
            An instance of VectorStore if successful, None otherwise.
        """
        try:
            # In a real implementation, you would load both the FAISS index
            # and the associated metadata from disk
            logger.info(f"Loading index from {filepath}")
            # Implementation would go here
            return None
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            return None