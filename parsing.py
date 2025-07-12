import re
from typing import List
from dataclasses import dataclass, field
from typing import List, Optional, Union
from datetime import datetime


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
    Parses markdown content into structured sections using a multi-pass approach.
    Each pass targets a specific heading level (1-6) and creates sections that
    end when encountering a heading of the same or higher level.

    Special handling for code-titled sections: headings followed by code blocks
    create sections that end when the code block closes.
    """
    sections = []
    lines = text.split("\n")
    section_id_counter = 0

    # Parse each heading level from 1 to 6
    for target_level in range(1, 7):
        target_pattern = re.compile(f"^{'#' * target_level}\\s+(.*)")

        i = 0
        while i < len(lines):
            line = lines[i]
            heading_match = target_pattern.match(line)

            if heading_match:
                heading_text = heading_match.group(1)

                # Check if this heading is followed by a code block
                is_code_titled = is_heading_followed_by_code(lines, i)

                # Collect content for this section
                section_content = []
                section_start = i
                i += 1  # Move past the heading line

                if is_code_titled:
                    # For code-titled sections, end when code block closes
                    in_code_block = False

                    while i < len(lines):
                        current_line = lines[i]
                        section_content.append(current_line)

                        if current_line.strip().startswith("```"):
                            in_code_block = not in_code_block
                            if not in_code_block:  # Code block just closed
                                i += 1
                                break
                        i += 1
                else:
                    # For regular sections, end when we hit same or higher level heading
                    while i < len(lines):
                        current_line = lines[i]

                        # Check if this line is a heading
                        heading_check = re.match(r"^(#+)\\s+", current_line)
                        if heading_check:
                            current_level = len(heading_check.group(1))
                            if current_level <= target_level:
                                # Found same or higher level heading, end section
                                break

                        section_content.append(current_line)
                        i += 1

                # Create the section
                sections.append(
                    ContentSection(
                        id=f"{section_id_counter}",
                        heading=heading_text.strip(),
                        content="\n".join(section_content).strip(),
                        level=target_level,
                    )
                )
                section_id_counter += 1
            else:
                i += 1

    if not sections:
        # If no headings are found, treat the entire text as a single section.
        sections.append(
            ContentSection(
                id="0",
                heading="<No Heading>",
                content=text.strip(),
                level=0,
            )
        )

    return sections


def is_heading_followed_by_code(lines: List[str], heading_index: int) -> bool:
    """
    Helper function to check if a heading is immediately followed by a code block.
    This helps identify headings that are likely titles for code snippets.
    """
    if heading_index + 1 >= len(lines):
        return False

    # Check the next non-empty line
    for i in range(heading_index + 1, len(lines)):
        line = lines[i].strip()
        if line:  # Found first non-empty line
            return line.startswith("```")

    return False


def parse_datetime(text: str) -> Optional[datetime]:
    """
    Parses the date and time from the first two lines of the note content.
    Returns None if the content doesn't follow the expected format.
    """
    lines = text.strip().split("\n")

    if len(lines) >= 2:
        date_str = lines[0].strip()
        time_str = lines[1].strip()

        date_pattern = r"^\d{1,2}-\d{1,2}-\d{4}$"  # MM-DD-YYYY or M-D-YYYY
        time_pattern = r"^\d{1,2}:\d{2} (AM|PM)$"  # HH:MM AM/PM or H:MM AM/PM

        if re.match(date_pattern, date_str) and re.match(time_pattern, time_str):
            try:
                return datetime.strptime(f"{date_str} {time_str}", "%m-%d-%Y %H:%M %p")
            except ValueError:
                pass

    return None


def parse_references(text: str) -> List[str]:
    """
    Parses reference URLs from the 'Reference:' line until the 'Tags:' line.
    """
    references = []
    in_references = False
    for line in text.split("\n"):
        if line.lower().startswith("reference:"):
            in_references = True
            line_content = line[len("Reference:") :].strip()
            if line_content:
                references.extend(re.split(r",\s*", line_content))
        elif in_references:
            if line.lower().startswith("tags:"):
                break
            line_content = line.strip()
            if line_content:
                references.extend(re.split(r",\s*", line_content))

    return [ref for ref in references if ref]


def parse_tags(text: str) -> List[str]:
    """
    Parses tags from the 'Tags:' line.
    """
    for line in text.split("\n"):
        if line.lower().startswith("tags:"):
            # Find all wikilinks in the tags line
            return extract_wikilinks(line)
    return []


def parse_body(raw_content: str) -> str:
    """
    Parses the main body of the note. The body is the content that appears
    after the 'Tags:' line and all associated tag declarations.
    """
    lines = raw_content.split("\n")

    try:
        tags_line_index = next(
            i for i, line in enumerate(lines) if line.lower().startswith("tags:")
        )

        # The body starts after the block of tags.
        # A block of tags is a contiguous set of non-empty lines after "Tags:".

        body_start_line = tags_line_index + 1

        # Move past any non-empty lines that are part of the tags block
        while body_start_line < len(lines) and lines[body_start_line].strip():
            body_start_line += 1

        # Move past any empty lines between tags and body
        while body_start_line < len(lines) and not lines[body_start_line].strip():
            body_start_line += 1

        if body_start_line < len(lines):
            return "\n".join(lines[body_start_line:]).strip()
        else:
            return ""

    except StopIteration:
        # If 'Tags:' is not found, consider the entire content as the body
        return raw_content.strip()
