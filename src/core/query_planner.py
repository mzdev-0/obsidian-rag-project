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
# It's good practice to handle the case where the API key might not be set.
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("The OPENROUTER_API_KEY environment variable is not set.")

client = OpenAI(
    base_url="http://10.10.110.101:11434/v1",
    api_key=api_key,
)

# --- Prompt & Schema ---
QUERY_PLANNER_PROMPT = """
You are a meticulous and intelligent query planner for a personal knowledge management system. Your purpose is to convert a user's natural language question into a precise, structured JSON object that can be executed against a Qdrant vector store.

Your sole output **MUST** be a single, raw JSON object conforming to the provided schema. Do not include any other text, explanations, or markdown formatting.

**# Current Date**
- Today's Date: {today_date}

**# Core Task**
Deconstruct the user's query into three main components:
1.  **`semantic_search_needed`**: A boolean (`true` or `false`) indicating if the query requires a vector search or can be satisfied by a metadata-only lookup.
2.  **`semantic_query`**: A rephrased version of the query, optimized for semantic vector search. This can be an empty string if `semantic_search_needed` is `false`.
3.  **`filters`**: A list of metadata filters to be applied as a Qdrant Filter object.

**# Semantic vs. Metadata Search**
You must decide if the user's query requires understanding the *meaning* of the text, or if it's just asking for items that match specific, exact metadata.

- Set `semantic_search_needed: true` if the query involves concepts, topics, or summarization (e.g., "notes about X", "what did I say about Y"). The `semantic_query` should be rich and descriptive.
- Set `semantic_search_needed: false` if the query can be answered *entirely* with the available filter fields (e.g., "all notes with tag 'project-alpha'", "files from last week"). The `semantic_query` can be left as an empty string `""`.

**# Available Filter Fields**
- `created_date`, `modified_date`: Unix timestamps (integers). Use with `gte` (greater than or equal) and `lte` (less than or equal).
- `tags`, `wikilinks`: String arrays. Use `match` for exact array matches or `contains` for partial matches.
- `file_path`, `heading`, `title`: String. Use `eq` for exact matches or `like` for partial matches.
- `level`: Integer (1-6). Use `eq`, `lte`, etc. to filter by heading depth.

**# Response Format**
Based on the user's intent, decide on the appropriate response format:
- **`metadata_only`**: Use for broad, exploratory queries (e.g., "find notes about...", "list my projects..."). This returns pointers to the information.
- **`selective_context`**: Use for specific, factual questions where the answer is likely contained in the text (e.g., "what did I write about...", "summarize my notes on..."). This returns the actual content.

**# Examples**

1.  **User Query**: "Recent RAG notes that mention ChromaDB"
    **Your Reasoning (Internal Monologue)**:
    - The user wants notes from recently. "Recent" implies a time filter.
    - The core concept is "RAG and ChromaDB". This is a strong conceptual search.
    - Because it's a conceptual search, `semantic_search_needed` must be `true`.
    - This is a specific request, so `selective_context` is best.
    **Your JSON Output**:
    ```json
    {{
      "semantic_search_needed": true,
      "semantic_query": "Notes about Retrieval-Augmented Generation that reference the ChromaDB vector store",
      "filters": [
        {{
          "field": "created_date",
          "operator": "gte",
          "value": 1720924800
        }}
      ],
      "response_format": "selective_context"
    }}
    ```

2.  **User Query**: "Show me all files tagged 'project-hydra' that are level 2 headings."
    **Your Reasoning (Internal Monologue)**:
    - The user is asking for a list based on very specific metadata. "tag is 'project-hydra'" and "level 2 headings" are both exact filters.
    - There is no conceptual or "aboutness" search here. This is a perfect case for a metadata-only lookup.
    - Therefore, `semantic_search_needed` is `false`, and the `semantic_query` can be empty.
    - The user wants a list of files, so `metadata_only` is the right response format.
    **Your JSON Output**:
    ```json
    {{
      "semantic_search_needed": false,
      "semantic_query": "",
      "filters": [
        {{
          "field": "tags",
          "operator": "contains",
          "value": "project-hydra"
        }},
        {{
          "field": "level",
          "operator": "eq",
          "value": 2
        }}
      ],
      "response_format": "metadata_only"
    }}
    ```

**# User Query to Process**
"{user_query}"

**# Your JSON Output**
"""

