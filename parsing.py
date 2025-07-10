import re


def extract_wikilinks(text):
    """
    Extracts all wikilinks from a string, handling aliases and ignoring .png files.
    """
    raw_links = re.findall(r"\[\[(.*?)\]\]", text)
    processed_links = []
    for link in raw_links:
        # Take the part before the '|' to handle aliased links
        actual_link = link.split("|")[0].strip()
        # Ignore links that are image files
        if not actual_link.endswith(".png"):
            processed_links.append(actual_link)
    return processed_links
