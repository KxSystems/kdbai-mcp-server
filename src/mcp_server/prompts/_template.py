"""
Template for creating MCP server prompts.

Prompts provide reusable, parameterized prompt templates that can be used by AI models.
They help standardize common prompt patterns and make them easily accessible.

To create a new prompt module:
1. Copy this file to a new name (without the leading underscore)
2. Implement your prompt logic in the *_impl functions
3. Update the register_prompts function with your prompt decorators
4. The module will be automatically discovered and registered

Prompt design best practices:
- Make prompts specific and actionable
- Include clear instructions and expected output format
- Use parameters to make prompts reusable
- Provide examples when helpful
- Structure output with clear sections (Executive Summary, Analysis, etc.)

Common prompt patterns:
- Analysis prompts: Analyze data and provide insights
- Comparison prompts: Compare multiple items or datasets
- Summarization prompts: Condense information into key points
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


async def example_analysis_prompt_impl(
    subject: str, focus_area: str = "general", output_format: str = "detailed"
) -> str:
    try:
        # Define focus area specific instructions
        focus_instructions = {
            "financial": """
            Focus your analysis on:
            - Financial performance metrics
            - Revenue and profitability trends
            - Cash flow and liquidity
            - Financial risks and opportunities
            """,
            "strategic": """
            Focus your analysis on:
            - Strategic positioning
            - Competitive advantages
            - Market opportunities
            - Long-term strategic risks
            """,
            "general": """
            Provide a comprehensive analysis covering:
            - Key performance indicators
            - Trends and patterns
            - Strengths and weaknesses
            - Recommendations for improvement
            """,
        }

        # Define output format instructions
        format_instructions = {
            "detailed": """
            Structure your analysis with:
            1. Executive Summary
            2. Key Findings
            3. Detailed Analysis
            4. Recommendations
            5. Conclusion
            
            Provide thorough explanations and supporting evidence for each section.
            """,
            "summary": """
            Provide a concise analysis with:
            1. Key Insights (3-5 main points)
            2. Critical Issues (if any)
            3. Top Recommendations (2-3 actionable items)
            
            Keep each section brief but informative.
            """,
            "bullet_points": """
            Present your analysis in bullet point format:
            • Key findings (5-7 points)
            • Critical issues (3-5 points)
            • Recommendations (3-5 actionable items)
            
            Use clear, concise bullet points with supporting data where relevant.
            """,
        }

        # Get instructions for the specified focus area and format
        focus_instruction = focus_instructions.get(
            focus_area, focus_instructions["general"]
        )
        format_instruction = format_instructions.get(
            output_format, format_instructions["detailed"]
        )

        # Generate the prompt
        prompt = f"""
You are an expert analyst tasked with analyzing {subject}.

{focus_instruction.strip()}

{format_instruction.strip()}

Use data and evidence to support your analysis. Be specific and actionable in your recommendations.
If you need additional information to complete the analysis, clearly state what data would be helpful.

Subject for Analysis: {subject}
Focus Area: {focus_area.replace("_", " ").title()}
Output Format: {output_format.replace("_", " ").title()}
        """.strip()

        logger.info(f"Generated analysis prompt for subject: {subject}")
        return prompt

    except Exception as e:
        logger.error(f"Error generating analysis prompt: {e}")
        return f"Error generating prompt: {str(e)}"
    

def register_prompts(mcp_server):
    @mcp_server.prompt()
    async def example_analysis(
        subject: str, focus_area: str = "general", output_format: str = "detailed"
    ) -> str:
        """
        Generate a comprehensive analysis prompt.

        Args:
            subject: The main subject to analyze
            focus_area: Specific area to focus the analysis on
            output_format: Format for the output (detailed, summary, bullet_points)

        Returns:
            str: The generated prompt text
        """
        return await example_analysis_prompt_impl(subject, focus_area, output_format)

    # Return the list of prompt names registered by this module
    return [
        "example_analysis",
    ]
