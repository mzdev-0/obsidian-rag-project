

import json
import re
from litellm import completion
from datetime import datetime

# The prompt template from the technical specification
QUERY_PLANNER_PROMPT = """
You are a query analysis engine for a personal knowledge management system. Your task is to deconstruct a user's question into a structured JSON object.

# Today's Date: {today_date}

# Available Filters
You can build filters using the following fields with ChromaDB operators ('$gt', '$lt', '$in', etc.):
- "created_date", "modified_date" (ISO 8601 datetime string)
- "tags", "wikilinks" (string, use '$in' for list matching)
- "file_path", "heading", "title" (string)
- "level" (integer, heading level from 1-6)

# Response Formats
Choose the most appropriate response format based on the user's query.
- "metadata_only": The default, efficient choice. Use for broad queries ("find notes about...") or when the user wants a list. This provides a set of pointers (ID, Title, Heading, Tags) for the chat LLM to decide if it needs more info.
- "selective_context": The high-precision choice. Use for specific, factual questions ("what did I write about..."). This returns the actual text content of the most relevant sections.

# User Query
"{user_query}"

# Your JSON Output
"""

def deconstruct_query(user_query: str, llm_client=None, max_retries=3) -> dict:
    """
    Generates a JSON query plan by deconstructing a user query with an LLM.

    Args:
        user_query: The raw string input from the user.
        llm_client: An instantiated client for an LLM (e.g., from LiteLLM).
        max_retries: The number of times to retry if the LLM output is not valid JSON.

    Returns:
        A Python dictionary matching the query plan structure.
    
    Raises:
        ValueError: If the LLM fails to produce valid JSON after max_retries.
    """
    # Default to LiteLLM's completion if no client is provided
    if llm_client is None:
        llm_client = completion

    today_date_str = datetime.now().strftime("%Y-%m-%d")
    prompt = QUERY_PLANNER_PROMPT.format(
        today_date=today_date_str,
        user_query=user_query
    )

    for attempt in range(max_retries):
        try:
            response = llm_client(
                model="qwen3:8b-instruct-q4_K_M",
                messages=[{"content": prompt, "role": "user"}],
                temperature=0.0,
            )
            
            # Extract the JSON part of the response
            json_str = response.choices[0].message.content
            # A common failure mode is the LLM wrapping the JSON in ```json ... ```
            match = re.search(r'```json\n({.*?})\n```', json_str, re.DOTALL)
            if match:
                json_str = match.group(1)

            plan = json.loads(json_str)
            return plan
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Attempt {attempt + 1} failed: Could not parse LLM output. Error: {e}")
            if attempt + 1 == max_retries:
                raise ValueError("LLM failed to produce valid JSON after multiple attempts.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            if attempt + 1 == max_retries:
                 raise ValueError("An unexpected error occurred while communicating with the LLM.")

    # This part should be unreachable if the loop works as expected
    return {"semantic_query": user_query, "filters": [], "response_format": "metadata_only"}

