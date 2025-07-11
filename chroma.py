import chromadb
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions import ChromaLangchainEmbeddingFunction
from langchain_community.embeddings import LlamaCppEmbeddings

MODEL_PATH = (
    "./models/Qwen3-Embedding-8B-Q4_K_M.gguf"  # <-- IMPORTANT: Update this path
)

# --- Model Loading ---
# Initialize the LlamaCppEmbeddings model
# This gives you fine-grained control over the model's parameters.
# n_gpu_layers: Offload layers to GPU. -1 means all possible layers. Adjust if you have a GPU.
# n_batch: Number of tokens to process in parallel. Adjust based on your hardware.
# n_ctx: The context size for the model.
# verbose: Set to True for detailed logging.
llama_embedder = LlamaCppEmbeddings(  # pyright: ignore[reportCallIssue]
    model_path=MODEL_PATH,
    n_gpu_layers=-1,
    n_batch=512,
    n_ctx=40960,
    verbose=False,
)

# Have to create a client
chroma_client = chromadb.PersistentClient(path="./chromadb")

# collections are like tables sorta. Collections are grouped into databases. So one ID, embed vector, metadata, and source document (heading) is a collection.
collection = chroma_client.get_or_create_collection(
    name="my_collection",
    embedding_function=ChromaLangchainEmbeddingFunction(llama_embedder),
)

# add to a collection
collection.add(
    ids=["id1", "id2"],
    documents=[
        "Test document",
        "Test document 2",
    ],
)
