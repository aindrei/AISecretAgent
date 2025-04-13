from typing import List
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
import sys
import json
from workflows.nodes.abstract_node import AbstractNode

# See how it is used for RAG:
# https://ds4sd.github.io/docling/examples/rag_langchain/#document-loading
class DocumentChunkerNode(AbstractNode):
    def __init__(self, node_id: str, 
                 max_chunk_size: int = 512,
                 min_chunk_size: int = 256,
                 overlap: int = 50,
                 tokenizer="BAAI/bge-small-en-v1.5",
                 cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.tokenizer = tokenizer
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
        self.converter = None
        self.result = None

    def start_impl(self):
        self.converter = DocumentConverter()
        self.result = []

    def run_impl(self, input_text):
        # Input: {"files": ["path1", "path2"]}
        # Output: [{"text": "hello", "text_location_in_doc": None, "doc_location": file_path}]
        json_obj = json.loads(input_text)
        if "files" not in json_obj:
            print(f"Invalid input: {input_text} - expected 'files' key")
            raise ValueError("Invalid input")
        file_paths = json_obj["files"]
        text_segments = []
        for file_path in file_paths:
            text_segments.extend(self.chunk_file(file_path))
        self.result = json.dumps(text_segments)
        return self.result

    def chunk_file(self, file_path: str) -> List[dict]:
        print(f"Chunking file: {file_path}")
        conv_res = self.converter.convert(file_path)
        doc = conv_res.document
        
        chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_chunk_size=self.max_chunk_size,
            min_chunk_size=self.min_chunk_size,
            overlap=self.overlap)

        chunks_iterator = chunker.chunk(doc)
        text_chunks = self._convert_chunks(chunks_iterator, file_path)
        return text_chunks

    def _convert_chunks(self, chunks_iterator, file_path: str) -> dict:
        chunks = []
        for docling_chunk in chunks_iterator:
            #print(docling_chunk)
            headings = ". ".join(docling_chunk.meta.headings) if docling_chunk.meta.headings else ""
            chunk_text = ": ".join([headings,docling_chunk.text])
            chunk = {
                "text": chunk_text,
                "text_location_in_doc": None, #TODO add chunk location
                "doc_location": file_path,
            }
            chunks.append(chunk)

        print(f"Number of chunks: {len(chunks)}")
        
        return chunks
    
    def stop_impl(self):
        return self.result

def main(file_path):
    chunker_node = DocumentChunkerNode("document_chunker_node")
    chunker_node.start()
    response_text = chunker_node.run(file_path)
    chunker_node.stop()

    chunks = json.loads(response_text)
    print(f"Response: {chunks}")
    
    for i, chunk in enumerate(chunks):
        doc_location = chunk["doc_location"]
        print(f"File {i} {doc_location}")
        chunk_text = chunk["text"]
        print(chunk_text)
        print("-" * 40)

    print(f"Total number of chunks: {len(chunks)}")
    print("-" * 80)

# Example usage: python document_chunker_node.py "C:\Alex\Docs\Ebooks\test\The Professional Pizza Guide.pdf"
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python document_chunker_node.py <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    node_input = json.dumps({"files": [file_path]})
    main(node_input)