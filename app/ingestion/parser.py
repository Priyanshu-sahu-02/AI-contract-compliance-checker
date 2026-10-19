from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_text(file_path: str) -> str:
    reader = PdfReader(file_path)

    pages = []


    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"[Page {page_number}]\n{text}")

    return "\n\n".join(pages)

def split_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = text_splitter.split_text(text)
    return chunks



if __name__ == "__main__":
    text = extract_text("Priyanshu_Sahu.pdf")
    chunks = split_text(text)

    print("Total chunks:", len(chunks))
    

    for i, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Chunk {i} ---\n")
        print(chunk)

  

    