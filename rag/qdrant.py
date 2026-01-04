from typing import List
from qdrant_client import QdrantClient
from utils.embeddings import fake_embedding


def qdrant_search(
    client: QdrantClient,
    collection: str,
    query: str,
    limit: int = 3
) -> List[str]:
    vector = fake_embedding(query)

    hits = client.search(
        collection_name=collection,
        query_vector=vector,
        limit=limit
    )

    return [
        h.payload["text"]
        for h in hits
        if h.payload and "text" in h.payload
    ]
