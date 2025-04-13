import json
from workflows.api_keys import *
from workflows.workflow import Workflow
from workflows.nodes.embeddings_generator_node import EmbeddingsGeneratorNode
from workflows.nodes.vector_db_reader_node import VectorDbReaderNode
from workflows.nodes.rag_context_preparer_node import RagContextPreparerNode
from workflows.nodes.text_gen_node import TextGenNode
from workflows.workflow_validator import WorkflowValidator

class RagRetrieverWorkflowBuilder:
    def __init__(self):
        super().__init__()

    # Creates a workflow to respond to a prompt using a RAG technique pointing to a vector database
    # EmbeddingsGeneratorNode->VectorDbReaderNode->RagContextPrepareNode->TextGenNode
    def build(self, db_location: str) -> Workflow:
        workflow = Workflow()

        # The passthrough node is used to duplicate the outputs
        emb_model_properties = {"model_provider": "ollama", "model_name": "mxbai-embed-large"}
        workflow.add_node("embeddings_generator", EmbeddingsGeneratorNode("embeddings generator node", emb_model_properties))
        workflow.add_node("vector_db_reader", VectorDbReaderNode("vector db reader node", db_location, "chroma"))
        workflow.add_node("rag_context", RagContextPreparerNode("rag context preparer node"))
        
        gen_model_properties = {
                "model_provider": "gemini",
                "model_name": "gemini-2.0-flash",
                "api_key": gemini_api_key,
            }
        prompt_properties = {}
        workflow.add_node("llm_answerer", TextGenNode("llm answerer node", gen_model_properties, prompt_properties))

        workflow.connect("embeddings_generator", "vector_db_reader")
        workflow.connect("vector_db_reader", "rag_context")
        workflow.connect("rag_context", "llm_answerer")

        workflow_validator = WorkflowValidator(workflow)
        valid = workflow_validator.validate_graph()
        if not valid:
            raise ValueError("Invalid graph")
        print(f"Graph is valid")

        return workflow

def main():
    workflow_builder = RagRetrieverWorkflowBuilder()
    workflow = workflow_builder.build("./chromadb_test2.db")
    input_data = json.dumps([{"text": "What recipes can I make with flour salt and yeast?"}])
    result = workflow.run(input_data)
    workflow.save_trace_report("workflow_report_rag_retriever.html")
    print("==============================================================")
    print(result)

if __name__ == "__main__":
    main()