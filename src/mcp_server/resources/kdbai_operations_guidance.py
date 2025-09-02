import logging

logger = logging.getLogger(__name__)


def kdbai_operations_guidance_impl() -> str:
    path = "src/mcp_server/resources/kdbai_operations_guidance.txt"
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def register_resources(mcp_server):
    @mcp_server.resource("file://kdbai_operations_guidance")
    async def kdbai_operations_guidance() -> str:
        """
        Provides guidance when using KDBAI operations like query, search and hybrid search.
        Incluides:
            - syntax information
            - examples of each operation
            - filters usage and examples
            - all other parameters usage and examples
            - guidance to follow in general
            - specific points to  take care while making decisions

        Returns:
            str: Guidance on using KDBAI operations.

        """
        return kdbai_operations_guidance_impl()

    return ["file://kdbai_operations_guidance"]
