"""Script to convert JSON page files to Markdown format."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from adsp.data_pipeline.fact_data_pipeline.extract_raw import run_json_to_markdown_conversion
from adsp.data_pipeline.fact_data_pipeline.extract_raw.config import FactDataExtractionConfig
from loguru import logger


def main():
    """Run the JSON to Markdown conversion."""
    logger.info("Starting JSON to Markdown conversion...")
    
    # Use paths from config
    config = FactDataExtractionConfig()
    input_dir = config.raw_responses_dir
    output_dir = config.fact_data_output_dir / "pages"
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    converted = run_json_to_markdown_conversion(input_dir, output_dir)
    
    logger.success(f"Conversion complete: {converted} files converted successfully.")
    return 0 if converted > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
