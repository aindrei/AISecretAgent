import pytest
import json
from unittest.mock import Mock, patch
from workflows.nodes.document_chunker_node import DocumentChunkerNode
from docling.document_converter import DocumentConverter

@pytest.fixture
def test_file_path():
    return "test_document.pdf"

@pytest.fixture
def chunker_node():
    return DocumentChunkerNode("test_chunker")

def test_init():
    node = DocumentChunkerNode("test_node")
    assert node.node_id == "test_node"
    assert node.max_chunk_size == 512
    assert node.min_chunk_size == 256
    assert node.overlap == 50
    assert node.tokenizer == "BAAI/bge-small-en-v1.5"

def test_invalid_input(chunker_node):
    chunker_node.start()
    with pytest.raises(ValueError, match="Invalid input"):
        chunker_node.run('{"invalid": []}')

@patch.object(DocumentConverter, 'convert')
def test_chunk_file(mock_convert, chunker_node, test_file_path):
    # Mock document with some text
    mock_doc = Mock()
    mock_doc.meta.headings = ["Section 1"]
    mock_doc.text = "This is a test document"
    
    # Mock conversion result
    mock_conv_result = Mock()
    mock_conv_result.document = mock_doc
    mock_convert.return_value = mock_conv_result

    # Mock chunker
    with patch('workflows.nodes.document_chunker_node.HybridChunker') as mock_chunker_class:
        mock_chunker = Mock()
        mock_chunk = Mock()
        mock_chunk.meta.headings = ["Section 1"]
        mock_chunk.text = "This is a test document"
        mock_chunker.chunk.return_value = [mock_chunk]
        mock_chunker_class.return_value = mock_chunker

        chunker_node.start()
        input_json = json.dumps({"files": [test_file_path]})
        result = chunker_node.run(input_json)
        chunks = json.loads(result)

        assert len(chunks) == 1
        assert chunks[0]["text"] == "Section 1: This is a test document"
        assert chunks[0]["doc_location"] == test_file_path
        assert chunks[0]["text_location_in_doc"] is None

def test_chunker_with_cache(test_file_path):
    node = DocumentChunkerNode("test_node", cache_enabled=True)
    node.start()
    
    with patch.object(DocumentConverter, 'convert'), \
         patch('workflows.nodes.document_chunker_node.HybridChunker'):
        
        input_json = json.dumps({"files": [test_file_path]})
        first_result = node.run(input_json)
        node.stop()

        # Second run should hit cache
        node.start()
        second_result = node.run(input_json)
        assert first_result == second_result
        assert node.cache_hit == True
