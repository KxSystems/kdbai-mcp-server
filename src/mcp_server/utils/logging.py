import logging


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the server."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
