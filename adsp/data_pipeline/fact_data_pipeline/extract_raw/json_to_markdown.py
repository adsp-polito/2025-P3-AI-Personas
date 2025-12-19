"""Transform JSON page files to Markdown format."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


class JSONToMarkdownConverter:
    """Converts structured JSON page data to Markdown format."""

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
    ):
        """
        Initialize the converter.
        
        Args:
            input_dir: Directory containing JSON files (data/interim/fact_data_extraction/pages)
            output_dir: Directory to store markdown files (data/processed/fact_data/pages)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _yaml_safe_string(value: Any) -> str:
        """Convert a value to a YAML-safe string, quoting if necessary."""
        if value is None:
            return ""
        str_value = str(value)
        # Check if the string needs quoting (contains YAML special characters)
        # Key characters: : (colon), # (comment), [ ] { } (collections), quotes, etc.
        needs_quoting = any(char in str_value for char in [':', '#', '[', ']', '{', '}', '&', '*', '!', '|', '>', "'", '"', '%', '@', '`'])
        
        if needs_quoting:
            # Escape any existing single quotes and wrap in single quotes
            escaped = str_value.replace("'", "''")
            return f"'{escaped}'"
        return str_value
    
    def convert_element_to_markdown(self, element: Dict[str, Any]) -> str:
        """
        Convert a single element to markdown based on its type and hints.
        
        Args:
            element: Element dictionary from JSON
            
        Returns:
            Markdown string representation of the element
        """
        element_type = element.get("element_type", "")
        normalized_text = element.get("normalized_text", "")
        raw_text = element.get("raw_text", "")
        structured_content = element.get("structured_content")
        markdown_hint = element.get("markdown_hint", {})
        preferred_block = markdown_hint.get("preferred_block", "paragraph")
        
        # Use normalized text if available, otherwise raw text
        text = normalized_text or raw_text or ""
        
        # Convert based on element type and preferred block type
        # Handle bullet_list and numbered_list explicitly
        if element_type in ("bullet_list", "numbered_list"):
            if structured_content:
                # Check if list has table structure (common in this dataset)
                if "table" in structured_content:
                    return self._format_table(structured_content["table"]) + "\n\n"
                # Check for list structure
                elif "list" in structured_content:
                    list_type = "ordered" if element_type == "numbered_list" else "unordered"
                    return self._format_list(structured_content["list"], list_type) + "\n\n"
            # Fallback: treat text as list items
            if text:
                return f"- {text}\n\n"
            return ""
        
        # Handle chart types (bar_chart, line_chart, pie_chart) via plot structure
        if element_type in ("bar_chart", "line_chart", "pie_chart", "plot"):
            if structured_content and "plot" in structured_content:
                return self._format_plot(structured_content["plot"], text) + "\n\n"
            # Fallback if no structured content
            if text:
                return f"**{text}**\n\n"
            return ""
        
        # Handle donut_chart explicitly
        if element_type == "donut_chart":
            if structured_content and "donut_chart" in structured_content:
                return self._format_donut_chart(structured_content["donut_chart"], text) + "\n\n"
            # Fallback if no structured content
            if text:
                return f"**{text}**\n\n"
            return ""
        
        # Convert based on preferred block type
        if preferred_block == "heading":
            if element_type == "title":
                return f"# {text}\n\n"
            elif element_type == "subheading":
                return f"## {text}\n\n"
            else:
                return f"### {text}\n\n"
        
        elif preferred_block == "image" and structured_content:
            # Check for plots and charts first
            if "plot" in structured_content:
                return self._format_plot(structured_content["plot"], text) + "\n\n"
            elif "donut_chart" in structured_content:
                return self._format_donut_chart(structured_content["donut_chart"], text) + "\n\n"
            
            # Handle regular image elements with structured content
            image_data = structured_content.get("image", {})
            caption = image_data.get("long_caption", "")
            # objects = image_data.get("detected_objects", [])
            
            markdown = ""
            if text:
                markdown += f"**{text}**\n\n"
            if caption:
                markdown += f"*{caption}*\n\n"
            # if objects:
            #     objects_str = ", ".join(objects)
            #     markdown += f"*(Detected objects: {objects_str})*\n\n"
            return markdown
        
        elif preferred_block == "table" and structured_content:
            # Handle table elements
            table_data = structured_content.get("table", {})
            if table_data:
                return self._format_table(table_data) + "\n\n"
            return ""
        
        elif preferred_block == "list" and structured_content:
            # Handle list elements
            list_data = structured_content.get("list", {})
            if list_data:
                return self._format_list(list_data) + "\n\n"
            return text + "\n\n" if text else ""
        
        else:
            # Default case: check for structured content even if preferred_block suggests paragraph
            if structured_content:
                # Check for table in structured content
                if "table" in structured_content:
                    return self._format_table(structured_content["table"]) + "\n\n"
                # Check for plot in structured content
                elif "plot" in structured_content:
                    return self._format_plot(structured_content["plot"], text) + "\n\n"
                # Check for donut_chart in structured content
                elif "donut_chart" in structured_content:
                    return self._format_donut_chart(structured_content["donut_chart"], text) + "\n\n"
                # Check for list in structured content
                elif "list" in structured_content:
                    return self._format_list(structured_content["list"]) + "\n\n"

            # Special formatting for specific element types
            if element_type == "logo":
                # Logos get bolded text
                if text:
                    return f"**{text}**\n\n"
                return ""
            elif element_type == "caption":
                # Captions get italicized
                if text:
                    return f"*{text}*\n\n"
                return ""
            elif element_type == "text_box":
                # Text boxes get formatted distinctly
                if text:
                    return f"text_box: {text}\n\n"
                return ""
            elif element_type in ("footer", "header", "page_number"):
                # Metadata elements get simple formatting
                if text:
                    return f"{element_type}: {text}\n\n"
                return ""
            elif element_type == "legend":
                # Legends are typically part of plots, but if standalone, format as list
                if text:
                    return f"*Legend: {text}*\n\n"
                return ""
            
            # Generic fallback for paragraph, misc, and unknown types
            if text:
                return f"{element_type}: {text}\n\n"
            return ""
    
    def _format_table(self, table_data: Dict[str, Any]) -> str:
        """Format table data as markdown table."""
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        table_title = table_data.get("table_title", "")
        
        if not headers or not rows:
            return ""
        
        markdown = ""
        
        # Add table title if present
        if table_title:
            markdown += f"**{table_title}**\n\n"
        
        # Extract header names (headers can be strings or dicts with 'name' field)
        header_names = []
        for header in headers:
            if isinstance(header, dict):
                name = header.get("name", "")
                unit = header.get("unit")
                if unit:
                    header_names.append(f"{name} ({unit})")
                else:
                    header_names.append(name)
            else:
                header_names.append(str(header))
        
        # Create header row
        markdown += "| " + " | ".join(header_names) + " |\n"
        # Create separator row
        markdown += "| " + " | ".join(["---"] * len(header_names)) + " |\n"
        
        # Create data rows (each cell can be a string or dict with 'value' field)
        for row in rows:
            cell_values = []
            for cell in row:
                if isinstance(cell, dict):
                    value = cell.get("value", "")
                    unit = cell.get("unit")
                    index = cell.get("index")
                    # Format cell with value and optionally unit/index
                    cell_str = str(value)
                    if unit and unit != "%":  # Don't add unit if it's already in header
                        cell_str += f" {unit}"
                    if index is not None:
                        cell_str += f" (idx: {index})"
                    cell_values.append(cell_str)
                else:
                    cell_values.append(str(cell))
            markdown += "| " + " | ".join(cell_values) + " |\n"
        
        # Add table notes if present
        notes = table_data.get("notes")
        if notes:
            markdown += f"\n*{notes}*\n"
        
        return markdown
    
    def _format_list(self, list_data: Dict[str, Any], list_type: Optional[str] = None) -> str:
        """Format list data as markdown list."""
        # Handle both old format (dict with "items" key) and new format (direct array)
        if isinstance(list_data, list):
            # list_data is directly an array
            items = list_data
            list_title = ""
        else:
            # list_data is a dict with "items", "type", "title" keys
            items = list_data.get("items", [])
            if list_type is None:
                list_type = list_data.get("type", "unordered")
            list_title = list_data.get("title", "")
        
        if not items:
            return ""
        
        markdown = ""
        
        # Add list title if present
        if list_title:
            markdown += f"**{list_title}**\n\n"
        
        for idx, item in enumerate(items, 1):
            # Handle both string items and dict items with 'text', 'value', or 'item' field
            if isinstance(item, dict):
                item_text = item.get("text") or item.get("value") or item.get("item") or str(item)
            else:
                item_text = str(item)
                
            if list_type == "ordered":
                markdown += f"{idx}. {item_text}\n"
            else:
                markdown += f"- {item_text}\n"
        
        return markdown
    
    def _format_plot(self, plot_data: Dict[str, Any], element_text: str = "") -> str:
        """Format plot/chart data as markdown."""
        plot_type = plot_data.get("plot_type", "chart")
        title = plot_data.get("title", "")
        caption = plot_data.get("caption", "")
        data_series = plot_data.get("data_series", [])
        notes = plot_data.get("notes", "")
        
        markdown = ""
        
        # Add plot title
        if title:
            markdown += f"### {title}\n\n"
        elif element_text:
            markdown += f"### {element_text}\n\n"
        
        markdown += f"**{plot_type.replace('_', ' ').title()}**\n\n"

        if caption:
            markdown += f"*{caption}*\n\n"
        
        # Format data series
        if data_series:
            for series in data_series:
                series_label = series.get("series_label", "")
                data_points = series.get("data_points", [])
                
                if series_label:
                    markdown += f"**{series_label}:**\n\n"
                
                # Create a simple table for data points
                if data_points:
                    # Check if we have consistent structure
                    has_category = any(isinstance(dp, dict) and dp.get("category") for dp in data_points)
                    
                    if has_category:
                        markdown += "| Category | Value |\n"
                        markdown += "| --- | --- |\n"
                        for dp in data_points:
                            if isinstance(dp, dict):
                                category = dp.get("category", "")
                                value = dp.get("value", "")
                                index = dp.get("index")
                                if index is not None:
                                    markdown += f"| {category} | {value} (idx: {index}) |\n"
                                else:
                                    markdown += f"| {category} | {value} |\n"
                        markdown += "\n"
                    else:
                        # Just list values
                        for dp in data_points:
                            if isinstance(dp, dict):
                                markdown += f"- {dp.get('value', dp)}\n"
                            else:
                                markdown += f"- {dp}\n"
                        markdown += "\n"
        
        # Add notes if present
        if notes:
            markdown += f"*{notes}*\n"
        
        return markdown
    
    def _format_donut_chart(self, donut_data: Dict[str, Any], element_text: str = "") -> str:
        """Format donut chart data as markdown."""
        slices = donut_data.get("slices", [])
        caption = donut_data.get("caption", "")
        
        markdown = ""
        
        # Add title
        if element_text:
            markdown += f"### {element_text}\n\n"
        
        markdown += "**Donut Chart**\n\n"
        
        if caption:
            markdown += f"*{caption}*\n\n"
        
        # Create table for slices
        if slices:
            markdown += "| Category | Value | Index |\n"
            markdown += "| --- | --- | --- |\n"
            
            # Sort slices by order
            sorted_slices = sorted(slices, key=lambda s: s.get("order", 0))
            
            for slice_data in sorted_slices:
                label = slice_data.get("legend_label", "")
                value = slice_data.get("value", "")
                index = slice_data.get("index", "")
                markdown += f"| {label} | {value} | {index} |\n"
            
            markdown += "\n"
        
        return markdown
    
    def convert_page_to_markdown(self, json_data: Dict[str, Any]) -> str:
        """
        Convert a complete page JSON to markdown.
        
        Args:
            json_data: Complete page JSON data
            
        Returns:
            Markdown string representation of the page
        """
        parsed = json_data.get("parsed", {})
        if not parsed:
            logger.warning(f"No parsed data found in JSON")
            return ""
        
        page_number = parsed.get("page_number", 0)
        page_metadata = parsed.get("page_metadata", {})
        elements = parsed.get("elements", [])
        page_notes = parsed.get("page_notes", "")
        segment = parsed.get("segment", {})
        
        # Start building markdown
        markdown_parts: List[str] = []
        
        # Add page header with metadata
        markdown_parts.append("---\n")
        markdown_parts.append(f"page: {page_number}\n")
        
        if page_metadata.get("section_title"):
            section = self._yaml_safe_string(page_metadata['section_title'])
            markdown_parts.append(f"section: {section}\n")
        if page_metadata.get("subsection_title"):
            subsection = self._yaml_safe_string(page_metadata['subsection_title'])
            markdown_parts.append(f"subsection: {subsection}\n")
        if page_metadata.get("template_type"):
            template = self._yaml_safe_string(page_metadata['template_type'])
            markdown_parts.append(f"template: {template}\n")
        if segment.get("segment_name"):
            segment_name = self._yaml_safe_string(segment['segment_name'])
            markdown_parts.append(f"segment: {segment_name}\n")
        
        markdown_parts.append("---\n\n")
        
        # Convert elements in reading order
        sorted_elements = sorted(elements, key=lambda e: e.get("reading_order", 0))
        
        for element in sorted_elements:
            element_md = self.convert_element_to_markdown(element)
            if element_md:
                markdown_parts.append(element_md)
        
        # Add page notes at the end if available
        if page_notes:
            markdown_parts.append(f"---\n\n*Page Notes: {page_notes}*\n")
        
        return "".join(markdown_parts)
    
    def convert_file(self, json_path: Path) -> Optional[Path]:
        """
        Convert a single JSON file to markdown.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            Path to the created markdown file, or None if conversion failed
        """
        try:
            # Read JSON file
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
            
            # Convert to markdown
            markdown_content = self.convert_page_to_markdown(json_data)
            
            # Create output filename (replace .json with .md)
            output_filename = json_path.stem + ".md"
            output_path = self.output_dir / output_filename
            
            # Write markdown file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            logger.info(f"Converted {json_path.name} -> {output_path.name}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert {json_path.name}: {e}")
            return None
    
    def convert_all(self) -> int:
        """
        Convert all JSON files in the input directory to markdown.
        
        Returns:
            Number of files successfully converted
        """
        json_files = sorted(self.input_dir.glob("page_*.json"))
        
        if not json_files:
            logger.warning(f"No JSON files found in {self.input_dir}")
            return 0
        
        logger.info(f"Found {len(json_files)} JSON files to convert")
        
        converted_count = 0
        for json_file in json_files:
            if self.convert_file(json_file):
                converted_count += 1
        
        logger.info(f"Successfully converted {converted_count}/{len(json_files)} files")
        return converted_count


def run_json_to_markdown_conversion(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> int:
    """
    Run the JSON to Markdown conversion pipeline.
    
    Args:
        input_dir: Input directory with JSON files. Defaults to data/interim/fact_data_extraction/pages
        output_dir: Output directory for markdown files. Defaults to data/processed/fact_data/pages
        
    Returns:
        Number of files successfully converted
    """
    # Set default paths relative to project root
    if input_dir is None:
        input_dir = Path("data/interim/fact_data_extraction/pages")
    if output_dir is None:
        output_dir = Path("data/processed/fact_data/pages")
    
    converter = JSONToMarkdownConverter(input_dir, output_dir)
    return converter.convert_all()


if __name__ == "__main__":
    # Run conversion with default paths
    converted = run_json_to_markdown_conversion()
    print(f"Conversion complete: {converted} files converted")
