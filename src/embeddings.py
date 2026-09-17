from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_embedding_model():
    return SentenceTransformer(MODEL_NAME)


def embed_chunks(chunks, model):
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    return embeddings