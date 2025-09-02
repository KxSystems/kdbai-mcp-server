import logging
from typing import Optional, Dict, Any, List
from mcp_server.utils.embeddings import get_provider
from mcp_server.utils.embeddings_helpers import get_embedding_config
from mcp_server.utils.kdbai import get_table
from mcp_server.utils.filters import parse_temporal_filters
from mcp_server.server import app_settings
import numpy as np
import pandas as pd

db_config = app_settings.db
logger = logging.getLogger(__name__)

# Normalizes the result from query and search operations
def normalize_result(df: Dict, table)-> Any:
    # Remove embedding columns if they exist
    if table.indexes:
        embedding_columns = {t['column'] for t in table.indexes}
        df = df.drop(columns=embedding_columns, errors='ignore')
    # serialize numpy ndarray type (emedding columns)
    df = df.map(lambda x: x.tolist() if isinstance(x, np.ndarray) else x)
    # convert timespan type (KDB time type)
    for col_name, col_type in df.dtypes.items():
        timespan_type = str(col_type).lower().startswith("timedelta")
        duration_type = str(col_type).lower().startswith("duration")
        if timespan_type or duration_type:
            df[col_name] = (pd.Timestamp("1970-01-01") + df[col_name]).dt.time
        # convert to dict
    return df.to_dict('records') if hasattr(df, 'to_dict') else df
    
async def kdbai_query_data_impl(table_name: str,
                                database_name: Optional[str] = None,
                                filters: Optional[List[tuple]] = None,
                                sort_columns: Optional[List[str]] = None,
                                group_by: Optional[List[str]] = None,
                                aggs: Optional[Dict[str, Any]] = None,
                                limit: Optional[int] = None) -> Dict[str, Any]:
    try:
        if database_name is None:
            database_name = db_config.database_name

        table = get_table(table_name, database_name)

        # Build query parameters efficiently
        query_params = {k: v for k, v in {
            'filter': parse_temporal_filters(filters,table.schema),
            'sort_columns': sort_columns,
            'group_by': group_by,
            'aggs': aggs,
            'limit': limit
        }.items() if v is not None}

        result = table.query(**query_params)
        result = normalize_result(result, table)
        return {
            "status": "success",
            "database": database_name,
            "table": table_name,
            "recordsCount": len(result),
            "records": result
        }

    except Exception as e:
        logger.error(f"Error executing query on table {table_name}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "database": database_name,
            "table": table_name
        }


