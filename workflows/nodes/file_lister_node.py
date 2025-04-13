import argparse
import json
from typing import List
from workflows.nodes.abstract_node import AbstractNode
from workers.storage.local_file_lister_worker import LocalFileListerWorker


class FileListerNode(AbstractNode):
    def __init__(self, node_id: str, cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)

    def start_impl(self):
        # Nothing to initialize
        pass

    def run_impl(self, input_text: str) -> str:
        # input: file path
        # output: {"files": [file_path1, file_path2, ...]}
        try:
            # Parse input JSON
            input_data = json.loads(input_text)
            
            # Validate required fields
            if 'file_location' not in input_data or 'file_type' not in input_data:
                raise ValueError("Input must contain 'file_location' and 'file_type'")
            
            location = input_data['file_location']
            file_type = input_data['file_type']

            # Handle different file types
            if file_type == "local":
                worker = LocalFileListerWorker("local_file_lister_worker")
                self.file_list = worker.list_files(location)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            print(f"Found {len(self.file_list)} files in {location}")
            # Convert result to JSON string
            result = json.dumps({"files": self.file_list})
            self.result = result
            return result

        except Exception as e:
            error_result = json.dumps({"error": str(e)})
            self.result = error_result
            return error_result

    def stop_impl(self) -> str:
        return self.result if self.result else json.dumps({"error": "No result available"})
    
def main(folder_path: str):
    # Test the FileListerNode
    node = FileListerNode("file_lister_node")
    input_data = json.dumps({"file_location": folder_path, "file_type": "local"})
    node.start()
    result = node.run(input_data)
    node.stop()
    print(result)

if __name__ == "__main__":
    # read the folder path from the command line argument folder_path
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--folder-path", type=str, help="The path to the folder to list files from")
    args = parser.parse_args()
    folder_path = args.folder_path

    main(folder_path)