import numpy as np
from typing import List

EMBEDDING_SIZE = 768

def fake_embedding(text: str) -> List[float]:
    """
    Embedding finto ma deterministico.
    Utile per sviluppo senza dipendenze pesanti.
    """
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    return rng.random(EMBEDDING_SIZE).tolist()
