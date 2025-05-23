#!/usr/bin/env python
"""
Simple script to render a Mermaid diagram from a string or file.

This can be useful for debugging or testing Mermaid syntax.

Usage:
    uv run render_mermaid.py --string "graph TD; A-->B;"
    uv run render_mermaid.py --file diagram.mmd
"""

import argparse
import sys
from pathlib import Path

try:
    from langchain_core.runnables.graph_mermaid import draw_mermaid_png, MermaidDrawMethod
except ImportError:
    print("Error: Required dependencies not found.")
    print("Please install the required packages:")
    print("  uv add langchain-core>=0.3.0")
    sys.exit(1)


def render_mermaid(
    mermaid_syntax: str,
    output_file: str = "diagram.png",
    background_color: str = "white",
    padding: int = 10,
) -> None:
    """
    Render a Mermaid diagram from a string.
    
    Args:
        mermaid_syntax: The Mermaid diagram syntax
        output_file: Path to save the output PNG
        background_color: Background color for the diagram
        padding: Padding around the diagram in pixels
    """
    try:
        # Generate and save the PNG
        draw_mermaid_png(
            mermaid_syntax=mermaid_syntax,
            output_file_path=output_file,
            draw_method=MermaidDrawMethod.API,
            background_color=background_color,
            padding=padding,
            max_retries=3,
            retry_delay=1.0,
        )
        
        print(f"Diagram saved to {output_file}")
    except Exception as e:
        print(f"Error rendering diagram: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Render a Mermaid diagram")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--string", type=str, help="Mermaid diagram syntax as a string")
    group.add_argument("--file", type=str, help="Path to a file containing Mermaid diagram syntax")
    parser.add_argument("--output", type=str, default="diagram.png", help="Output file path")
    parser.add_argument("--bg-color", type=str, default="white", help="Background color")
    parser.add_argument("--padding", type=int, default=10, help="Padding in pixels")
    
    args = parser.parse_args()
    
    # Get the Mermaid syntax
    if args.string:
        mermaid_syntax = args.string
    else:
        try:
            with open(args.file, "r") as f:
                mermaid_syntax = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    
    # Render the diagram
    render_mermaid(
        mermaid_syntax=mermaid_syntax,
        output_file=args.output,
        background_color=args.bg_color,
        padding=args.padding,
    )


if __name__ == "__main__":
    main()
