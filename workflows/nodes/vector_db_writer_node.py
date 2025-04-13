from typing import List, Dict, Any
import numpy as np
from abc import ABC, abstractmethod
from workflows.nodes.abstract_node import AbstractNode
from workers.storage.chromadb_worker import ChromaDbWorker
from workers.storage.milvus_db_worker import MilvusDbWorker
import json

# Writes text embeddings to a vector database
# Supported databases: Chroma, Milvus(not tested)
class VectorDbWriterNode(AbstractNode):
    def __init__(self, node_id: str, db_location: str, db_type: str = "chroma", cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.db_location = db_location
        self.db_type = db_type.lower()
        self.worker = None
        self.segments = []
        self.embeddings = []

    def start_impl(self):
        if self.db_type == "milvus": # this is not tested
            connection_params = {
                "host": "localhost",
                "port": 19530,
                "db_location": self.db_location
            }
            self.worker = MilvusDbWorker(connection_params)
            self.worker.connect()
        elif self.db_type == "chroma": # this is tested
            self.worker = ChromaDbWorker(uri=self.db_location, collection_name="test_collection")
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    # Writes the embeddings to the database
    # Old Input: [{"segments": [{"text": "hello", "embeddings": [1,2], "location": None}],"doc_location": file_path}]
    # New input: [{"text": "hello", "embeddings": [1,2], "text_location_in_doc": None, "doc_location": file_path}]
    # Output: {"number_of_segments": 4, "number_of_documents": 2}
    def run_impl(self, input_text: str) -> str:
        documents = set()
        try:
            print(f"Processing input text: {input_text[:500]}")
            chunks = json.loads(input_text)
            
            for chunk in chunks:
                text = chunk.get("text", "")
                embeddings_list = chunk.get("embeddings", [])
                if not text or not embeddings_list or len(embeddings_list) < 1:
                    raise ValueError("Invalid input format or missing text/embeddings")
                doc_location = chunk.get("doc_location", None)
                if doc_location:
                    documents.add(doc_location)

                self.segments.append(text)
                self.embeddings.append(embeddings_list)

            self.worker.add_vectors(self.segments, self.embeddings)
            self.result = {
                "number_of_segments": len(self.segments),
                "number_of_documents": len(documents),
            }

            print(f"Successfully processed {len(self.segments)} chunks for vector database")
            return json.dumps(self.result)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON input text: {input_text}")

    def stop_impl(self) -> str:
        return self.result

    def get_cache_key(self) -> str:
        return f"{self.node_id}:{self.db_location}:{self.db_type}"
    
def main():
    node = VectorDbWriterNode("node_name", "./chromadb_test.db", "chroma")
    node.start()
    input_text = json.dumps([
        {"text": "file1text1", "embeddings": [1,1], "text_location_in_doc": None, "doc_location": "file1.txt"},
        {"text": "file1text2", "embeddings": [2,2], "text_location_in_doc": None, "doc_location": "file1.txt"},
        {"text": "file1text3", "embeddings": [3,3], "text_location_in_doc": None, "doc_location": "file1.txt"},
        {"text": "file2text1", "embeddings": [4,4], "text_location_in_doc": None, "doc_location": "file2.txt"}
    ])
    result = node.run(input_text)
    print(result)
    node.stop()

    # Find the closest vectors to point1
    query_embedding = [[1,1]]
    results =node.worker.collection.query(
        query_embeddings=query_embedding, 
        n_results=2
    )
    print("Finding the closest embeddings to [1,1]")
    print(results)

if __name__ == "__main__":
    main()