import json
import os

from src.logger import logger


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


def get_json_to_data(json_file):
    """
    Loads the JSON data dynamically and handles errors.

    Args:
        json_file: Path to the JSON file.
    Returns:
        dict: Processed data dictionary or empty dict if error occurs
    """
    if not os.path.exists(json_file):
        logger.error(f"JSON file not found: {json_file}")
        return {}

    try:
        json_data = get_json(json_file)

        if not isinstance(json_data, dict):
            logger.error(f"Invalid JSON format: {json_file}")
            return {}

        # Build the data dictionary dynamically
        data = {key: value for key, value in json_data.items()
                if isinstance(value, dict)}

        # Ensure styles are present if available
        if "styles" in json_data and isinstance(json_data["styles"], dict):
            data["styles"] = json_data["styles"]

        logger.info(f"Successfully loaded JSON: {json_file}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON syntax in {json_file}: {e}")
    except FileNotFoundError:
        logger.error(f"File not found: {json_file}")
    except Exception as e:
        logger.error(f"Unexpected error while loading JSON ({json_file}): {e}")

    return {}
