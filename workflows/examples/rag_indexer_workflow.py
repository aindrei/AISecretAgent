import json
from workflows.workflow import Workflow
from workflows.nodes.file_lister_node import FileListerNode
from workflows.nodes.document_chunker_node import DocumentChunkerNode
from workflows.nodes.embeddings_generator_node import EmbeddingsGeneratorNode
from workflows.nodes.vector_db_writer_node import VectorDbWriterNode
from workflows.workflow_validator import WorkflowValidator
import argparse

class RagIndexerWorkflowBuilder:
    def __init__(self):
        super().__init__()

    # Creates a workflow to index all the files in a specified folder into a vector database to be used for RAG searches
    # FileListerNode->DocumentChunkerNode->GenerateEmbeddingsNode->VectorDBWriterNode
    def build(self, db_location: str) -> Workflow:
        workflow = Workflow()

        # Start with a web search
        workflow.add_node("file_lister", FileListerNode("file lister node"))
        max_chunk_size = 400 # leaving some space to 512
        workflow.add_node("document_chunker", DocumentChunkerNode("document chunker node", max_chunk_size))
        model_properties = {"model_provider": "ollama", "model_name": "mxbai-embed-large"}
        workflow.add_node("embeddings_generator", EmbeddingsGeneratorNode("file lister node", model_properties))
        workflow.add_node("vector_db_writer", VectorDbWriterNode("vector db writer node", db_location, "chroma"))

        workflow.connect("file_lister", "document_chunker")
        workflow.connect("document_chunker", "embeddings_generator")
        workflow.connect("embeddings_generator", "vector_db_writer")

        workflow_validator = WorkflowValidator(workflow)
        valid = workflow_validator.validate_graph()
        if not valid:
            raise ValueError("Invalid graph")
        print(f"Graph is valid")

        return workflow

def main():
    parser = argparse.ArgumentParser(description='Index documents for RAG search')
    parser.add_argument('folder', type=str, help='Path to the folder containing documents to index')
    args = parser.parse_args()
    assert args.folder, "Folder path is required"

    workflow_builder = RagIndexerWorkflowBuilder()
    workflow = workflow_builder.build("./chromadb_test2.db")
    input_data = json.dumps({"file_location": args.folder, "file_type": "local"})
    result = workflow.run(input_data)
    workflow.save_trace_report("workflow_report_rag_indexer.html")
    print(result)

if __name__ == "__main__":
    main()