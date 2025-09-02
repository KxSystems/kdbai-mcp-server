import logging
from typing import Optional, Dict, Any
from mcp_server.utils.kdbai import get_kdbai_client
from mcp_server.server import app_settings

db_config = app_settings.db
logger = logging.getLogger(__name__)

async def kdbai_list_databases_impl() -> Dict[str, Any]:
    try:
        client = get_kdbai_client()
        return {
            "status": "success",
            "databases": [db.name for db in client.databases()]
        }
    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

async def kdbai_databases_info_impl(database: Optional[str] = None) -> Dict[str, Any]:
    try:
        client = get_kdbai_client()
        if database is None: # all database info
            info = client.databases_info()
        else:  # specific database info
            info = client.database(database).info()
        return {
            "status": "success",
            "info": info
        }
    except Exception as e:
        logger.error(f"Error in getting database info: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def register_tools(mcp_server):
    @mcp_server.tool()
    async def kdbai_list_databases() -> Dict[str, Any]:
        """
        List all databases name in the KDB.AI database.

        Returns:
            A dictionary with following data:
            status: 'success' for successfull execution , 'error' if function fails
            databases: list of databases names
        """
        return await kdbai_list_databases_impl()

    @mcp_server.tool()
    async def kdbai_database_info(database: Optional[str] = "default") -> Dict[str, Any]:
        """
        Get KDBAI database information. Database information also includes tables information for each table in the database.

        Args:
            database (Optional[str], optional): Name of the database. If not given then uses 'default' database.

        Returns:
            A dictionary with following data:
                status: 'success' for successfull execution , 'error' if function fails
                info: dictionary containing database information.
                    - The dictionary has a key 'tables' which maps to a list of dictionaries.
                    - Each dictionary in this list represents a single table, and holds its corresponding information (eg: name,rowCount).
        """
        info = await kdbai_databases_info_impl(database)
        return info

    @mcp_server.tool()
    async def kdbai_all_databases_info() -> Dict[str, Any]:
        """
        Get information of all databases in KDBAI database. Each database entry includes tables information of each table in that database.

        Returns:
            A dictionary with following data:
                status: 'success' for successfull execution , 'error' if function fails
                info: dictionary that has information of all databases.
                    - The dictionary has a key 'databases' which maps to a list of dictionaries.
                    - Each dictionary in this list represents a single database, and holds its corresponding information (eg: tableCount, tables).
        """
        info = await kdbai_databases_info_impl()
        return info

    return [
        "kdbai_list_databases",
        "kdbai_database_info",
        "kdbai_all_databases_info",
    ]