async def kdbai_similarity_search_impl( table_name: str,
                                        query: str,
                                        vector_index_name: str,
                                        database_name: Optional[str] = None,
                                        n: Optional[int] = None,
                                        filters: Optional[List[tuple]] = None,
                                        sort_columns: Optional[List[str]] = None,
                                        group_by: Optional[List[str]] = None,
                                        aggs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

    try:
        if database_name is None:
            database_name = db_config.database_name
        if n is None:
            n = db_config.k

        embeddings_provider, embeddings_model, _, _ = get_embedding_config(database_name, table_name)
        
        dense_provider = get_provider(embeddings_provider)
        query_vector = await dense_provider.dense_embed(query, embeddings_model)
        table = get_table(table_name, database_name)

        # Build search parameters efficiently
        search_params = {
            "vectors": {vector_index_name: [query_vector]},
            "n": int(n),
            **{k: v for k, v in {
                'filter': parse_temporal_filters(filters,table.schema),
                'sort_columns': sort_columns,
                'group_by': group_by,
                'aggs': aggs
            }.items() if v is not None}
        }

        result = table.search(**search_params)[0]
        result = normalize_result(result, table)

        return {
            "status": "success",
            "database": database_name,
            "table": table_name,
            "recordsCount": len(result),
            "records": result
        }
    except Exception as e:
        logger.error(f"Error performing search on table {table_name}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "database": database_name,
            "table": table_name,
        }


async def kdbai_hybrid_search_impl(table_name: str,
                                    query: str,
                                    vector_index_name: str,
                                    sparse_index_name: str,
                                    database_name: Optional[str] = None,
                                    n: Optional[int] = None,
                                    filters: Optional[List[tuple]] = None,
                                    sort_columns: Optional[List[str]] = None,
                                    group_by: Optional[List[str]] = None,
                                    aggs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        if database_name is None:
            database_name = db_config.database_name
        if n is None:
            n = db_config.k

        table = get_table(table_name, database_name)

        embeddings_provider, embeddings_model, sparse_tokenizer_provider, sparse_tokenizer_model = get_embedding_config(database_name, table_name)

        dense_provider = get_provider(embeddings_provider)
        sparse_provider = dense_provider if embeddings_provider==sparse_tokenizer_provider else  get_provider(sparse_tokenizer_provider)
        query_vector = await dense_provider.dense_embed(query, embeddings_model)
        query_sparse = await sparse_provider.sparse_embed(query, sparse_tokenizer_model)

        search_params = {
            "vectors": {
                vector_index_name: [query_vector],
                sparse_index_name: [query_sparse],
            },
            "n": int(n),
            "index_params": {
                vector_index_name: {"weight": db_config.vector_weight},
                sparse_index_name: {"weight": db_config.sparse_weight},
            },
            **{k: v for k, v in {
                'filter': parse_temporal_filters(filters,table.schema),
                'sort_columns': sort_columns,
                'group_by': group_by,
                'aggs': aggs
            }.items() if v is not None}
        }

        result = table.search(**search_params)[0]
        result = normalize_result(result, table)
        return {
            "status": "success",
            "database": database_name,
            "table": table_name,
            "recordsCount": len(result),
            "records": result
        }
    except Exception as e:
        logger.error(f"Error performing hybrid search on table {table_name}: {e}")
        return {
            "status": "error",
            "message": str(e),
            "database": database_name,
            "table": table_name,
        }


def register_tools(mcp_server):
    @mcp_server.tool()
    async def kdbai_query_data(table_name: str,
                                database_name: Optional[str] = None,
                                filters: Optional[List[tuple]] = None,
                                sort_columns: Optional[List[str]] = None,
                                group_by: Optional[List[str]] = None,
                                aggs: Optional[Dict[str, Any]] = None,
                                limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Query data from a KDBAI table with support for filtering, sorting, grouping,limit and aggregation.
        It removes the embedding columns from the output.

        For query syntax and examples, see: file://kdbai_operations_guidance

        Args:
            database_name: Name of the database containing the table.
            table_name: Name of the table to query
            filters: List of filter conditions as q/kdb+ parse tree (operator, filter column name, value)
            Examples:
                - Simple equality: ("=", "filter_column_name", "value")
                - Logical AND: [("<", "filter_column_name_1", "value"), (">", "filter_column_name_2", "value")]
            sort_columns: List of column names to sort by, e.g. '["price", "date"]'
            group_by: List of column names to group by, e.g. '["category"]'
            aggs: Dictionary of aggregation rules, e.g. '{"total": ["sum", "amount"]}'. It can use any KDB+ supported aggregation function like avg, max, sum etc.
            limit: String representation of maximum number of rows to return, e.g. "10"

        Returns:
            Dictionary containing query results or error message

        """
        results = await kdbai_query_data_impl(
            table_name, 
            database_name, 
            filters, 
            sort_columns, 
            group_by, 
            aggs, 
            limit
        )
        return results

    @mcp_server.tool()
    async def kdbai_similarity_search(table_name: str,
                            query: str,
                            vector_index_name: str,
                            database_name: Optional[str] = None,
                            n: Optional[int] = None,
                            filters: Optional[List[tuple]] = None,
                            sort_columns: Optional[List[str]] = None,
                            group_by: Optional[List[str]] = None,
                            aggs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform vector similarity search on a KDB.AI table.
        For search syntax and examples, see: file://kdbai_operations_guidance

        Args:
            table_name: Name of the table to search
            query: Text query to convert to vector and search
            vector_index_name: Name of the vector index to search against
            embeddings_provider: Embedding provider ('sentence_transformers', 'openai', etc.)
            embeddings_model: Specific embedding model to use
            database (Optional[str], optional): Name of the database
            n (Optional[int], optional): Number of results to return
            filters (Optional[List[tuple]], optional): List of filter conditions as q/kdb+ parse tree (operator, filter column name, value).
                - Filters Examples:
                 - Simple equality: ("=", "filter_column_name", "value")
                 - Logical AND: [("<", "filter_column_name_1", "value"), (">", "filter_column_name_2", "value")]
            sort_columns: List of column names to sort by, e.g. '["price", "date"]'
            group_by: List of column names to group by, e.g. '["category"]'
            aggs: Dictionary of aggregation rules, e.g. '{"total": ["sum", "amount"]}'. It can use any KDB+ supported aggregation function like avg, max, sum etc.
            limit: String representation of maximum number of rows to return, e.g. "10"

        Returns:
            Dictionary containing search result.
        """
        results = await kdbai_similarity_search_impl(
            table_name,
            query, 
            vector_index_name, 
            database_name, 
            n, 
            filters, 
            sort_columns, 
            group_by, 
            aggs
        )
        return results

    @mcp_server.tool()
    async def kdbai_hybrid_search(table_name: str,
                                    query: str,
                                    vector_index_name: str,
                                    sparse_index_name: str,
                                    database_name: Optional[str] = None,
                                    n: Optional[int] = None,
                                    filters: Optional[List[tuple]] = None,
                                    sort_columns: Optional[List[str]] = None,
                                    group_by: Optional[List[str]] = None,
                                    aggs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Performs hybrid search on a KDB.AI table by combining vector and text(sparse) search on a KDB.AI table.
        For search syntax and examples, see: file://kdbai_operations_guidance

        Args:
            table_name: Name of the table to search
            query: Text query for both vector and text or sparse search
            vector_index_name: Name of the vector index for similarity search
            sparse_index_name: Name of the sparse index for text search
            embeddings_provider: Embedding provider ('sentence_transformers', 'openai', etc.)
            embeddings_model: Specific embedding model to use
            sparse_tokenizer_provider: Tokenizer provider ('sentence_transformers', 'openai', etc.)
            sparse_tokenizer_model: Specific tokenizer model to use            
            database (Optional[str], optional): Name of the database
            n (Optional[int], optional): Number of results to return
            filters (Optional[List[tuple]], optional): List of filter conditions as q/kdb+ parse tree (operator, filter column name, value).
                - Filters Examples:
                 - Simple equality: ("=", "filter_column_name", "value")
                 - Logical AND: [("<", "filter_column_name_1", "value"), (">", "filter_column_name_2", "value")]
            sort_columns: List of column names to sort by, e.g. '["price", "date"]'
            group_by: List of column names to group by, e.g. '["category"]'
            aggs: Dictionary of aggregation rules, e.g. '{"total": ["sum", "amount"]}'. It can use any KDB+ supported aggregation function like avg, max, sum etc.

        Returns:
            Dictionary containing hybrid search result.
        """
        results = await kdbai_hybrid_search_impl(
            table_name,
            query,
            vector_index_name,
            sparse_index_name,
            database_name,
            n,
            filters,
            sort_columns,
            group_by,
            aggs
        )
        return results

    return ["kdbai_query_data", "kdbai_similarity_search", "kdbai_hybrid_search"]
