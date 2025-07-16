import re
import logging
import time
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

Vector = List[float]

# Configure module-level logger
logger = logging.getLogger(__name__)


@dataclass
class ContentSection:
    """Represents a structured section of content from a note."""

    id: str
    heading: str
    content: str
    level: int  # e.g., 1 for #, 2 for ##
    embedding: Optional[Vector] = None

    def to_langchain_document(self, note_title: str, file_path: str, tags: List[str], 
                             wikilinks: List[str], created_date: datetime, 
                             modified_date: datetime):
        """Convert this section to a LangChain Document."""
        logger = logging.getLogger(__name__)
        
        from langchain.schema import Document
        from pathlib import Path
        
        content = f"{note_title} | {self.heading}\n\n{self.content}".strip()
        
        metadata = {
            "title": note_title,
            "file_path": str(file_path),
            "heading": self.heading,
            "level": self.level,
            "tags": ",".join(tags) if tags else "",
            "wikilinks": ",".join(wikilinks) if wikilinks else "",
            "created_date": created_date.isoformat(),
            "modified_date": modified_date.isoformat(),
        }
        
        doc_id = f"{Path(file_path).stem}::{self.id}"
        
        logger.debug(f"Created LangChain document: id={doc_id}, title='{note_title}', heading='{self.heading}', content_length={len(content)}")
        
        return Document(page_content=content, metadata=metadata)


def extract_wikilinks(text):
    """
    Extracts all wikilinks from a string, handling aliases and ignoring .png files.
    """
    logger = logging.getLogger(__name__)
    
    raw_links = re.findall(r"\[\[(.*?)\]\]", text)
    logger.debug(f"Found {len(raw_links)} raw wikilinks in text")
    
    processed_links = []
    for link in raw_links:
        # Take the part before the '|' to handle aliased links
        actual_link = link.split("|")[0].strip()
        # Ignore links that are image files
        if not actual_link.endswith(".png"):
            processed_links.append(actual_link)
            logger.debug(f"Processed wikilink: '{actual_link}' (original: '{link}')")
        else:
            logger.debug(f"Skipped .png wikilink: '{actual_link}'")
    
    logger.debug(f"Extracted {len(processed_links)} valid wikilinks from {len(raw_links)} total")
    return processed_links


def parse_headings(text: str) -> List[ContentSection]:
    """
    Parses markdown content into structured sections using a multi-pass approach.
    Each pass targets a specific heading level (1-6) and creates sections that
    end when encountering a heading of the same or higher level.

    Special handling for code-titled sections: headings followed by code blocks
    create sections that end when the code block closes.
    """
    start_time = time.time()
    sections = []
    lines = text.split("\n")
    section_id_counter = 0

    logger.debug(f"Starting heading parsing for text with {len(lines)} lines")

    # Parse each heading level from 1 to 6
    for target_level in range(1, 7):
        target_pattern = re.compile(f"^{'#' * target_level}\\s+(.*)")
        logger.debug(f"Processing heading level {target_level}")

        i = 0
        level_sections = 0
        while i < len(lines):
            line = lines[i]
            heading_match = target_pattern.match(line)

            if heading_match:
                heading_text = heading_match.group(1)
                logger.debug(f"Found heading level {target_level}: '{heading_text.strip()}' at line {i}")

                # Check if this heading is followed by a code block
                is_code_titled = is_heading_followed_by_code(lines, i)
                logger.debug(f"Heading '{heading_text.strip()}' is code-titled: {is_code_titled}")

                # Collect content for this section
                section_content = []
                section_start = i
                i += 1  # Move past the heading line

                if is_code_titled:
                    # For code-titled sections, end when code block closes
                    in_code_block = False
                    code_lines = 0

                    while i < len(lines):
                        current_line = lines[i]
                        section_content.append(current_line)

                        if current_line.strip().startswith("```"):
                            in_code_block = not in_code_block
                            if not in_code_block:  # Code block just closed
                                code_lines = len(section_content)
                                i += 1
                                break
                        i += 1
                    
                    logger.debug(f"Code-titled section collected {code_lines} lines")
                else:
                    # For regular sections, end when we hit same or higher level heading
                    content_lines = 0
                    while i < len(lines):
                        current_line = lines[i]

                        # Check if this line is a heading
                        heading_check = re.match(r"^(#+)\s+", current_line)
                        if heading_check:
                            current_level = len(heading_check.group(1))
                            if current_level <= target_level:
                                # Found same or higher level heading, end section
                                logger.debug(f"Ending section at line {i} due to level {current_level} heading")
                                break

                        section_content.append(current_line)
                        content_lines += 1
                        i += 1
                    
                    logger.debug(f"Regular section collected {content_lines} lines")

                # Create the section
                content = "\n".join(section_content).strip()
                sections.append(
                    ContentSection(
                        id=f"{section_id_counter}",
                        heading=heading_text.strip(),
                        content=content,
                        level=target_level,
                    )
                )
                logger.debug(f"Created section {section_id_counter}: '{heading_text.strip()}' ({len(content)} chars)")
                section_id_counter += 1
                level_sections += 1
            else:
                i += 1
        
        logger.debug(f"Level {target_level} processing complete: {level_sections} sections found")

    if not sections:
        # If no headings are found, treat the entire text as a single section.
        logger.info("No headings found, creating single section for entire text")
        sections.append(
            ContentSection(
                id="0",
                heading="<No Heading>",
                content=text.strip(),
                level=0,
            )
        )

    parse_time = time.time() - start_time
    logger.info(f"Heading parsing complete: {len(sections)} sections created in {parse_time:.3f}s")
    
    return sections


