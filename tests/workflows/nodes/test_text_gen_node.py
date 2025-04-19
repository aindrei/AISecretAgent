import pytest
from unittest.mock import Mock, patch
from workflows.nodes.text_gen_node import TextGenNode
from workers.llm.ollama_worker import OllamaWorker
from workers.llm.mistral_worker import MistralWorker

@pytest.fixture
def ollama_properties():
    return {
        "model_provider": "ollama",
        "worker_name": "test_ollama",
        "model_name": "llama2",
        "use_lib": True,
        "base_url": "http://localhost:11434"
    }

@pytest.fixture
def mistral_properties():
    return {
        "model_provider": "mistral", 
        "worker_name": "test_mistral",
        "model_name": "mistral",
        "api_key": "test_key"
    }

def test_create_ollama_worker(ollama_properties):
    node = TextGenNode("test_node", ollama_properties)
    node.start()
    assert isinstance(node.worker, OllamaWorker)
    assert node.worker.model_name == "llama2"
    assert node.worker.use_lib is True
    assert node.worker.base_url == "http://localhost:11434"

def test_create_mistral_worker(mistral_properties):
    node = TextGenNode("test_node", mistral_properties)
    node.start()
    assert isinstance(node.worker, MistralWorker)
    assert node.worker.model_name == "mistral"

def test_invalid_model_provider():
    invalid_properties = {
        "model_provider": "invalid",
        "model_name": "llama2",
    }
    with pytest.raises(ValueError, match="Invalid model provider: invalid"):
        node = TextGenNode("test_node", invalid_properties)
        node.start()

def test_missing_model_provider():
    invalid_properties = {
        "model_name": "llama2",
    }
    with pytest.raises(AssertionError, match="Model provider is required"):
        node = TextGenNode("test_node", invalid_properties)
        node.start()

def test_missing_model_name():
    invalid_properties = {
        "model_provider": "mistral",
    }
    with pytest.raises(AssertionError, match="Model name is required"):
        node = TextGenNode("test_node", invalid_properties)
        node.start()

def test_run_method():
    mock_worker = Mock()
    mock_worker.generate_response.return_value = "Generated text"
    
    with patch('workflows.nodes.text_gen_node.OllamaWorker', return_value=mock_worker):
        node = TextGenNode("test_node", {"model_provider": "ollama", "model_name": "llama2"})
        node.start()
        node.worker = mock_worker
        result = node.run("Test input")
        
        assert result == "Generated text"
        mock_worker.generate_response.assert_called_once_with("Test input", None, None, None)
