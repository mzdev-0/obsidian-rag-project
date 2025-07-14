import json
import re
import os
import time
import logging
from datetime import datetime
from openai import OpenAI

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
DEFAULT_MODEL = "qwen3:8b"

# --- OpenAI Client Initialization ---
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("The OPENROUTER_API_KEY environment variable is not set.")

client = OpenAI(
    base_url="http://10.10.110.101:11434/v1",
    api_key=api_key,
)

# --- Prompt & Schema ---
QUERY_PLANNER_PROMPT = """
You are a meticulous and intelligent query planner for a personal knowledge management system. Your purpose is to convert a user's natural language question into a precise, structured JSON object that can be executed against a ChromaDB vector store.

Your sole output **MUST** be a single, raw JSON object conforming to the provided schema. Do not include any other text, explanations, or markdown formatting.

**# Current Date**
- Today's Date: {today_date}

**# Core Task**
Deconstruct the user's query into two main components:
1.  **`semantic_query`**: A rephrased version of the query, optimized for semantic vector search. Focus on the core *concepts* of the query.
2.  **`filters`**: A list of metadata filters to be applied as a `where` clause in ChromaDB.

**# Available Filter Fields**
- `created_date`, `modified_date`: ISO 8601 datetime string (e.g., "2024-07-13T12:00:00"). Use with `$gte` (greater than or equal) and `$lte` (less than or equal).
- `tags`, `wikilinks`: String lists. Use the `$in` operator for matching one or more items.
- `file_path`, `heading`, `title`: String. Use `$eq` for exact matches.
- `level`: Integer (1-6). Use `$eq`, `$lte`, etc. to filter by heading depth.

**# Response Format**
Based on the user's intent, decide on the appropriate response format:
- **`metadata_only`**: Use for broad, exploratory queries (e.g., "find notes about...", "list my projects..."). This returns pointers to the information.
- **`selective_context`**: Use for specific, factual questions where the answer is likely contained in the text (e.g., "what did I write about...", "summarize my notes on..."). This returns the actual content.

**# Examples**

1.  **User Query**: "Recent RAG notes that mention ChromaDB but aren't tagged as draft"
    **Your Reasoning (Internal Monologue)**:
    - The user wants notes from recently. "Recent" implies a time filter, maybe the last month.
    - Core concept is "RAG and ChromaDB". This is the semantic query.
    - Two explicit filters: "mention ChromaDB" (can be semantic, but also good for semantic query) and "aren't tagged as draft". The 'draft' tag needs to be excluded. Wait, ChromaDB doesn't have a `$nin` (not in) for lists. I'll have to omit this filter and let the parent LLM handle it, but I will capture everything else.
    - This is a specific request, so `selective_context` is best.
    **Your JSON Output**:
    ```json
    {{
      "semantic_query": "Notes about Retrieval-Augmented Generation that reference the ChromaDB vector store",
      "filters": [
        {{
          "field": "created_date",
          "operator": "$gte",
          "value": "2024-06-13T00:00:00"
        }}
      ],
      "response_format": "selective_context"
    }}
    ```

2.  **User Query**: "Give me a list of recon TTPs from my notes."
    **Your Reasoning (Internal Monologue)**:
    - The user wants a "list". This signals a `metadata_only` response.
    - The core concept is "reconnaissance TTPs" (Tactics, Techniques, and Procedures). This is a strong semantic query.
    - There are no explicit metadata filters mentioned.
    **Your JSON Output**:
    ```json
    {{
      "semantic_query": "Tactics, Techniques, and Procedures (TTPs) for reconnaissance in cybersecurity.",
      "filters": [],
      "response_format": "metadata_only"
    }}
    ```

**# User Query to Process**
"{user_query}"

**# Your JSON Output**
"""

# The schema is now a dictionary, NOT a list containing a dictionary.
SCHEMA_OBJECT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Query Plan",
    "description": "A structured query plan deconstructed from a user's natural language query.",
    "type": "object",
    "properties": {
        "semantic_query": {
            "description": "The user's query, rephrased for optimal semantic search performance.",
            "type": "string",
        },
        "filters": {
            "description": "A list of structured filters to apply to the search, based on metadata extracted from the query.",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {
                        "description": "The database field to apply the filter on.",
                        "type": "string",
                        "enum": [
                            "created_date",
                            "modified_date",
                            "tags",
                            "wikilinks",
                            "file_path",
                            "heading",
                            "title",
                            "level",
                        ],
                    },
                    "operator": {
                        "description": "The operator to use for the filter, following ChromaDB syntax.",
                        "type": "string",
                        "enum": ["$gt", "$lt", "$gte", "$lte", "$eq", "$ne", "$in"],
                    },
                    "value": {
                        "description": "The value to filter against. Can be a string, integer, or a list of strings for the '$in' operator.",
                        "oneOf": [
                            {"type": "string"},
                            {"type": "integer"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                    },
                },
                "required": ["field", "operator", "value"],
            },
        },
        "response_format": {
            "description": "The desired format for the response, dictating whether to return full content or just metadata.",
            "type": "string",
            "enum": ["metadata_only", "selective_context"],
        },
    },
    "required": ["semantic_query", "filters", "response_format"],
}


def deconstruct_query(
    user_query: str, model: str = DEFAULT_MODEL, max_retries: int = 3
) -> dict:
    """
    Generates a JSON query plan by deconstructing a user query with an LLM API.
    """
    today_date_str = datetime.now().strftime("%Y-%m-%d")
    prompt = QUERY_PLANNER_PROMPT.format(
        today_date=today_date_str, user_query=user_query
    )

    for attempt in range(max_retries):
        try:
            logging.info(
                f"Attempt {attempt + 1} of {max_retries} to deconstruct query for: '{user_query[:50]}...'"
            )

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "query_plan", "schema": SCHEMA_OBJECT},
                },
            )

            content_str = response.choices[0].message.content
            plan = json.loads(content_str)  # pyright: ignore

            # Basic validation can be removed if you trust the schema, but can be a good safety net.
            logging.info("Successfully deconstructed query using JSON Schema.")
            print("**** PLAN IN JSON ****")
            print(plan)
            print("**** END PRINT PLAN ****")
            return plan

        except json.JSONDecodeError as e:
            logging.error(
                f"JSON decoding failed on attempt {attempt + 1}: {e}\nRaw content: {content_str}"  # pyright: ignore
            )
        except Exception as e:
            logging.error(
                f"An API call or unexpected error occurred on attempt {attempt + 1}: {e}"
            )

        if attempt < max_retries - 1:
            wait_time = 2 ** (attempt + 1)
            logging.info(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)

    raise RuntimeError(f"Failed to get a valid response after {max_retries} attempts.")
