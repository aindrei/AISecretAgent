import json
import os
import requests
#from typing import override
from workers.web.web_search_worker import WebSearchWorker
from workflows.api_keys import brave_search_api_key

# Uses Brave Search API to perform web searches
class BraveWebSearchWorker(WebSearchWorker):
    def __init__(self, worker_name: str, result_type: str = WebSearchWorker.RESULT_TYPE_WEB, api_key: str = None):
        super().__init__(worker_name)
        if not api_key:
            api_key = os.environ["BRAVE_SEARCH_API_KEY"]
        assert api_key, "Brave Search API key is required"
        self.api_key = api_key
        self.result_type = result_type
        if self.result_type == WebSearchWorker.RESULT_TYPE_WEB:
            self.base_url = "https://api.search.brave.com/res/v1/web/search"
        elif self.result_type == WebSearchWorker.RESULT_TYPE_IMAGE:
            self.base_url = "https://api.search.brave.com/res/v1/images/search"
        else:
            raise ValueError(f"Invalid result type: {self.result_type}")

        # Initialize the HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        })

    #@override
    def search(self, keywords: str, number_of_results: int = 10) -> str:
        params = {
            "q": keywords,
            "count": number_of_results
        }

        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            response_text = response.text
            results = self.parse_results(response_text, number_of_results)
            #print(f"Search results: {results}")
            return results
        except requests.RequestException as e:
            return f"Error performing search: {str(e)}"
        
    #@override
    def cleanup(self):
        """Clean up the HTTP session"""
        if self.session:
            self.session.close()
            self.session = None
        
    def parse_results(self, response_text: str, number_of_results: int) -> list[dict]:
        try:
            search_response_object = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error {str(e)} when parsing search response: {response_text}")
            raise e
            return []

        if self.result_type == WebSearchWorker.RESULT_TYPE_WEB:
            return self.parse_web_results(search_response_object, number_of_results)
        elif self.result_type == WebSearchWorker.RESULT_TYPE_IMAGE:
            return self.parse_image_results(search_response_object)
        else:
            raise ValueError(f"Invalid result type: {self.result_type}")
        
    def parse_image_results(self, search_response_object) -> list[dict]:
        """
        Parse Brave search results into a list of standardized image objects
        
        Args:
            search_response_object: parsed JSON object response from Brave search API
            https://api-dashboard.search.brave.com/app/documentation/image-search/responses
            
        Returns:
            list[dict]: List of result objects with rank, url, description, type, image_url
        """
        results = search_response_object['results']

        image_results = []
        for i, result in enumerate(results):
            image_result = {}
            image_result['rank'] = i
            image_result['type'] = 'image'
            image_result['description'] = result.get('title', '')
            image_result['url'] = result.get('url', '')
            result_properties = result.get('properties', {})
            image_result['image_url'] = result_properties.get('url', '')
            image_results.append(image_result)
        
        return image_results

    def parse_web_results(self, search_response_object, number_of_results: int) -> list[dict]:
        """
        Parse Brave search results into a list of standardized objects
        
        Args:
            search_response (str): JSON response from Brave search API
            
        Returns:
            list[dict]: List of result objects with rank, url, description, type
        """

        results = []
        rank = 0

        # iterate over the mixed results which contains the results ordered by relevance
        if not 'mixed' in search_response_object or not 'main' in search_response_object['mixed']:
            print(f"No mixed results found for {search_response_object}")
            return []

        for result_reference in search_response_object['mixed']['main']:
            if len(results) >= number_of_results:
                break
            
            result_type = result_reference['type']
            # Only consider web and news results for now
            if result_type != 'web' and result_type != 'news':
                continue

            if result_reference['all']:
                # pull in all results from search_response_object[<type>]['results']
                for web_result in search_response_object[result_type]['results']:
                    if len(result_reference) >= number_of_results:
                        break
            
                    results.append({
                            'rank': rank,
                            'url': web_result['url'],
                            'title': web_result.get('title', ''),
                            'description': web_result.get('description', ''),
                            'type': result_type
                        })
                    rank += 1
            else:
                # Find the data in the specific category of results
                index = result_reference['index']
                result = search_response_object[result_type]['results'][index]
                results.append({
                    'rank': rank,
                    'url': result['url'],
                    'title': result.get('title', ''),
                    'description': result.get('description', ''),
                    'type': 'web'
                })
                rank += 1

        return results

def main():
    worker = BraveWebSearchWorker("brave search worker", WebSearchWorker.RESULT_TYPE_WEB, brave_search_api_key)
    number_of_results = 1
    result = worker.search("cute puppies", number_of_results)
    print(result)

if __name__ == "__main__":
    main()