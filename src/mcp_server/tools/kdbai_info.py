import logging
from typing import Dict, Any
from mcp_server.utils.kdbai import get_kdbai_client

logger = logging.getLogger(__name__)


async def kdbai_session_info_impl() -> Dict[str, Any]:
    try:
        client = get_kdbai_client()
        info = client.session_info()
        return info
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise


async def kdbai_system_info_impl() -> Dict[str, Any]:
    try:
        client = get_kdbai_client()
        info = client.system_info()
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise


async def kdbai_process_info_impl() -> Dict[str, Any]:
    try:
        client = get_kdbai_client()
        info = client.process_info()
        return info
    except Exception as e:
        logger.error(f"Error getting process info: {e}")
        raise


def register_tools(mcp_server):
    @mcp_server.tool()
    async def kdbai_session_info() -> str:
        """
        Get session information from KDB.AI.

        Returns:
            Dictionary containing session information and metadata.
        """
        info = await kdbai_session_info_impl()
        return str(info)

    @mcp_server.tool()
    async def kdbai_system_info() -> str:
        """
        Get system information from KDB.AI.

        Returns:
            Dictionary containing system information and metadata.
        """
        info = await kdbai_system_info_impl()
        return str(info)

    @mcp_server.tool()
    async def kdbai_process_info() -> str:
        """
        Get process information from KDB.AI.

        Returns:
            Dictionary containing process information and metadata.
        """
        info = await kdbai_process_info_impl()
        return str(info)

    return ["kdbai_session_info", "kdbai_system_info", "kdbai_process_info"]
