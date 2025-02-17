import json


def get_json(file):
    """
    Loads and parses a JSON file.

    :param file: Path to the JSON file.
    :return: Parsed JSON data as a dictionary.
    :raises FileNotFoundError: If the file does not exist.
    :raises json.JSONDecodeError: If the file is not valid JSON.
    :raises Exception: Any other unexpected errors.
    """
    with open(file, "r", encoding="utf-8") as json_file:  # No path manipulation
        return json.load(json_file)
