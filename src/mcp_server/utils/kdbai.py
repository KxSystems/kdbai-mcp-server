import logging
from functools import lru_cache
from typing import Optional, Union
import kdbai_client as kdbai
from kdbai_client.rerankers import CohereReranker, JinaAIReranker, VoyageAIReranker
from mcp_server.settings import KDBAIConfig
from mcp_server.server import app_settings

db_config = app_settings.db
logger = logging.getLogger(__name__)

@lru_cache()
def get_kdbai_client(config: Optional[KDBAIConfig] = None) -> kdbai.Session:
    if config is None:
        config = db_config

    logger.debug(f"KDBAIConfig: {config=}")
    logger.info(f"Connecting to KDB.AI at {config.host}:{config.port}")
    retry = config.retry
    for attempt in range(1, retry + 1):
        try:
            if config.password:
                conn_options = {"username":config.username, "password":config.password.get_secret_value(), "reconnection_attempts":2}
            else:
                conn_options = {"reconnection_attempts":2}

            protocol = "http"
            if config.mode == "rest":
                protocol = config.rest_protocol
            else:  # qipc mode
                if config.qipc_tls:
                    conn_options["tls"] = True

            endpoint = f"{protocol}://{config.host}:{config.port}"
            client = kdbai.Session(endpoint=endpoint, mode=config.mode, options=conn_options)
            logger.info("Connected to KDB.AI")
            return client
        except Exception as e:
            logger.warning(f"KDB.AI connectivity attempt {attempt}/{retry} failed: {str(e)}")
            if attempt == retry:
                logger.error(f"Failed to connect to KDB.AI after {retry} attempts")
                raise


@lru_cache()
def get_reranker(
    config: Optional[KDBAIConfig] = None,
) -> Union[CohereReranker, JinaAIReranker, VoyageAIReranker]:
    if config is None:
        config = db_config

    if not config.reranker_api_key:
        raise ValueError(
            f"{config.reranker_provider.upper()}_API_KEY environment variable is not set."
        )

    kwargs = {
        "api_key": config.reranker_api_key,
        "overfetch_factor": config.overfetch_factor,
    }

    if config.reranker_model:
        kwargs["model"] = config.reranker_model

    if config.reranker_provider.lower() == "cohere":
        return CohereReranker(**kwargs)
    elif config.reranker_provider.lower() == "jina":
        return JinaAIReranker(**kwargs)
    elif config.reranker_provider.lower() == "voyage":
        return VoyageAIReranker(**kwargs)
    else:
        raise ValueError(
            f"Unsupported reranker provider: {config.reranker_provider}. Supported providers: cohere, jina, voyage"
        )


def get_table(table_name: str, database_name: Optional[str] = None) -> kdbai.Table:

    if database_name is None:
        database_name = db_config.database_name

    try:
        client = get_kdbai_client()
        logger.debug(f"Retrieving table '{table_name}' from database '{database_name}'")
        return client.database(database_name).table(table_name)
    except Exception as e:
        if "Error during creating connection" in str(e):
            logger.warning("KDBAI connection issue detected. Reinitializing...")
            cleanup_kdbai_client()
            client = get_kdbai_client()
            return client.database(database_name).table(table_name)
        else:
            logger.error(f"Error retrieving KDBAI table '{table_name}': {e}")
            raise


def cleanup_kdbai_client():
    get_kdbai_client.cache_clear()
    logger.info("KDBAI client cache cleared")
