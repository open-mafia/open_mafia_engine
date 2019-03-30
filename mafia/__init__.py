# Logging best practices from here:
# https://docs.python-guide.org/writing/logging/
# Generally, we don't want logging unless the user wants it, so:
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"