# Updated schema for Qdrant-native filtering
SCHEMA_OBJECT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Query Plan",
    "description": "A structured query plan deconstructed from a user's natural language query for Qdrant.",
    "type": "object",
    "properties": {
        "semantic_search_needed": {
            "description": "Determines if the query requires a semantic vector search or can be fulfilled with a metadata-only lookup.",
            "type": "boolean",
        },
        "semantic_query": {
            "description": "The user's query, rephrased for optimal semantic search. Must be empty string if semantic_search_needed is false.",
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
                        "description": "The operator to use for the filter, following Qdrant syntax.",
                        "type": "string",
                        "enum": [
                            "gt",
                            "gte",
                            "lt",
                            "lte",
                            "eq",
                            "ne",
                            "match",
                            "contains",
                            "like",
                        ],
                    },
                    "value": {
                        "description": "The value to filter against. Can be string, int, or array.",
                        "anyOf": [
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
            "description": "The desired format for the response.",
            "type": "string",
            "enum": ["metadata_only", "selective_context"],
        },
    },
    "required": [
        "semantic_search_needed",
        "semantic_query",
        "filters",
        "response_format",
    ],
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
    if not user_query.strip():
        logging.warning("User query is empty. Skipping")
        return

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

            logging.info("Successfully deconstructed query using JSON Schema.")
            return plan

        except json.JSONDecodeError as e:
            logging.error(
                f"JSON decoding failed on attempt {attempt + 1}: {e}\nRaw content: {content_str}"  # pyright: ignore
            )
            logging.info("Attempting manual JSON parsing fallback...")
            try:
                plan = _manual_json_parse(content_str)
                if plan:
                    return plan
            except Exception:  # noqa: BLE001
                logging.warning("Manual JSON parsing also failed.")
        except Exception as e:
            logging.error(
                f"An API call or unexpected error occurred on attempt {attempt + 1}: {e}"
            )

        if attempt < max_retries - 1:
            wait_time = 2 ** (attempt + 1)
            logging.info(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)

    raise RuntimeError(f"Failed to get a valid response after {max_retries} attempts.")


def _manual_json_parse(content: str) -> dict:
    """
    Fallback function to manually extract JSON from the LLM response
    when structured JSON schema parsing fails.
    """
    import re

    # Try to find JSON object in the content
    json_pattern = r'\{[^{}]*"semantic_search_needed"[^{}]*\}'
    match = re.search(json_pattern, content.strip())

    if not match:
        # Try broader JSON object pattern
        json_pattern = r'\{[^{}]*"semantic_query"[^{}]*\}'
        match = re.search(json_pattern, content.strip())

    if not match:
        # Try even broader JSON object pattern
        json_pattern = r"\{[^{}]*\}"
        matches = re.findall(json_pattern, content.strip())

        # Look for a candidate with required fields
        for json_str in matches:
            try:
                parsed = json.loads(json_str)
                if all(
                    key in parsed
                    for key in ["semantic_search_needed", "filters", "response_format"]
                ):
                    # Ensure semantic_query is present (can be empty string)
                    if "semantic_query" not in parsed:
                        parsed["semantic_query"] = ""
                    return parsed
            except json.JSONDecodeError:
                continue

    if match:
        try:
            parsed = json.loads(match.group())
            # Ensure all required fields are present
            if all(
                key in parsed
                for key in ["semantic_search_needed", "filters", "response_format"]
            ):
                if "semantic_query" not in parsed:
                    parsed["semantic_query"] = ""
                return parsed
        except json.JSONDecodeError:
            pass

    # Return a default fallback plan
    logging.warning("Using default fallback query plan")
    return {
        "semantic_search_needed": True,
        "semantic_query": content.strip(),
        "filters": [],
        "response_format": "selective_context",
    }
