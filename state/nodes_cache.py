import hashlib
import json
import sqlite3

# Uses sqlite3 to store the output of the nodes. The key is the nodeid_input.
class NodesCache:
    file_name = None
    connection = None
    cursor = None

    @classmethod
    def init_database(cls, database_file_name: str = "database.db"):
        cls.file_name = database_file_name
        if not cls.connection:
            print("Initializing database")
            cls.connection = sqlite3.connect(database_file_name)
            cls.cursor = cls.connection.cursor()
            # Create a table with the key node_id+input and value output
            cls.cursor.execute("CREATE TABLE IF NOT EXISTS node_outputs (key TEXT PRIMARY KEY, output TEXT, output_type TEXT)")

    @classmethod
    def get_output(cls, cache_key: str, input) -> str:
        key = cls.build_cache_key(cache_key, input)
        print(f"Getting output for key: {key}")
        result = cls.cursor.execute("SELECT output, output_type FROM node_outputs WHERE key = ?", (key,)).fetchone()
        if result:
            output = result[0]
            output_type = result[1]
            if output_type == "object": # if the type is object, the value that was stored is a json string and we need to convert it back to an object
                return json.loads(output)
            return output
        return None
    
    @classmethod
    def set_output(cls, cache_key: str, input: str, output: str):
        key = cls.build_cache_key(cache_key, input)
        print(f"Setting output for key: {key}")
        output_type = cls.get_output_type(output)
        if output_type == "object":
            # Convert the object to json string
            output = json.dumps(output)
        cls.cursor.execute("INSERT INTO node_outputs (key, output, output_type) VALUES (?, ?, ?)", (key, output, output_type))
        cls.connection.commit()
    
    @classmethod
    def build_cache_key(cls, node_cache_key: str, input: str) -> str:
        if not isinstance(input, str):
            input = json.dumps(input, sort_keys=True)
        input_hash = hashlib.sha256(input.encode("UTF-8")).hexdigest()
        return node_cache_key + "_" + str(input_hash)
    
    @classmethod
    def get_output_type(cls, output: str) -> str:
        if isinstance(output, str):
            if output.startswith("{"):
                return "json"
            return "text"
        return "object"
