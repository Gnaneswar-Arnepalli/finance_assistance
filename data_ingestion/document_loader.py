# document_loader.py

from pathlib import Path
from typing import List
from unstructured.partition.pdf import partition_pdf

def load_pdf_documents(directory: str) -> List[str]:
    """
    Load and extract text chunks from all PDF files in a directory.

    Args:
        directory (str): Path to folder containing PDF files.

    Returns:
        List[str]: List of text chunks extracted from PDFs.
    """
    all_chunks = []
    pdf_files = Path(directory).rglob("*.pdf")
    
    for pdf_path in pdf_files:
        try:
            elements = partition_pdf(filename=str(pdf_path))
            chunks = [el.text for el in elements if el.text.strip()]
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error reading {pdf_path.name}: {e}")
    
    return all_chunks

# Test run
if __name__ == "__main__":
    chunks = load_pdf_documents("sample_pdfs")
    print(f"Loaded {len(chunks)} chunks")
    print(chunks[:2])
