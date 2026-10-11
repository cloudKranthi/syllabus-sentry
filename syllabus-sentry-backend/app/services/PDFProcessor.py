import fitz
from typing import List,Dict,Any
class PDFProcessor:
    def __init__(self):
        pass
    @staticmethod    
    def get_text(pdf_bytes:bytes)->str:
        doc = fitz.open(stream=pdf_bytes,filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        doc.close()
        return "\n".join(text)
    @staticmethod
    def get_chunks(text:str,chunk_size:int=500,overlap:int=50)->List[str]:
        words=text.split()
        if not words: return[]
        chunks=[]
        start=0
        step = max(1, chunk_size - overlap)
        while start <len(words):
            end=start+chunk_size
            chunk=" ".join(words[start:end])
            chunks.append(chunk)
            if end>=len(words): break
            start+=step
        return chunks
    
