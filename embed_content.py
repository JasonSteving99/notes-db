from google import genai
import os
from typing import List, Optional


def get_embedding(
    text: str,
    model: str = "gemini-embedding-exp-03-07",
    api_key: Optional[str] = None
) -> List[float]:
    """
    Generate text embeddings using Gemini API.
    
    Args:
        text: The text to generate embeddings for
        model: The embedding model to use
        api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)
        
    Returns:
        A list of float values representing the embedding
        
    Raises:
        ValueError: If no API key is available
        Exception: If the API call fails
    """
    # Get API key from parameter or environment
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("Gemini API key must be provided or set as GEMINI_API_KEY environment variable")
    
    # Initialize the client
    client = genai.Client(api_key=api_key)
    
    # Generate embedding
    result = client.models.embed_content(
        model=model,
        contents=text,
    )
    
    # Return the embedding values (first element only)
    return result.embeddings[0].values