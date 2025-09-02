import logging
from typing import Optional, Dict, Any, List
from mcp_server.utils.kdbai import get_kdbai_client, get_table
from mcp_server.server import app_settings

db_config = app_settings.db
logger = logging.getLogger(__name__)


async def list_tables_impl(database_name: Optional[str] = None) -> List[str]:
    try:
        if database_name is None:
            database_name = db_config.database_name
        client = get_kdbai_client()
        db = client.database(database_name)
        tables = [table.name for table in db.tables]
        return {'database': database_name, 'tables': tables}
    except Exception as e:
        logger.error(f"Error listing tables in database {database_name}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "database": database_name
        }


async def kdbai_table_info_impl(table_name: str, database_name: Optional[str] = None) -> Dict[str, Any]:
    """
        Get comprehensive information about a table including schema and statistics.
        Check function kdbai_info_table for details
    """
    try:
        if database_name is None:
            database_name = db_config.database_name

        client = get_kdbai_client()
        table = client.database(database_name).table(table_name)
        data = table.info()
        data['schema'] = table.schema
        if len(table.indexes) > 0:
            data['indexes'] = table.indexes
        return data
    except Exception as e:
        logger.error(f"Error getting table info for {table_name}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "database": database_name
        }


def register_tools(mcp_server):
    @mcp_server.tool()
    async def kdbai_list_tables(database_name: Optional[str] = None) -> Dict[str, Any]:
        """
        List all tables in the given database.

        Args:
            database_name: Name of the database (optional:defaults to configured database)

        Returns:
            A dictionary with following details:
            database: name of database
            tables: list of tables in the mentioned database
        """
        return await list_tables_impl(database_name)

    @mcp_server.tool()
    async def kdbai_table_info(table_name: str, database_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive information about a table including schema and statistics.

        Args:
            table_name: Name of the table
            database_name: Name of the database (defaults to configured database)

        Returns:
            Dictionary containing table information and metadata as below.
            name: table name
            database: database name
            disk: disk size used by table in MB
            rowCount: total number of rows in the table
            schema: table schema as list of dictionary. Each item as column name and column type.
            indexes: table indexes as list of dictionary. Each entry is one index information.
        """
        return await kdbai_table_info_impl(table_name, database_name)

    return [
        "kdbai_list_tables",
        "kdbai_table_info",
    ]
