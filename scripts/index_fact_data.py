"""Script to chunk and index fact data markdown files into a RAG system."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from adsp.data_pipeline.fact_data_pipeline.rag import run_fact_data_indexing_pipeline
from adsp.data_pipeline.fact_data_pipeline.extract_raw.config import FactDataExtractionConfig
from adsp.data_pipeline.fact_data_pipeline.rag import documents_to_context_prompt

def main():
    """Chunk and index fact data markdown files."""
    parser = argparse.ArgumentParser(
        description="Chunk and index fact data markdown files for RAG retrieval."
    )
    parser.add_argument(
        "--markdown-dir",
        type=str,
        default=None,
        help="Directory containing markdown files (default: from config)",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="sentence-transformers/all-mpnet-base-v2",
        help="HuggingFace embedding model name",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1200,
        help="Maximum chunk size in characters (default: 1200)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlap between chunks in characters (default: 50)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="page_*.md",
        help="Glob pattern for markdown files (default: page_*.md)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of results to return for test query (default: 10)",
    )
    parser.add_argument(
        "--test-query",
        type=bool,
        default=True,
        help="Whether to run test queries after indexing (default: True)"
    )
    
    args = parser.parse_args()
    
    # Determine markdown directory
    if args.markdown_dir:
        markdown_dir = Path(args.markdown_dir)
    else:
        config = FactDataExtractionConfig()
        markdown_dir = config.fact_data_output_dir / "pages"
    
    if not markdown_dir.exists():
        logger.error(f"Markdown directory not found: {markdown_dir}")
        return 1
    
    # Run the indexing pipeline
    try:
        rag = run_fact_data_indexing_pipeline(
            markdown_dir=markdown_dir,
            embedding_model_name=args.embedding_model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            pattern=args.pattern,
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    if args.test_query:
        queries = [
            "What are the demographics of Curious Connoisseurs?",
            "What coffee brands do they prefer?",
            "Tell me about their lifestyle and interests",
        ]

        for query in queries:
            print(f"\nQuery: {query}")
            print("=" * 60)
            
            # Search for relevant chunks
            results = rag.search(query, k=10)
            
            # Convert to context prompt format
            context = documents_to_context_prompt(results)
            
            print(f"\nRetrieved {len(results)} relevant chunks:\n")
            print(context)
            print("\n" + "=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
