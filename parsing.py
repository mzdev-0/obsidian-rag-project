import re
from typing import List
from dataclasses import dataclass, field
from typing import List, Optional


Vector = List[float]


@dataclass
class ContentSection:
    """Represents a structured section of content from a note."""

    id: str
    heading: str
    content: str
    level: int  # e.g., 1 for #, 2 for ##
    embedding: Optional[Vector] = None


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


def parse_headings(text: str) -> List[ContentSection]:
    """
    Parses markdown content into structured sections based on headings,
    ignoring all content before the first heading.
    """
    sections = []
    lines = text.split("\n")
    section_id_counter = 0
    in_content = False

    current_heading = ""
    current_level = 0
    current_content = []

    for line in lines:
        heading_match = re.match(r"^(#+)\s+(.*)", line)
        if heading_match:
            if in_content and "".join(current_content).strip():
                # Save the previous section
                sections.append(
                    ContentSection(
                        id=f"{section_id_counter}",
                        heading=current_heading.strip(),
                        content="\n".join(current_content).strip(),
                        level=current_level,
                    )
                )
                section_id_counter += 1

            # Start a new section
            in_content = True
            current_level = len(heading_match.group(1))
            current_heading = heading_match.group(2)
            current_content = []
        elif in_content:
            current_content.append(line)

    # Add the last section
    if in_content and (current_heading or "".join(current_content).strip()):
        sections.append(
            ContentSection(
                id=f"{section_id_counter}",
                heading=current_heading.strip(),
                content="\n".join(current_content).strip(),
                level=current_level,
            )
        )

    if not sections:
        print("Error: No headings found in the provided text.")

    return sections


def extract_images(content):
    pass
