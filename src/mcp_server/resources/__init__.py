import logging
import importlib
from typing import List
from pathlib import Path
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def _discover_resource_modules() -> List[str]:
    resources_dir = Path(__file__).parent

    resource_modules = []
    for file_path in resources_dir.glob("*.py"):
        # Name resources with a leading _ to disable them
        if file_path.name != "__init__.py" and not file_path.name.startswith("_"):
            module_name = file_path.stem
            resource_modules.append(module_name)

    return sorted(resource_modules)


def register_resources(mcp_server: FastMCP) -> List[str]:
    """Register all available resources with the server."""
    registered_resources = []
    failed_modules = []
    skipped_modules = []

    logger.info(("=" * 30, "Starting resource registration process", "=" * 30))

    resource_modules = _discover_resource_modules()
    logger.info(f"Discovered resource modules: {resource_modules}")

    if not resource_modules:
        logger.warning("No resource modules found in resources directory")
        return registered_resources

    for module_name in resource_modules:
        try:
            logger.info(f"Processing module: {module_name}")

            module = importlib.import_module(f".{module_name}", package=__name__)

            if hasattr(module, "register_resources"):
                register_func = getattr(module, "register_resources")
                resources = register_func(mcp_server)

                if resources:
                    resources_list = (
                        resources if isinstance(resources, list) else [resources]
                    )
                    registered_resources.extend(resources_list)
                    for resource in resources_list:
                        logger.info(
                            f"Registered resource: '{resource}' from module '{module_name}'"
                        )
                else:
                    logger.warning(f"Module '{module_name}' returned no resources")
                    skipped_modules.append(module_name)
            else:
                logger.warning(
                    f"Module '{module_name}' has no register_resources function"
                )
                skipped_modules.append(module_name)

        except ImportError as e:
            logger.error(f"Failed to import module '{module_name}': {e}")
            failed_modules.append(module_name)
        except Exception as e:
            logger.error(f"Error processing module '{module_name}': {e}")
            failed_modules.append(module_name)

    logger.info(("=" * 30, "Resource registration summary", "=" * 30))
    logger.info(f"Successfully registered: {len(registered_resources)} resources")
    logger.info(f"Failed modules: {len(failed_modules)} - {failed_modules}")
    logger.info(f"Skipped modules: {len(skipped_modules)} - {skipped_modules}")

    if registered_resources:
        logger.info(f"Registered resources: {registered_resources}")

    logger.info("=" * 60)

    return registered_resources


def get_available_resources() -> List[str]:
    return _discover_resource_modules()
