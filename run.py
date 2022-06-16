# Import required packages.
from setuptools import setup
import yaml
import rich
import logging

# Define constants.
LOGGING_LEVEL = "INFO"  # Choices are: "DEBUG", "INFO", "WARN", "CRITICAL", "ERROR"

def setup_logger(level) -> logging.Logger:
    """
    Sets up the built-in python logger with the appropriate handlers and formatting.

    Parameters:
    -----------
        level - The level/depth at which information is logged.

    Returns:
    --------
        Logger - The logger object to interface with.
    """
    # Load config file.
    log_config = yaml.safe_load(open("logging_config.yaml", "r").read())
    logging.config.dictConfig(log_config)

    # Loop through the configured handlers in the yaml file and set their level.
    for handler in logging.getLogger().handlers:
        # Check if handler is an actual text console one.
        if isinstance(handler, type(rich.logging.RichHandler())):
            handler.setLevel(level)

    return logging.getLogger()

# Main program loop.
def main() -> None:
    # Initialize logger.
    logger = setup_logger(LOGGING_LEVEL)

    # Start UI.
    

# Call main function.
if __name__ == "__main__":
    main()