def is_heading_followed_by_code(lines: List[str], heading_index: int) -> bool:
    """
    Helper function to check if a heading is immediately followed by a code block.
    This helps identify headings that are likely titles for code snippets.
    """
    logger = logging.getLogger(__name__)
    
    if heading_index + 1 >= len(lines):
        logger.debug(f"Heading at index {heading_index} has no following lines")
        return False

    # Check the next non-empty line
    for i in range(heading_index + 1, len(lines)):
        line = lines[i].strip()
        if line:  # Found first non-empty line
            is_code = line.startswith("```")
            logger.debug(f"Heading followed by code block: {is_code} (line {i}: '{line[:50]}...')")
            return is_code

    logger.debug(f"No non-empty line found after heading at index {heading_index}")
    return False


def parse_datetime(text: str) -> Optional[datetime]:
    """
    Parses the date and time from the first two lines of the note content.
    Returns None if the content doesn't follow the expected format.
    """
    logger = logging.getLogger(__name__)
    
    lines = text.strip().split("\n")
    logger.debug(f"Parsing datetime from {len(lines)} lines")

    if len(lines) >= 2:
        date_str = lines[0].strip()
        time_str = lines[1].strip()

        logger.debug(f"Date string: '{date_str}', Time string: '{time_str}'")

        date_pattern = r"^\d{1,2}-\d{1,2}-\d{4}$"  # MM-DD-YYYY or M-D-YYYY
        time_pattern = r"^\d{1,2}:\d{2} (AM|PM)$"  # HH:MM AM/PM or H:MM AM/PM

        if re.match(date_pattern, date_str) and re.match(time_pattern, time_str):
            try:
                parsed = datetime.strptime(f"{date_str} {time_str}", "%m-%d-%Y %I:%M %p")
                logger.debug(f"Successfully parsed datetime: {parsed}")
                return parsed
            except ValueError as e:
                logger.debug(f"Failed to parse datetime: {e}")
        else:
            logger.debug("Date/time strings don't match expected patterns")
    else:
        logger.debug("Insufficient lines for datetime parsing")

    return None


def parse_references(text: str) -> List[str]:
    """
    Parses reference URLs from the 'Reference:' line until the 'Tags:' line.
    """
    logger = logging.getLogger(__name__)
    
    references = []
    in_references = False
    lines = text.split("\n")
    
    logger.debug(f"Parsing references from {len(lines)} lines")
    
    for line_num, line in enumerate(lines):
        if line.lower().startswith("reference:"):
            in_references = True
            line_content = line[len("Reference:") :].strip()
            if line_content:
                refs = re.split(r",\s*", line_content)
                references.extend(refs)
                logger.debug(f"Found reference line {line_num}: {len(refs)} refs")
        elif in_references:
            if line.lower().startswith("tags:"):
                logger.debug(f"Stopping reference parsing at line {line_num} (found 'Tags:')")
                break
            line_content = line.strip()
            if line_content:
                refs = re.split(r",\s*", line_content)
                references.extend(refs)
                logger.debug(f"Found additional reference line {line_num}: {len(refs)} refs")

    valid_refs = [ref for ref in references if ref]
    logger.debug(f"Parsed {len(valid_refs)} valid references from {len(references)} total")
    return valid_refs


def parse_tags(text: str) -> List[str]:
    """
    Parses tags from the 'Tags:' line.
    """
    logger = logging.getLogger(__name__)
    
    lines = text.split("\n")
    logger.debug(f"Parsing tags from {len(lines)} lines")
    
    for line_num, line in enumerate(lines):
        if line.lower().startswith("tags:"):
            tags = extract_wikilinks(line)
            logger.debug(f"Found tags line {line_num}: {len(tags)} tags extracted")
            return tags
    
    logger.debug("No tags line found")
    return []


def parse_body(raw_content: str) -> str:
    """
    Parses the main body of the note. The body is the content that appears
    after the 'Tags:' line and all associated tag declarations.
    """
    logger = logging.getLogger(__name__)
    
    lines = raw_content.split("\n")
    logger.debug(f"Parsing body from {len(lines)} lines")

    try:
        tags_line_index = next(
            i for i, line in enumerate(lines) if line.lower().startswith("tags:")
        )
        logger.debug(f"Found tags line at index {tags_line_index}")

        # The body starts after the block of tags.
        # A block of tags is a contiguous set of non-empty lines after "Tags:".

        body_start_line = tags_line_index + 1
        logger.debug(f"Initial body start line: {body_start_line}")

        # Move past any non-empty lines that are part of the tags block
        original_start = body_start_line
        while body_start_line < len(lines) and lines[body_start_line].strip():
            body_start_line += 1
        
        if body_start_line > original_start:
            logger.debug(f"Skipped {body_start_line - original_start} additional tag lines")

        # Move past any empty lines between tags and body
        empty_lines = 0
        while body_start_line < len(lines) and not lines[body_start_line].strip():
            body_start_line += 1
            empty_lines += 1
        
        if empty_lines > 0:
            logger.debug(f"Skipped {empty_lines} empty lines")

        if body_start_line < len(lines):
            body_content = "\n".join(lines[body_start_line:]).strip()
            logger.debug(f"Parsed body: {len(body_content)} characters")
            return body_content
        else:
            logger.debug("No body content found after tags")
            return ""

    except StopIteration:
        # If 'Tags:' is not found, consider the entire content as the body
        logger.info("No 'Tags:' line found, using entire content as body")
        return raw_content.strip()
