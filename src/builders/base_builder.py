import abc
import json
import os

from src.logger import python_logger
from src.service_factory import get_json

from src.logger import python_logger


def get_json_to_data(json_file):
    """
    Loads the JSON data dynamically and handles errors.
    """
    if not os.path.exists(json_file):
        python_logger.error(f"JSON file not found: {json_file}")
        return {}

    try:
        json_data = get_json(json_file)

        if not isinstance(json_data, dict):
            python_logger.error(f"Invalid JSON format: {json_file}")
            return {}

        # Build the data dictionary dynamically
        data = {key: value for key, value in json_data.items() if isinstance(value, dict)}

        # Ensure styles are present if available
        if "styles" in json_data and isinstance(json_data["styles"], dict):
            data["styles"] = json_data["styles"]

        python_logger.info(f"Successfully loaded JSON: {json_file}")
        return data

    except json.JSONDecodeError as e:
        python_logger.error(f"Invalid JSON syntax in {json_file}: {e}")
    except FileNotFoundError:
        python_logger.error(f"File not found: {json_file}")
    except Exception as e:
        python_logger.error(f"Unexpected error while loading JSON ({json_file}): {e}")

    return {}  # If there's an error, return an empty dictionary


class BaseBuilder(metaclass=abc.ABCMeta):
    def __init__(self, json_file, **kwargs):
        """
        :param json_file: Path to the JSON file.
        """
        self.valid = True  # Default: initialization is successful

        try:
            self.json_file = json_file
            self.data = get_json_to_data(json_file)
            if not self.data:
                python_logger.error("JSON loading failed!")
                self.valid = False

        except Exception as e:
            python_logger.error(f"Failed to load JSON: {e}")
            self.valid = False

        # PDF-specific properties
        self.paper_book = kwargs.get("paper_book", False)
        self.black_and_white = kwargs.get("black_and_white", False)
        self.short = kwargs.get("short", False)
        self.language = kwargs.get("language", "en")

        # EPUB-specific properties
        self.epub_type = kwargs.get("epub_type", None)

    @abc.abstractmethod
    def run(self):
        """Abstract method that must be implemented by subclasses."""
        pass
