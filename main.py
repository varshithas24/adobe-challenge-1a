import os
import json
import re
from pathlib import Path
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
import argparse


class PDFStructureExtractor:
    def __init__(self):
        self.heading_patterns = [
            r'^\s*(\d+(?:\.\d+)*\.?)\s+(.+)$',               # Numbered headings: 1., 1.1, 1.1.1
            r'^\s*([IVX]+\.)\s+(.+)$',                          # Roman numerals
            r'^\s*([A-Z]\.)\s+(.+)$',                           # Letters: A., B.
            r'^\s*(Chapter|Section|Part)\s+(\d+[:\-\s]*(.+))$',  # Chapter 1, Section 2
            r'^\s*(Abstract|Introduction|Methodology|Results|Discussion|Conclusion|References|Bibliography|Acknowledgments)\s*$'
        ]

    def is_numbered_form_label(self, text: str) -> bool:
        return bool(re.match(r"^\s*\d+(\(\w\))?\.\s+", text))

    def extract_title_from_metadata(self, doc) -> str:
        try:
            metadata = doc.metadata
            if metadata and 'title' in metadata and metadata['title']:
                title = metadata['title'].strip()
                if len(title) > 5 and not title.lower().endswith('.pdf'):
                    return title
        except:
            pass
        return ""

    def extract_title_from_text(self, doc) -> str:
        try:
            first_page = doc[0]
            blocks = first_page.get_text("dict")["blocks"]
            candidates = []
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if len(text) < 5 or len(text) > 200:
                            continue
                        y_pos = span["bbox"][1]
                        position_score = 1000 - y_pos
                        font_size = span["size"]
                        size_score = font_size * 10
                        font_flags = span.get("flags", 0)
                        format_score = 50 if font_flags & 2**4 else 0
                        total_score = position_score + size_score + format_score
                        candidates.append({
                            'text': text,
                            'score': total_score,
                            'y_pos': y_pos,
                            'font_size': font_size
                        })
            filtered_candidates = []
            for candidate in candidates:
                text = candidate['text'].lower()
                if not any(skip in text for skip in ['page', 'doi:', 'http', 'www.', '@', 'copyright']):
                    if not re.match(r'^\d+$', candidate['text'].strip()):
                        filtered_candidates.append(candidate)
            if filtered_candidates:
                best_candidate = sorted(filtered_candidates, key=lambda x: x['score'], reverse=True)[0]
                return best_candidate['text']
        except Exception as e:
            print(f"Error extracting title from text: {e}")
        return "Untitled Document"

    def classify_heading_level(self, text: str, font_size: float, avg_font_size: float, is_bold: bool, is_numbered: bool) -> str:
        for pattern in self.heading_patterns:
            match = re.match(pattern, text.strip(), re.IGNORECASE)
            if match:
                if is_numbered:
                    number_part = match.group(1)
                    if '.' in number_part:
                        level_depth = number_part.count('.')
                        if level_depth == 1:
                            return "H1"
                        elif level_depth == 2:
                            return "H2"
                        else:
                            return "H3"
                    else:
                        return "H1"
                else:
                    if font_size > avg_font_size * 1.3 or is_bold:
                        return "H1"
                    elif font_size > avg_font_size * 1.1:
                        return "H2"
                    else:
                        return "H3"
        if font_size > avg_font_size * 1.5:
            return "H1"
        elif font_size > avg_font_size * 1.2:
            return "H2"
        else:
            return "H3"

    def is_likely_heading(self, text: str, font_size: float, avg_font_size: float, is_bold: bool, position_y: float, page_height: float) -> bool:
        if len(text.strip()) < 3 or len(text.strip()) > 200:
            return False
        if self.is_numbered_form_label(text):
            return False
        has_heading_pattern = any(re.match(pattern, text.strip(), re.IGNORECASE) for pattern in self.heading_patterns)
        is_larger_font = font_size > avg_font_size * 1.1
        relative_position = position_y / page_height
        if has_heading_pattern:
            return True
        if is_bold and is_larger_font:
            return True
        if is_larger_font and font_size > avg_font_size * 1.3:
            return True
        return False

    def extract_headings(self, doc) -> List[Dict[str, Any]]:
        headings = []
        font_sizes = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip():
                            font_sizes.append(span["size"])
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_height = page.rect.height
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    line_text = ""
                    line_spans = []
                    for span in line["spans"]:
                        line_text += span["text"]
                        line_spans.append(span)
                    line_text = line_text.strip()
                    if not line_text:
                        continue
                    if line_spans:
                        dominant_span = max(line_spans, key=lambda s: len(s["text"]))
                        font_size = dominant_span["size"]
                        font_flags = dominant_span.get("flags", 0)
                        is_bold = bool(font_flags & 2**4)
                        position_y = dominant_span["bbox"][1]
                        if self.is_likely_heading(line_text, font_size, avg_font_size, is_bold, position_y, page_height):
                            is_numbered = bool(re.match(r'^\s*\d+(?:\.\d+)*\.?\s', line_text))
                            level = self.classify_heading_level(line_text, font_size, avg_font_size, is_bold, is_numbered)
                            headings.append({
                                "level": level,
                                "text": line_text,
                                "page": page_num + 1
                            })
        return headings

    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        try:
            doc = fitz.open(pdf_path)
            title = self.extract_title_from_metadata(doc)
            if not title:
                title = self.extract_title_from_text(doc)
            headings = self.extract_headings(doc)
            seen_headings = set()
            unique_headings = []
            for heading in headings:
                heading_key = (heading["text"], heading["page"])
                if heading_key not in seen_headings:
                    seen_headings.add(heading_key)
                    unique_headings.append(heading)
            unique_headings.sort(key=lambda x: x["page"])
            doc.close()
            return {
                "title": title,
                "outline": unique_headings
            }
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return {
                "title": "Error Processing Document",
                "outline": []
            }


def main():
    parser = argparse.ArgumentParser(description='Extract PDF structure for Adobe Challenge 1A')
    parser.add_argument('--input-dir', default='./input', help='Input directory containing PDFs')
    parser.add_argument('--output-dir', default='./output', help='Output directory for JSON files')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    extractor = PDFStructureExtractor()
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        print(f"Please add PDF files to the '{input_dir}' directory and run again.")
        return
    print(f"Found {len(pdf_files)} PDF files to process")
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        result = extractor.process_pdf(str(pdf_file))
        output_filename = pdf_file.stem + ".json"
        output_path = output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved: {output_filename}")
    print("Processing complete!")


if __name__ == "__main__":
    main()
