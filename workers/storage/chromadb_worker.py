from typing import List
import chromadb

class ChromaDbWorker():
    def __init__(self, uri: str, collection_name: str):
        self.uri = uri
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=uri)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    # TODO add metadata (ex. document and position) and ids    
    def add_vectors(self, documents: List[str], embeddings: List[List[float]]):
        assert len(documents) == len(embeddings)
        document_ids = []
        for i in range(len(documents)):
            document_ids.append(str(i))

        self.collection.add(
            documents = documents,
            embeddings = embeddings,
            ids = document_ids
        )

    # Finds the closest embeddings in the vector database
    # https://docs.trychroma.com/docs/querying-collections/query-and-get
    def find_closest_embeddings(self, query_embeddings: List[List[float]], results: int = 5):
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=results,
            include=["embeddings", "documents"] # need to specify this so that the embeddings are also returned
        )
        return results["embeddings"], results["documents"]

def main():
    documents = ["point1", "point2", "point3", "point4", "point5"]
    embeddings = [[1,1], [2,2], [3,3], [4,4], [5,5]]
    collection_name = "test_collection"
    worker = ChromaDbWorker(uri="./chromadb_test.db", collection_name=collection_name)
    worker.add_vectors(documents, embeddings)

    # Find the closest vectors to point1
    query_embeddings = [[1,1]]
    results = worker.collection.query(
        query_embeddings=query_embeddings, 
        n_results=2
    )
    print(results)

    closest_embeddings, closest_texts = worker.find_closest_embeddings(
        query_embeddings=query_embeddings, results=2
    )
    print("Closest embeddings:", closest_embeddings)
    print("Closest texts:", closest_texts)

if __name__ == "__main__":
    main()