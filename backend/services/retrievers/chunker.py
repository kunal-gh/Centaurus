"""
Centaurus Markdown Chunker.
Splits files into structured DocumentChunks and tags them with metadata.
"""
import os
import re
from typing import List, Dict, Any
from pydantic import BaseModel

class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]

def chunk_markdown_file(file_path: str) -> List[DocumentChunk]:
    """
    Reads a markdown file, splits it by '## ' headers, and parses out
    the section names and body text into a list of DocumentChunk objects.
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Try to find a top-level document title (e.g., # Centaurus Operations Manual)
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else os.path.basename(file_path)

    # Split the content by H2 headers
    sections = re.split(r"^##\s+", content, flags=re.MULTILINE)

    chunks = []
    
    # Process the intro section (any text before the first '## ')
    intro = sections[0].strip()
    # Remove the H1 title if present in intro to get actual body
    intro_body = re.sub(r"^#\s+.+$", "", intro, flags=re.MULTILINE).strip()
    if intro_body and len(intro_body) > 30:
        chunks.append(DocumentChunk(
            chunk_id="sec_introduction",
            text=intro_body,
            metadata={
                "source": os.path.basename(file_path),
                "section": "Introduction",
                "category": "policy",
                "document_title": doc_title
            }
        ))

    # Process all other sections
    for section in sections[1:]:
        if not section.strip():
            continue
            
        lines = section.split("\n")
        header = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        if len(body) < 10:
            # Exclude header-only or very short segments
            continue

        # Generate a slug for chunk_id
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", header).strip("_").lower()
        chunk_id = f"sec_{slug}"

        # Combine header and body into the retrieved text so the embedding captures both
        full_text = f"## {header}\n{body}"

        chunks.append(DocumentChunk(
            chunk_id=chunk_id,
            text=full_text,
            metadata={
                "source": os.path.basename(file_path),
                "section": header,
                "category": "policy",
                "document_title": doc_title
            }
        ))

    return chunks
