"""
Centaurus Embedding Service.
Handles dense vector embedding generation using local FastEmbed or OpenAI fallbacks.
"""
from typing import List
from backend.config import settings

_MODEL = None

def get_embedding_model():
    """
    Lazy loads the local FastEmbed text embedding model.
    """
    global _MODEL
    if _MODEL is None:
        if settings.is_mock_mode:
            return "mock"
        try:
            from fastembed import TextEmbedding
            # Default model is 'BAAI/bge-small-en-v1.5' (384 dimensions)
            # Extremely fast and lightweight CPU-only local model.
            _MODEL = TextEmbedding()
        except Exception as e:
            print(f"Warning: could not import fastembed: {e}. Falling back to OpenAI API.")
            _MODEL = "openai"
    return _MODEL

def get_embedding_dim() -> int:
    """
    Returns the vector dimension of the active embedding provider.
    """
    if settings.is_mock_mode:
        return 384
        
    model = get_embedding_model()
    if model == "openai":
        return 1536
    elif model == "mock":
        return 384
    else:
        # FastEmbed bge-small-en-v1.5 is 384-dimensional
        return 384

def get_embedding(text: str) -> List[float]:
    """
    Generates a dense vector embedding for the input text.
    """
    # 1. Mock Mode
    if settings.is_mock_mode:
        # Generate a deterministic mock vector based on string hash
        import random
        random.seed(hash(text))
        return [random.uniform(-0.2, 0.2) for _ in range(384)]

    # 2. Get active provider
    model = get_embedding_model()

    if model == "openai":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]
            )
            return response.data[0].embedding
        except Exception as exc:
            print(f"Error calling OpenAI Embeddings: {exc}. Falling back to mock values.")
            import random
            random.seed(hash(text))
            return [random.uniform(-0.2, 0.2) for _ in range(1536)]
    elif model == "mock":
        import random
        random.seed(hash(text))
        return [random.uniform(-0.2, 0.2) for _ in range(384)]
    else:
        # Run local FastEmbed inference
        embeddings_generator = model.embed([text])
        embedding_list = list(embeddings_generator)[0]
        return embedding_list.tolist()
