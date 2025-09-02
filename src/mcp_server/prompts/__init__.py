import logging
import importlib
from typing import List
from pathlib import Path
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def _discover_prompt_modules() -> List[str]:
    prompts_dir = Path(__file__).parent

    prompt_modules = []
    for file_path in prompts_dir.glob("*.py"):
        # Name prompts with a leading _ to disable them
        if file_path.name != "__init__.py" and not file_path.name.startswith("_"):
            module_name = file_path.stem
            prompt_modules.append(module_name)

    return sorted(prompt_modules)


def register_prompts(mcp_server: FastMCP) -> List[str]:
    registered_prompts = []
    failed_modules = []
    skipped_modules = []

    logger.info(("=" * 30, "Starting prompt registration process", "=" * 30))

    prompt_modules = _discover_prompt_modules()
    logger.info(f"Discovered prompt modules: {prompt_modules}")

    if not prompt_modules:
        logger.warning("No prompt modules found in prompts directory")
        return registered_prompts

    for module_name in prompt_modules:
        try:
            logger.info(f"Processing module: {module_name}")

            # Import the module dynamically
            module = importlib.import_module(f".{module_name}", package=__name__)

            register_func = getattr(module, "register_prompts")
            prompts = register_func(mcp_server)

            if prompts:
                prompts_list = prompts if isinstance(prompts, list) else [prompts]
                registered_prompts.extend(prompts_list)
                for prompt in prompts_list:
                    logger.info(
                        f"Registered prompt: '{prompt}' from module '{module_name}'"
                    )
            else:
                logger.warning(f"Module '{module_name}' returned no prompts")
                skipped_modules.append(module_name)

        except ImportError as e:
            logger.error(f"Failed to import module '{module_name}': {e}")
            failed_modules.append(module_name)
        except Exception as e:
            logger.error(f"Error processing module '{module_name}': {e}")
            failed_modules.append(module_name)

    logger.info(("=" * 30, "Prompt registration summary", "=" * 30))
    logger.info(f"Successfully registered: {len(registered_prompts)} prompts")
    logger.info(f"Failed modules: {len(failed_modules)} - {failed_modules}")
    logger.info(f"Skipped modules: {len(skipped_modules)} - {skipped_modules}")

    if registered_prompts:
        logger.info(f"Registered prompts: {registered_prompts}")

    logger.info("=" * 60)

    return registered_prompts


def get_available_prompts() -> List[str]:
    return _discover_prompt_modules()
