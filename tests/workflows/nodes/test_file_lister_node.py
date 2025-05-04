import json
import pytest
from unittest.mock import Mock, patch
from workflows.nodes.file_lister_node import FileListerNode
from workers.storage.local_file_lister_worker import LocalFileListerWorker

@pytest.fixture
def valid_input():
    return {
        "file_location": "/test/path",
        "file_type": "local"
    }

def test_node_initialization():
    node = FileListerNode("test_node")
    assert node.node_id == "test_node"
    assert node.cache_enabled is False

def test_start_impl():
    node = FileListerNode("test_node")
    node.start()  # Should not raise any exceptions

def test_run_impl_with_valid_input(valid_input):
    mock_worker = Mock()
    mock_worker.list_files.return_value = ["file1.txt", "file2.txt"]
    
    with patch('workflows.nodes.file_lister_node.LocalFileListerWorker', return_value=mock_worker):
        node = FileListerNode("test_node")
        node.start()
        result = node.run(json.dumps(valid_input))
        
        assert json.loads(result) == {"files": ["file1.txt", "file2.txt"]}
        mock_worker.list_files.assert_called_once_with("/test/path")

def test_run_impl_missing_file_location():
    node = FileListerNode("test_node")
    node.start()
    invalid_input = json.dumps({"file_type": "local"})
    result = node.run(invalid_input)
    
    assert "error" in json.loads(result)
    assert "must contain 'file_location'" in json.loads(result)["error"]

def test_run_impl_missing_file_type():
    node = FileListerNode("test_node")
    node.start()
    invalid_input = json.dumps({"file_location": "/test/path"})
    result = node.run(invalid_input)
    
    assert "error" in json.loads(result)
    assert "Input must contain 'file_location' and 'file_type'" in json.loads(result)["error"]

def test_run_impl_invalid_file_type():
    node = FileListerNode("test_node")
    node.start()
    invalid_input = json.dumps({
        "file_location": "/test/path",
        "file_type": "invalid"
    })
    result = node.run(invalid_input)
    
    assert "error" in json.loads(result)
    assert "Unsupported file type" in json.loads(result)["error"]

def test_stop_impl_with_result():
    node = FileListerNode("test_node")
    node.start()
    node.result = json.dumps({"files": ["test.txt"]})
    result = node.stop_impl()
    
    assert json.loads(result) == {"files": ["test.txt"]}

def test_stop_impl_without_result():
    node = FileListerNode("test_node")
    node.start()
    result = node.stop_impl()
    
    assert json.loads(result) == {"error": "No result available"}
