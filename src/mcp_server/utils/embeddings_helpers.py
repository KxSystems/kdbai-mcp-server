from mcp_server.server import app_settings
import pandas as pd
from functools import lru_cache
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@lru_cache()
def get_csv_data(csv_path: str):
    return pd.read_csv(csv_path)

def get_embedding_config(
    database: str, 
    table: str, 
) -> List[Optional[str]]:
    """
    Get embedding or sparse tokenizer configuration for a specific database/table.
    
    Args:
        database: Database name to match
        table: Table name to match
        
    Returns:
        List[Optional[str]]: [provider, model] based on config_type
    """
    # Filter rows where both database and table match
    df = get_csv_data(app_settings.db.embedding_csv_path)
    mask = (df['database'] == database) & (df['table'] == table)
    matching_rows = df[mask]
    
    if len(matching_rows) == 0:
        logger.error(f"No configuration found for database='{database}', table='{table}'")
        return [None, None, None, None]
    elif len(matching_rows) > 1:
        logger.error(f"Warning: Multiple configurations found for database='{database}', table='{table}'. Using first match.")
        return [None, None, None, None]

    # Get the first matching row
    row = matching_rows.iloc[0]
    
    # Choose columns based on config_type flag
    return [row['embedding_provider'], row['embedding_model'], row['sparse_tokenizer_provider'], row['sparse_tokenizer_model']]