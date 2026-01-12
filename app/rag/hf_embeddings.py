"""
Hugging Face Inference API helper for embeddings.
Uses the hosted API instead of downloading models locally.
"""
import sys
from pathlib import Path
import numpy as np
import httpx
from typing import List, Union

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import HUGGINGFACE_API_KEY

# Hugging Face Inference API endpoints for sentence-transformers/all-MiniLM-L6-v2
# Try router endpoint first (newer), fallback to standard endpoint
HF_API_URL_ROUTER = (
    "https://router.huggingface.co/"
    "hf-inference/models/"
    "sentence-transformers/all-MiniLM-L6-v2/"
    "pipeline/feature-extraction"
)

HF_API_URL_STANDARD = (
    "https://api-inference.huggingface.co/models/"
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Timeout for API requests (in seconds)
API_TIMEOUT = 30.0


def get_embeddings(texts: Union[str, List[str]], normalize: bool = True, batch_size: int = 32) -> np.ndarray:
    """
    Get embeddings from Hugging Face Inference API.
    
    Args:
        texts: Single text string or list of text strings
        normalize: Whether to normalize embeddings (for cosine similarity)
        batch_size: Number of texts to process per API call (for large batches)
    
    Returns:
        numpy array of embeddings with shape (n_texts, embedding_dim)
    """
    # Convert single string to list
    if isinstance(texts, str):
        texts = [texts]
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    all_embeddings = []
    
    # Process in batches if needed
    with httpx.Client(timeout=API_TIMEOUT) as client:
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Prepare payload
            payload = {
                "inputs": batch_texts,
                "options": {
                    "wait_for_model": True  # Wait if model is loading
                }
            }
            
            # Make API request - try router endpoint first, fallback to standard
            api_urls = [HF_API_URL_ROUTER, HF_API_URL_STANDARD]
            response = None
            last_error = None
            
            for api_url in api_urls:
                try:
                    response = client.post(api_url, json=payload, headers=headers)
                    
                    # If successful, break out of loop
                    if response.status_code == 200:
                        break
                    
                    # If 403 on router, try standard endpoint
                    if response.status_code == 403 and api_url == HF_API_URL_ROUTER:
                        last_error = response.text
                        continue
                    
                    # For other errors, handle below
                    break
                except Exception as e:
                    last_error = str(e)
                    if api_url == api_urls[-1]:  # Last URL, re-raise
                        raise
                    continue
            
            # Handle API errors
            if response is None or response.status_code != 200:
                error_msg = response.text if response else last_error
                
                if response and response.status_code == 503:
                    raise RuntimeError(
                        f"Hugging Face API model is loading. Please wait a moment and try again. "
                        f"Error: {error_msg}"
                    )
                elif response and response.status_code == 401:
                    raise ValueError(
                        f"Invalid Hugging Face API key. Please check your HUGGINGFACE_API_KEY. "
                        f"Get your key from https://huggingface.co/settings/tokens"
                    )
                elif response and response.status_code == 403:
                    raise ValueError(
                        f"Hugging Face API token lacks Inference API permissions. "
                        f"Please create a new token with 'read' permissions at https://huggingface.co/settings/tokens. "
                        f"Error: {error_msg}"
                    )
                else:
                    raise RuntimeError(
                        f"Hugging Face API error (status {response.status_code if response else 'unknown'}): {error_msg}"
                    )
            
            result = response.json()
            
            # Handle response format (could be list of lists or nested structure)
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], list):
                    # Direct list of embeddings
                    batch_embeddings = np.array(result)
                else:
                    # Might be wrapped in another structure
                    batch_embeddings = np.array([item if isinstance(item, list) else [item] for item in result])
            else:
                raise ValueError(f"Unexpected response format from Hugging Face API: {type(result)}")
            
            all_embeddings.append(batch_embeddings)
            
            # Progress indicator for large batches
            if len(texts) > batch_size:
                print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} texts...")
    
    # Concatenate all batches
    embeddings = np.vstack(all_embeddings)
    
    # Normalize embeddings if requested (for cosine similarity)
    if normalize:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        embeddings = embeddings / norms
    
    return embeddings

