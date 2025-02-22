import logging
from workflows.nodes.abstract_node import AbstractNode
#from typing import override
import requests
from bs4 import BeautifulSoup
import asyncio
from crawl4ai import *

# Node that receives a url and returns the content of the web page
class WebPageFetcherNode(AbstractNode):
    def __init__(self, node_id: str, cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.text_tags = set(["a", "img", "div", "span", "li", "p", "h1", "h2", "h3", "h4", "h5", "h6"])

    #@override
    def start_impl(self):
        self.logger.info(f"Starting node {self.node_id}")

    #@override
    def run_impl(self, input_text: str) -> str:
        print(f"Input text: {input_text}")
        url = input_text['url']
        print(f"Fetching web page: {url}")
        #web_page_html = self.get_web_page(url)
        
        web_page_html = asyncio.run(self.get_web_page_with_crawl4ai(url))
        web_page_text = self.extract_text_v2(web_page_html)

        self.result = web_page_text
        return web_page_text
    
    def get_web_page(self, url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        try:
            response = requests.get(
                url, 
                headers=headers,
                timeout=10,
                verify=True
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    async def get_web_page_with_crawl4ai(self, url: str) -> str:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
            )
            #return result.markdown
            return result.html

    def extract_text(self, web_page_html: str) -> str:
        soup = BeautifulSoup(web_page_html, features="html.parser")
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # get text
        text = soup.get_text()

        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    
    def extract_text_v2(self, web_page_html: str) -> str:
        # navigate the html tree and extract text from each link, image link, div, lists and paragraphs
        soup = BeautifulSoup(web_page_html, features="html.parser")
        text = ""
        for tag in soup.find_all(["body"]):
            #current_text = None
            #if tag.name == "img":
            #    current_text = tag.get("alt", "")
            #elif tag.name in self.text_tags:
            #    current_text = tag.get_text(" ")
            #if current_text:
            #    text += current_text + "|"
            text += tag.get_text(" ") + " "
            #print(f"Tag: {tag.name} Text: {text}")
        return text
    
    #@override
    def stop_impl(self) -> str:
        self.logger.info(f"Stopping node {self.node_id}")
        return self.result

def main():
    node = WebPageFetcherNode("web_page_fetcher")
    node.start_impl()
    #result = node.run_impl({"url": "https://www.example.com"})
    result = node.run_impl({"url": "https://www.viator.com/Los-Angeles/d645"})
    node.stop_impl()
    print(result)

def test_extract_text_v2():
    node = WebPageFetcherNode("web_page_fetcher")
    html = """
    <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <h1>Test</h1>
            <span>This is a <p>test</p></span>
        </body>
    </html>
    """
    html = """
    <body>
    <div class="AuQZR f"><div class="f u" data-automation="topNav_discover"><div class="JLKop w"><button class="rmyCe _G B- z _S c Wc wSSLS jWkoZ InwKl" type="button"><span class="biGQs _P ttuOS">Discover</span></button></div></div><div class="f u" data-automation="topNav_trips"><div class="JLKop w"><button class="rmyCe _G B- z _S c Wc wSSLS jWkoZ InwKl" type="button"><span class="biGQs _P ttuOS">Trips</span></button></div></div><div class="f u" data-automation="topNav_review"><div class="JLKop w"><button class="rmyCe _G B- z _S c Wc wSSLS jWkoZ InwKl" type="button"><span class="biGQs _P ttuOS">Review</span></button></div></div></div>
    </body>
    """
    text = node.extract_text_v2(html)
    print(f"Extracted text = {text}")
    
if __name__ == "__main__":
    main()