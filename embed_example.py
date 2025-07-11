from typing import List
from langchain.embeddings.base import Embeddings
from llama_cpp import Llama

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LlamaCppEmbeddings(Embeddings):
    """
    LangChain embeddings integration for llama-cpp-python.
    """

    def __init__(self, model_path: str, **kwargs):
        """
        Initialize the LlamaCppEmbeddings class.

        Args:
            model_path (str): The path to the GGUF model file.
            **kwargs: Additional keyword arguments to pass to the Llama constructor.
        """
        try:
            self.model = Llama(model_path=model_path, embedding=True, **kwargs)
        except Exception as e:
            logger.error(f"Error initializing Llama model: {e}")
            logger.error(
                "Please ensure that the model path is correct and that llama-cpp-python is installed correctly."
            )
            raise

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts.

        Args:
            texts (List[str]): A list of texts to embed.

        Returns:
            List[List[float]]: A list of embeddings for the given texts.
        """
        if not texts:
            return []

        result = self.model.create_embedding(texts)

        if "data" not in result or not isinstance(result["data"], list):
            logger.error(f"Unexpected output format from create_embedding: {result}")
            return []

        embeddings = []
        for item in result["data"]:
            if "embedding" in item and isinstance(item["embedding"], list):
                embeddings.append(item["embedding"])
            else:
                logger.warning(f"Skipping item with unexpected format: {item}")

        return embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts (List[str]): A list of documents to embed.

        Returns:
            List[List[float]]: A list of embeddings for the given documents.
        """
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text (str): The query to embed.

        Returns:
            List[float]: The embedding for the given query.
        """
        return self._embed([text])[0]


if __name__ == "__main__":
    # --- Example Usage ---

    # 1. Specify the path to your GGUF embedding model.
    #    Make sure this model is in the same directory as the script,
    #    or provide the full path to the model.
    model_path = "./models/Qwen3-Embedding-8B-Q4_K_M.gguf"

    # 2. (Optional) Specify additional parameters for the Llama model.
    #    For example, you can enable GPU acceleration if you have a compatible GPU
    #    and have installed llama-cpp-python with the appropriate backend (e.g., CUDA).
    #
    #    Example for GPU acceleration (uncomment if needed):
    #    kwargs = {
    #        "n_gpu_layers": -1,  # Offload all layers to GPU
    #        "n_ctx": 2048,       # Set context size
    #    }
    #
    #    For CPU-only usage, you can leave kwargs empty.
    kwargs = {}

    try:
        # 3. Initialize the LlamaCppEmbeddings class.
        print(f"Loading model from: {model_path}")
        embeddings = LlamaCppEmbeddings(model_path=model_path, **kwargs)
        print("Model loaded successfully.")

        # 4. Embed a sample query.
        query_text = "What is the capital of France?"
        print(f"\nEmbedding query: '{query_text}'")
        query_embedding = embeddings.embed_query(query_text)

        # Print the first few dimensions of the embedding as a sample.
        print(f"Embedding dimensions: {len(query_embedding)}")
        print(f"First 5 dimensions: {query_embedding[:5]}")

        # 5. Embed a list of documents.
        documents_to_embed = [
            "Paris is the capital and most populous city of France.",
            "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris.",
            "The Louvre Museum is the world's largest art museum and a historic monument in Paris.",
        ]
        print("\nEmbedding documents:")
        for doc in documents_to_embed:
            print(f"- '{doc}'")

        document_embeddings = embeddings.embed_documents(documents_to_embed)

        print(f"\nGenerated {len(document_embeddings)} document embeddings.")
        for i, doc_embedding in enumerate(document_embeddings):
            print(f"  - Document {i + 1} embedding dimensions: {len(doc_embedding)}")
            print(f"    First 5 dimensions: {doc_embedding[:5]}")

    except Exception as e:
        print(f"\nAn error occurred during the example usage: {e}")
        print("Please check the model path and ensure all dependencies are installed.")
