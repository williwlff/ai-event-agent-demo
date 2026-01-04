from typing import List
from qdrant_client import QdrantClient


def qdrant_search(
    client: QdrantClient | None,
    collection: str,
    query: str,
    limit: int = 3
) -> List[str]:
    """
    RAG disabilitato per ambienti senza Qdrant (es. Render demo)
    """
    return []
