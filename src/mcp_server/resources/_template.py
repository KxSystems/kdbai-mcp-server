"""
Template for creating MCP server resources.

Resources provide read-only access to data that can be referenced by tools and prompts.
They are identified by URIs and can return various content types.

To create a new resource module:
1. Copy this file to a new name (without the leading underscore)
2. Implement your resource logic in the *_impl functions
3. Update the register_resources function with your resource decorators
4. The module will be automatically discovered and registered

Resource URI patterns:
- Use consistent naming: "category://subcategory/item"
- Examples: "database://tables", "files://config/{filename}", "api://status"
- Use path parameters for dynamic resources: {param_name}

Content types available:
- TextContent: Plain text or formatted text
- ImageContent: Image data with specific formats
"""

import logging
from typing import List
from mcp.types import TextContent, ImageContent

logger = logging.getLogger(__name__)


async def example_static_resource_impl() -> List[TextContent]:
    try:
        # Your resource logic here
        content = "This is example static resource content"

        logger.info("Static resource accessed successfully")
        return [TextContent(type="text", text=content)]

    except Exception as e:
        logger.error(f"Error accessing static resource: {e}")
        return [TextContent(type="text", text=f"Error accessing resource: {str(e)}")]


def register_resources(mcp_server):
    """
    Register all resources from this module with the MCP server.

    Args:
        mcp_server: The FastMCP server instance

    Returns:
        List[str]: List of registered resource URIs
    """

    @mcp_server.resource("example://static")
    async def example_static_resource() -> List[TextContent]:
        """
        Implementation for a static resource that doesn't take parameters.

        Returns:
            List[TextContent]: Resource content as text
        """
        return await example_static_resource_impl()

    return [
        "example://static",
    ]
