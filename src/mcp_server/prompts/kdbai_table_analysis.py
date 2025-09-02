import logging
from typing import Optional, List, Dict, Any, Literal
logger = logging.getLogger(__name__)

async def kdbai_table_analysis_prompt_impl(
    table_name: str,
    analysis_type: str = "overview",
    sample_size: int = 10
) -> str:
    """
    Generate a concise analysis prompt for a KDB.AI text table.
    
    Args:
        table_name: Name of the KDB.AI table to analyze
        analysis_type: Type of analysis (overview, content, quality, search)
        sample_size: Number of records to examine
        
    Returns:
        str: The generated analysis prompt
    """

    valid_types = ["overview", "content", "quality", "search"]

    analysis_focus = {
        "overview": """
        Focus on table overview:
            - table structure (schema, columns, indexes)
            - content types (documents, length patterns)
            - basic statistics (row count, memory usage)
            - overall data characteristics
            """,
        "content": """
        Focus on content analysis:
            - text themes and topics
            - document types and formats
            - content patterns (language, style, complexity)
            - temporal distribution
            - subject matter coverage
            """, 
        "quality": """
        Focus on data quality assessment:
            - data completeness (missing fields, null values)
            - duplicate detection (identical/similar content)
            - text formatting issues (encoding, truncation, corruption)
            - metadata consistency
            """,
        "search": """
        Focus on search optimization:
            - similarity search effectiveness (relevance quality)
            - optimal query strategies (keywords vs phrases)
            - distance threshold analysis
            - embedding performance assessment
            """
    }
    try:
        
        if analysis_type not in valid_types:
            logger.warning(f"Invalid analysis type '{analysis_type}' provided. Defaulting to 'overview'.")
            analysis_type = "overview"
        
        focus = analysis_focus[analysis_type]
        
        prompt = f"""
    You are a data analyst conducting an in-depth analysis of the KDB.AI table: {table_name}
    First, examine the table structure and sample data to understand its content and characteristics.
    Use the available KDB.AI tools to get detailed information about this table.

    {focus.strip()}

    Structure your analysis as follows:
    1. **Table Overview**:
    - Business purpose and context of this table
    - Key entity or concept it represents per column
    - Total record count and data volume
    2. **Data Profile**:
    - Sample data examination ({sample_size} records)
    - Text content patterns and characteristics
    - Metadata field analysis
    3. **Search Performance Analysis**:
    - Test 3-5 similarity searches with different queries
    - Distance threshold effectiveness
    - Query strategy recommendations

    Focus on actionable insights that would help someone understand and effectively use this KDB.AI table for text search and retrieval.

    Table to analyze: {table_name}
    Analysis type: {analysis_type}
            """.strip()
        
        logger.info(f"Generated concise analysis prompt for {table_name}")
        return prompt
        
    except Exception as e:
        logger.error(f"Error generating analysis prompt: {e}")
        return f"Error: {str(e)}"

def register_prompts(mcp_server):
    @mcp_server.prompt()
    async def kdbai_table_analysis(
        table_name: str,
        analysis_type: Literal["overview", "content", "quality", "search", ""] = "overview",
        sample_size: int = 10
    ) -> str:
        """
        Conduct detailed analysis of a specific table.
        Analysis_type Options: overview, content, quality, search.
        """
        return await kdbai_table_analysis_prompt_impl(table_name, analysis_type, sample_size)
    return ['kdbai_table_analysis']
