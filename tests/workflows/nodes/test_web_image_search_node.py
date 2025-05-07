import pytest
from unittest.mock import Mock, patch
from workflows.nodes.web_image_search_node import WebImageSearchNode
from workers.web.web_search_worker import WebSearchWorker

@pytest.fixture
def web_image_search_node():
    return WebImageSearchNode("test-node", "fake-api-key", 5)

class TestWebImageSearchNode:
    def test_initialization(self, web_image_search_node):
        assert web_image_search_node.node_id == "test-node"
        assert web_image_search_node.api_key == "fake-api-key"
        assert web_image_search_node.number_of_results == 5
        assert web_image_search_node.worker is None

    @patch('workflows.nodes.web_image_search_node.BraveWebSearchWorker')
    def test_start_impl(self, mock_worker_class, web_image_search_node):
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker
        
        web_image_search_node.start_impl()
        
        mock_worker_class.assert_called_once_with(
            "brave_image_search_workertest-node",
            WebSearchWorker.RESULT_TYPE_IMAGE,
            "fake-api-key"
        )
        assert web_image_search_node.worker == mock_worker

    def test_run_impl(self, web_image_search_node):
        mock_worker = Mock()
        mock_worker.search.return_value = "mock results"
        web_image_search_node.worker = mock_worker
        
        result = web_image_search_node.run_impl("test query")
        
        mock_worker.search.assert_called_once_with("test query", 5)
        assert result == "mock results"

    def test_stop_impl(self, web_image_search_node):
        mock_worker = Mock()
        web_image_search_node.worker = mock_worker
        
        web_image_search_node.stop_impl()
        
        mock_worker.cleanup.assert_called_once()

    def test_get_cache_key(self, web_image_search_node):
        assert web_image_search_node.get_cache_key() == "test-node_5"
