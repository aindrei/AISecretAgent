from pathlib import Path

class LocalFileWriterWorker():
    def __init__(self, worker_name: str, output_path: str):
        """
        Initialize the FileWriterWorker with the output file path.
        
        Args:
            output_path (str): Path where the HTML file will be written
        """
        self.worker_name = worker_name
        self.output_path = Path(output_path)

    # returns file path
    def write(self, text: str) -> str:
        """Process the input and write HTML content to file."""
        # Create directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return self.output_path

