from typing import List, Dict, Any
import numpy as np
from abc import ABC, abstractmethod
from workflows.nodes.abstract_node import AbstractNode
from workers.storage.chromadb_worker import ChromaDbWorker
from workers.storage.milvus_db_worker import MilvusDbWorker
import json

# Finds the closest embeddings in a vector database
# Supported databases: Chroma, Milvus(not tested)
class VectorDbReaderNode(AbstractNode):
    def __init__(self, node_id: str, db_location: str, db_type: str = "chroma", num_results = 10, cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.db_location = db_location
        self.db_type = db_type.lower()
        self.num_results = num_results
        self.worker = None
        self.chunks = []
        self.embeddings = []

    def start_impl(self):
        self.result = []
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

    # Finds the closest embeddings in the vector database
    # Input: [{"text": "What is the capital of France?", "embeddings": [1,2]}]
    # Output: [{"text": "What is the capital of France?", "embeddings": [1,2], "closest_embeddings": [[1,2], [3,4]], "closest_texts": ["Paris", "Nice"]}]
    def run_impl(self, input_text: str) -> str:
        try:
            print(f"Processing input text: {input_text[:500]}")
            text_embeddings = json.loads(input_text)
            for text_embedding in text_embeddings:
                text = text_embedding.get("text")
                embeddings = text_embedding.get("embeddings")

                if not text or not embeddings:
                    raise ValueError("Invalid input: 'text' and 'embeddings' are required")
                
                closest_embeddings, closest_texts = self.worker.find_closest_embeddings(
                    query_embeddings=[embeddings], results=self.num_results
                )
                text_embedding["closest_embeddings"] = closest_embeddings[0].tolist()
                text_embedding["closest_texts"] = closest_texts[0]
                self.result.append(text_embedding)

            return json.dumps(self.result)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON input text: {input_text}")

    def stop_impl(self) -> str:
        return self.result

    def get_cache_key(self) -> str:
        return f"{self.node_id}:{self.db_location}:{self.db_type}"
    
def main():
    node = VectorDbReaderNode("node_name", "./chromadb_test.db", "chroma", 2)
    node.start()
    input_text = "[{\"text\": \"point1\", \"embeddings\": [1,1]}]"
    result = node.run(input_text)
    print(result)
    node.stop()

if __name__ == "__main__":
    main()