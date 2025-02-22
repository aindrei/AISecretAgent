from workflows.workflow import Workflow
from workflows.api_keys import *
from pydantic import BaseModel, Field
from typing import List
from enum import Enum
from workflows.nodes.web_search_node import WebSearchNode
from workflows.nodes.web_page_fetcher_node import WebPageFetcherNode
from workflows.nodes.text_gen_node import TextGenNode
from workflows.nodes.collate_node import CollateNode
from workflows.nodes.writer_node import WriterNode
from workflows.workflow_validator import WorkflowValidator


class AttractionCategory(str, Enum):
    MUSEUM = "museum"
    LANDMARK = "landmark"
    PARK = "park"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"

class Attraction(BaseModel):
    name: str
    description: str = Field(max_length=100)
    popularity_score: int = Field(ge=1, le=10)
    category: AttractionCategory

class TouristAttractions(BaseModel):
    attractions: List[Attraction]

class TouristAttractionsWorkflow:
    LLM_PROMPT = """Analyze the following article and extract the most popular tourist attractions in {city}.
            Return the results in JSON format.

            Rules:
            - Include only important tourist attractions
            - Estimate a popularity_score (number from 1 to 100 based on popularity or rating)
            - If there is a star ratings convert the 1-5 star rating to 1-100 popularity_score by multiplying by 20
            - An attraction that is listed earlier in the page is higher popularity
            - Maximum 10 attractions
            - Sort by popularity_score descending
            - category should be one of: museum, landmark, park, entertainment
            - Description should highlight key features

            Article:
            {input_text}"""

    # This was used before I gave it the structure format through the API
    LLM_PROMPT_WITH_FORMAT = """Analyze the following article and extract the most popular tourist attractions in {city}.
            Return the results in this exact JSON format:
            {
                "attractions": [
                    {
                        "name": "string",
                        "description": "string (max 100 words)",
                        "popularity_score": number (1-10),
                        "category": "string (museum/landmark/park/entertainment)"
                    }
                ]
            }

            Rules:
            - Include only tourist attractions
            - Score based on visitor numbers and reviews
            - Maximum 10 attractions
            - Sort by popularity_score descending
            - Description should highlight key features

            Article:
            {input_text}"""
    
    LLM_PROMPT_HTML_REPORT = """ Given the following list of tourist attractions in JSON format create a HTML report with the following format:
            - Title: Tourist Attractions in {city}
            - Table with columns: Index, Name, Description, Popularity Score, Category
            Attractions: {input_text}
            """
    
    SUMMARIZE_LLM_PROMPT_WITH_FORMAT = """Given the following tourist attractions in {city} that were obtained from multiple sources, deduplicate and sort the results by popularity_score descending. 
        Return the result in the same JSON format. Attractions:
         {input_text}"""
    
    def __init__(self):
        super().__init__()

    def _build_model_properties(self, model_provider: str, llm_prompt: str) -> dict:
        if model_provider == "mistral":
            model_properties = {
                "model_provider": "mistral",
                "model_name": "mistral-large-latest", #"ministral-8b-latest"
                "api_key": mistral_api_key,
            }
        elif model_provider == "deepseek":
            model_properties = {
                "model_provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": deepseek_api_key,
            }
        elif model_provider == "gemini":
            model_properties = {
                "model_provider": "gemini",
                "model_name": "gemini-2.0-flash",
                "api_key": gemini_api_key,
            }
        elif model_provider == "ollama":
            model_properties = {
                "model_provider": "ollama",
                "model_name": "deepseek-r1:14b", #"phi4:latest", #"qwen2:7b",
            }
        else:
            raise ValueError(f"Invalid model provider: {model_provider}")
        model_properties["instructions"] = llm_prompt
        return model_properties

    # Build a workflow to find the best tourist attractions in a city. Start with a search query, fetch web pages,
    # extract top attractions from each website and collate the results.
    # WebSearchNode --> WebPageFetcherNode --> TextGenNode --> CollateNode --> SummarizeNode
    #                 \-> WebPageFetcherNode --> TextGenNode --/
    def build(self, city: str, number_of_results: int = 1) -> Workflow:
        workflow = Workflow()

        # Start with a web search
        workflow.add_node("search", WebSearchNode("web search node", brave_search_api_key, number_of_results, True))

        # Create the branches with web fetcher and llm text gen
        llm_prompt = self.LLM_PROMPT.replace("{city}", city)
        model_provider = "deepseek"
        model_properties = self._build_model_properties(model_provider, llm_prompt)
        prompt_properties = {
            "output_format": "json",
            "response_model": TouristAttractions,
        }
        for i in range(number_of_results):
            web_fetcher_node_id = f"web page fetcher node{i+2}"
            workflow.add_node(web_fetcher_node_id, WebPageFetcherNode(web_fetcher_node_id, True))
            workflow.connect("search", web_fetcher_node_id)

            llm_node_id = f"llm node{i+2}"
            model_properties["worker_name"] = f"llm worker{i+2}"

            workflow.add_node(llm_node_id, TextGenNode(llm_node_id, model_properties, prompt_properties, True))
            workflow.connect(web_fetcher_node_id, llm_node_id)

        # Connect all the branches to the collate node
        workflow.add_node("collator", CollateNode("collate node"))
        for i in range(number_of_results):
            llm_node_id = f"llm node{i+2}"
            workflow.connect(llm_node_id, "collator")

        # Create an LLM node to deduplicate and sort the results
        summarize_prompt = self.SUMMARIZE_LLM_PROMPT_WITH_FORMAT.replace("{city}", city)
        summarize_node = TextGenNode("summarize", self._build_model_properties(model_provider, summarize_prompt), prompt_properties, True)
        workflow.add_node("summarize", summarize_node)
        workflow.connect("collator", "summarize")

        html_report_prompt = self.LLM_PROMPT_HTML_REPORT.replace("{city}", city)
        html_prompt_properties = {
            "output_format": "html"
        }
        html_report_node = TextGenNode("html report", self._build_model_properties(model_provider, html_report_prompt), html_prompt_properties, True)
        workflow.add_node("html report", html_report_node)
        workflow.connect("summarize", "html report")

        file_writer_node = WriterNode("file writer", WriterNode.LOCAL_DISK, "tourist_attractions_la.html", False)
        workflow.add_node("file_writer", file_writer_node)
        workflow.connect("html report", "file_writer")
        
        workflow_validator = WorkflowValidator(workflow)
        valid = workflow_validator.validate_graph()
        if not valid:
            print("Invalid graph")
            return None
        print(f"Graph is valid")

        return workflow
    
def main():
    city = "Los Angeles"
    #city = "Seattle"
    workflow_builder = TouristAttractionsWorkflow()
    number_of_results = 6
    workflow = workflow_builder.build(city, number_of_results)
    result = workflow.run(f"things to do in {city}")
    workflow.save_trace_report("workflow_report.html")
    print(result)

if __name__ == "__main__":
    main()