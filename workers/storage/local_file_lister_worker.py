import os
from typing import List

class LocalFileListerWorker:
    def __init__(self, worker_name: str):
        self.worker_name = worker_name

    def list_files(self, location: str) -> List[str]:
        """List all files in the given location."""
        if os.path.isfile(location):
            return [location]
        elif os.path.isdir(location):
            file_list = []
            for root, _, files in os.walk(location):
                for file in files:
                    file_list.append(os.path.join(root, file))
            return file_list
        else:
            raise ValueError(f"Location not found: {location}")
        
def main():
    # Test the LocalFileListerWorker
    worker = LocalFileListerWorker("local_file_lister_worker")
    location = "add folder path here"
    file_list = worker.list_files(location)
    print(file_list)

if __name__ == "__main__":
    main()