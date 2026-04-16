import os
import sys
import logging


# Simple ANSI color codes
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Colors.BLUE,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, Colors.ENDC)
        record.levelname = f"{color}{record.levelname}{Colors.ENDC}"
        return super().format(record)


def setup_logging(name="ai", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if setup_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
