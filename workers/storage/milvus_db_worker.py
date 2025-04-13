# https://milvus.io/docs/build-rag-with-milvus.md
from pymilvus import MilvusClient
from typing import List

# This doesn't work on Windows so it is not tested
class MilvusDbWorker():
    def __init__(self, uri: str, collection_name: str, embeddings_dim: int, metric_type: str = "IP"):
        self.uri = uri
        self.collection_name = collection_name
        self.milvus_client = MilvusClient(uri=uri)
        if not self.milvus_client.has_collection(collection_name):
            self.milvus_client.create_collection(collection_name=collection_name, dimension=embeddings_dim, metric_type=metric_type)
        
    def add_vectors(self, chunks: List[str], embeddings: List[List[float]]):
        assert len(chunks) == len(embeddings)
        data = []
        for i, chunk in enumerate(chunks):
            embedding = embeddings[i]
            data.append({"id": i, "vector": embedding, "text": chunk})

        self.milvus_client.insert(collection_name=self.collection_name, data=data)

    # Not tested
    def find_closest_embeddings(self, query_embeddings: List[List[float]], results: int = 5):
        search_params = {"metric_type": "IP", "params": {}}
        results = self.milvus_client.search(
            collection_name=self.collection_name, 
            data=query_embeddings, 
            limit=results, 
            search_params=search_params,
            output_fields=["text"],
        )
        return results

def main():
    chunks = ["point1", "point2", "point3", "point4", "point5"]
    embeddings = [[1,1], [2,2], [3,3], [4,4], [5,5]]
    collection_name = "test_collection"
    milvus_db_worker = MilvusDbWorker(uri="./milvus_test.db", collection_name=collection_name, embeddings_dim=2)
    milvus_db_worker.add_vectors(chunks, embeddings)

    # Find the closest vectors to point1
    query_embedding = [[1,1]]
    results = milvus_db_worker.milvus_client.search(
        collection_name=collection_name, 
        data=query_embedding, 
        limit=2, 
        search_params={"metric_type": "IP", "params": {}},
        output_fields=["text"],
    )
    print(results)

if __name__ == "__main__":
    main()