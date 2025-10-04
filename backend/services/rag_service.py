from typing import Dict, Any
import logging
from backend.db.vector_store import VectorStore
from backend.ai_model.summarizer import summarize_text
from backend.ai_model.prompts.prompt_style_news import SYSTEM_PROMPT as STYLE_PROMPT
from backend.ai_model.llm_client import LocalLLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM client with error handling
try:
    llm = LocalLLMClient()
except Exception as e:
    logger.error(f"Failed to initialize LLM client: {str(e)}")
    raise

# Configuration
VECTOR_DIM = 384  # Should match the embedder model's output dimension

# Initialize vector store
try:
    vector_store = VectorStore(dim=VECTOR_DIM)
    logger.info("Vector store initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize vector store: {str(e)}")
    raise


def process_and_index(news_id: str, text: str, metadata: Dict[str, Any]) -> str:
    """Process and index a news article.
    
    Args:
        news_id: Unique identifier for the news article
        text: Full text content of the article
        metadata: Additional metadata to store with the article
        
    Returns:
        str: Generated summary of the article
        
    Raises:
        ValueError: If input validation fails
        RuntimeError: If processing or indexing fails
    """
    if not news_id or not isinstance(news_id, str):
        raise ValueError("news_id must be a non-empty string")
    if not text or not isinstance(text, str):
        raise ValueError("text must be a non-empty string")
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a dictionary")
    
    try:
        # Generate summary
        logger.info(f"Generating summary for news_id: {news_id}")
        summary = summarize_text(text)
        
        # Update metadata with summary
        metadata = metadata.copy()
        metadata['summary'] = summary
        
        # Index the document
        logger.debug(f"Indexing document: {news_id}")
        vector_store.index_news(news_id, text, metadata)
        
        logger.info(f"Successfully processed and indexed news_id: {news_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Error processing news_id {news_id}: {str(e)}")
        raise RuntimeError(f"Failed to process and index document: {str(e)}")


def retrieve_and_normalize(text: str, top_k: int = 5) -> str:
    """Retrieve relevant context and normalize the input text.
    
    Args:
        text: Input text to be normalized
        top_k: Number of context chunks to retrieve
        
    Returns:
        str: Normalized text in a consistent style
        
    Raises:
        ValueError: If input validation fails
        RuntimeError: If retrieval or normalization fails
    """
    if not text or not isinstance(text, str):
        raise ValueError("text must be a non-empty string")
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    
    try:
        # Retrieve relevant context
        logger.debug(f"Retrieving top-{top_k} relevant contexts")
        retrieved = vector_store.query(text, top_k=top_k)
        
        if not retrieved:
            logger.warning("No relevant context found for the query")
            return text  # Return original text if no context found
        
        # Prepare context for the LLM
        context_parts = [
            "Собран контекст ниже. На его основе приведи основной текст к единому стилю.\n\n"
        ]
        
        for i, result in enumerate(retrieved, 1):
            meta = result.get('meta', {})
            chunk = meta.get('chunk', '')
            context_parts.append(f"Контекст {i}:\n{chunk}\n")
        
        # Assemble the final prompt
        prompt = "\n\n".join(context_parts) + f"\n\nВходная новость:\n{text}"
        
        # Generate normalized output
        logger.info("Generating normalized output")
        normalized = llm.chat(
            prompt=prompt,
            system=STYLE_PROMPT,
            max_tokens=1024,
            temperature=0.3  # Lower temperature for more consistent style
        )
        
        return normalized.strip()
        
    except Exception as e:
        logger.error(f"Error in retrieve_and_normalize: {str(e)}")
        raise RuntimeError(f"Failed to normalize text: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Example metadata
    example_metadata = {
        "source": "example_source",
        "date": "2023-01-01",
        "author": "AI System"
    }
    
    # Example usage of process_and_index
    example_text = """
    Вчера на фондовом рынке произошло значительное падение индекса S&P 500. 
    Эксперты связывают это с ростом инфляционных ожиданий.
    """
    
    try:
        summary = process_and_index("example_news_1", example_text, example_metadata)
        print(f"Generated summary: {summary}")
        
        # Example usage of retrieve_and_normalize
        query = "Новость о падении индекса S&P 500"
        result = retrieve_and_normalize(query)
        print(f"\nNormalized result:\n{result}")
        
    except Exception as e:
        logger.critical(f"Example failed: {str(e)}", exc_info=True)