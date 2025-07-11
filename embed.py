# Requires transformers>=4.51.0
# Requires sentence-transformers>=2.7.0
import torch
from sentence_transformers import SentenceTransformer
from transformers.utils.quantization_config import BitsAndBytesConfig

# empty the cache
torch.cuda.empty_cache()

# Set the memory fraction to 40% of the total GPU memory.
# Adjust the 0.4 value as needed for your model and hardware.
# torch.cuda.set_per_process_memory_fraction(0.7, 0)

# Load the model
#
# model = SentenceTransformer("Qwen/Qwen3-Embedding-4B")

# quantization_config = BitsAndBytesConfig(
#    load_in_4bit=True,
#    bnb_4bit_quant_type="nf4",  # Normal Float 4-bit
#    bnb_4bit_compute_dtype=torch.float16,  # Compute in fp16
#    bnb_4bit_use_double_quant=True,  # Double quantization for extra savings
# )
# We recommend enabling flash_attention_2 for better acceleration and memory saving,
# together with setting `padding_side` to "left":
model = SentenceTransformer(
    "Qwen/Qwen3-Embedding-8B-GGUF",
    model_kwargs={
        "file_name": "qwen3-embedding-8b-Q4_K_M",
        #        "quantization_config": quantization_config,
        "attn_implementation": "flash_attention_2",
        "device_map": "auto",
        "torch_dtype": torch.float16,
        "low_cpu_mem_usage": True,
    },
    tokenizer_kwargs={"padding_side": "left"},
    device=None,
)

# The queries and documents to embed
queries = [
    "What is the capital of China?",
    "Explain gravity",
]
documents = [
    "The capital of China is Beijing.",
    "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
]

# Encode the queries and documents. Note that queries benefit from using a prompt
# Here we use the prompt called "query" stored under `model.prompts`, but you can
# also pass your own prompt via the `prompt` argument
query_embeddings = model.encode(queries, prompt_name="query")
document_embeddings = model.encode(documents)

# Compute the (cosine) similarity between the query and document embeddings
similarity = model.similarity(query_embeddings, document_embeddings)
print(document_embeddings.shape)
print(similarity)
# tensor([[0.7493, 0.0751],
#         [0.0880, 0.6318]])
