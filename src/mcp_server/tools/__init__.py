import logging
import importlib
from typing import List, Set
from pathlib import Path
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def _discover_tool_modules() -> List[str]:
    tools_dir = Path(__file__).parent

    tool_modules = []
    for file_path in tools_dir.glob("*.py"):
        # Name tools with a leading _ to disable them
        if file_path.name != "__init__.py" and not file_path.name.startswith("_"):
            module_name = file_path.stem
            tool_modules.append(module_name)

    return sorted(tool_modules)


def register_tools(mcp_server: FastMCP) -> List[str]:
    registered_tools = []
    failed_modules = []
    skipped_modules = []

    logger.info(("=" * 30, "Starting tool registration process", "=" * 30))

    tool_modules = _discover_tool_modules()
    logger.info(f"Discovered tool modules: {tool_modules}")

    if not tool_modules:
        logger.warning("No tool modules found in tools directory")
        return registered_tools

    for module_name in tool_modules:
        try:
            logger.info(f"Processing module: {module_name}")

            # Import the module dynamically
            module = importlib.import_module(f".{module_name}", package=__name__)

            # Register tools from this module
            register_func = getattr(module, "register_tools")
            tools = register_func(mcp_server)

            if tools:
                tools_list = tools if isinstance(tools, list) else [tools]
                registered_tools.extend(tools_list)
                for tool in tools_list:
                    logger.info(
                        f"Registered tool: '{tool}' from module '{module_name}'"
                    )
            else:
                logger.warning(f"Module '{module_name}' returned no tools")
                skipped_modules.append(module_name)

        except ImportError as e:
            logger.error(f"Failed to import module '{module_name}': {e}")
            failed_modules.append(module_name)
        except Exception as e:
            logger.error(f"Error processing module '{module_name}': {e}")
            failed_modules.append(module_name)

    logger.info(("=" * 30, "Tools registration summary", "=" * 30))
    logger.info(f"Successfully registered: {len(registered_tools)} tools")
    logger.info(f"Failed modules: {len(failed_modules)} - {failed_modules}")
    logger.info(f"Skipped modules: {len(skipped_modules)} - {skipped_modules}")

    if registered_tools:
        logger.info(f"Registered tools: {registered_tools}")

    logger.info("=" * 60)

    return registered_tools


def get_available_tools() -> List[str]:
    return _discover_tool_modules()
