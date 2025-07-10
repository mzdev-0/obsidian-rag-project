

import os
import re
import json
import sys
from collections import defaultdict

def is_markdown_file(file_path):
    """Checks if a file is a Markdown file."""
    return file_path.endswith(".md")

def extract_wikilinks(text):
    """
    Extracts all wikilinks from a string, handling aliases and ignoring .png files.
    """
    raw_links = re.findall(r"\[\[(.*?)\]\]", text)
    processed_links = []
    for link in raw_links:
        # Take the part before the '|' to handle aliased links
        actual_link = link.split('|')[0].strip()
        # Ignore links that are image files
        if not actual_link.endswith('.png'):
            processed_links.append(actual_link)
    return processed_links

def count_wikilinks_in_directory(directory):
    """
    Recursively finds all Markdown files in a directory,
    extracts all wikilinks, and counts their occurrences.
    """
    wikilink_counts = defaultdict(int)
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if is_markdown_file(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        wikilinks = extract_wikilinks(content)
                        for link in wikilinks:
                            wikilink_counts[link] += 1
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}", file=sys.stderr)
    return dict(wikilink_counts)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(__file__)} <directory>")
        sys.exit(1)
    target_directory = sys.argv[1]
    if not os.path.isdir(target_directory):
        print(f"Error: Directory not found at '{target_directory}'")
        sys.exit(1)
    
    wikilink_counts = count_wikilinks_in_directory(target_directory)
    
    # Sort the dictionary by value (the count) in descending order
    sorted_wikilinks = dict(sorted(wikilink_counts.items(), key=lambda item: item[1], reverse=True))
    
    # Print the result as a JSON string
    print(json.dumps(sorted_wikilinks, indent=4))

