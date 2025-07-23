# 🧠 Adobe Challenge 1A: PDF Structure Extractor  
**Connecting the Dots Through Docs**

## 🔍 Problem Statement  
Extract structured outlines from PDF documents — including:
- **Document title**
- **Headings (H1, H2, H3)**  
- **Page number for each heading**

This outline helps build intelligent document navigation for the next rounds.

---

## 📁 Project Structure

```
.
├── input/                # Folder to store input PDF files
├── output/               # JSON outputs are saved here
├── main.py               # Main script for PDF structure extraction
├── Dockerfile            # For building container image
├── requirements.txt      # Dependencies (PyMuPDF)
└── README.md             # Project documentation
```

---

## 🧩 Approach

### 1. PDF Parsing
- Uses `PyMuPDF` (fitz) to extract rich text information: font size, boldness, position.

### 2. Title Extraction
- First attempts to read from PDF metadata.
- Falls back to selecting the largest bold title-like text from the first page using a custom scoring system (size + Y-position).

### 3. Heading Detection
- Line text is checked for:
  - Known heading patterns (`1.`, `A.`, `I.`, `Chapter`, `Section`, etc.)
  - Boldness
  - Relative font size
  - Vertical position on the page (higher is more likely a heading)

### 4. Filtering
- Filters out invalid headings like form labels (`12. Amount of advance required`).
- Avoids duplicate headings across pages.

---

## 📂 Input/Output Folder Usage

- 📥 Place your `.pdf` files inside the `input/` folder.
- 📤 The script automatically generates `.json` files inside the `output/` folder, each with the same base filename as the input.

Example:
```
input/
├── sample.pdf

output/
├── sample.json
```

---

## 📝 Output Format

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Main Heading",
      "page": 1
    },
    {
      "level": "H2",
      "text": "Subsection",
      "page": 2
    },
    {
      "level": "H3",
      "text": "Sub-subsection",
      "page": 3
    }
  ]
}
```

⚠️ Ensure your output exactly follows this format — with keys `title`, `outline`, and for each heading: `level`, `text`, and `page`.

---

## 🐳 Run Using Docker

### 1. Build the Docker Image

```bash
docker build --platform linux/amd64 -t pdf-outline-extractor:latest .
```

### 2. Run the Container

#### ✅ For Linux/macOS:
```bash
docker run --rm   -v $(pwd)/input:/app/input   -v $(pwd)/output:/app/output   --network none   pdf-outline-extractor:latest
```

#### ✅ For Windows PowerShell:
```powershell
docker run --rm `
  -v "${PWD}\input:/app/input" `
  -v "${PWD}\output:/app/output" `
  --network none `
  pdf-outline-extractor:latest
```

---

## ⚙️ Tech Stack

- Python 3.10+
- PyMuPDF (fitz)
- argparse, json, re, pathlib, os

---

## ✅ Constraints Satisfied

| Requirement             | Status         |
|-------------------------|----------------|
| ⏱️ Max runtime (≤ 10s)    | ✅ Yes          |
| 📦 Model size ≤ 200MB     | ✅ No model used |
| 🌐 No network usage      | ✅ Yes          |
| 🖥️ CPU only              | ✅ Yes          |
| 🐳 Linux/amd64 Docker    | ✅ Yes          |

---

## 📚 Example Output

For `sample.pdf`:

```json
{
  "title": "Microsoft Word - LTC_CLAIM_FORMS .doc",
  "outline": [
    {
      "level": "H3",
      "text": "Application form for grant of LTC advance",
      "page": 1
    }
  ]
}
```

---

## ⚠️ What We Avoided

- ❌ No hardcoded file-specific logic
- ❌ No reliance on font size alone
- ❌ No AI/ML model dependencies
- ❌ No internet calls or cloud services

---

## ✅ Summary

- 🏗️ Modular code (reusable in Round 1B) — Yes  
- 🐳 Docker-compatible with AMD64 — Yes  
- 🧠 Heading detection accuracy with fallback logic — Yes  
- ⛓️ No external calls or large models — Yes  
- 📄 Works on any number of `.pdf` files — Yes  

---

## 🔜 Ready for Round 1B

This code is designed with modularity in mind to support the upcoming persona-based document intelligence required in **Round 1B** of the challenge.

---