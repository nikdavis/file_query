#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
# Fix imports to work when installed as a package
from file_query_text.main import parse_query, QueryVisitor, execute_query, get_file_attributes
from file_query_text import __version__

def main():
    parser = argparse.ArgumentParser(description="SQL-like queries for your filesystem")
    parser.add_argument("query", nargs="?", default="",
                        help="SQL query for finding files (default: lists all files in current directory)")
    parser.add_argument(
        "--show-content", "-c",
        action="store_true",
        help="Display content of the matching files"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Debug mode: print all file attributes regardless of query"
    )
    parser.add_argument(
        "--no-gitignore", "-g",
        action="store_true",
        help="Don't respect .gitignore files (show ignored files)"
    )
    parser.add_argument(
        "--show-hidden", "-s",
        action="store_true",
        help="Show hidden files (starting with a dot)"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"file_query_text {__version__}",
        help="Show the version and exit"
    )
    args = parser.parse_args()

    # Get current working directory for the query
    cwd = os.getcwd()

    # Handle different query formats:
    # 1. Full SQL format: "SELECT * FROM 'path' WHERE condition"
    # 2. Simple condition: "extension == 'py'"
    # 3. Simple path only: "SELECT * FROM 'path'"
    # 4. Empty query: return all files in current directory
    if not args.query.strip():
        # Empty query - list all files in current directory
        query_str = f"SELECT * FROM '{cwd}'"
    elif args.query.strip().upper().startswith("SELECT"):
        # Full SQL format or SELECT * FROM without WHERE - use as is
        query_str = args.query
    else:
        # Simple condition format - assume it's a WHERE condition
        query_str = f"SELECT * FROM '{cwd}' WHERE {args.query}"

    # Parse and execute the query
    parsed = parse_query(query_str)
    if parsed:
        visitor = QueryVisitor()
        visitor.visit(parsed)
        results = execute_query(
            visitor.select,
            visitor.from_dirs,
            visitor.where,
            respect_gitignore=not args.no_gitignore,
            show_hidden=args.show_hidden
        )

        # Display results
        if not results:
            print("No matching files found.")
            return

        print(f"Found {len(results)} matching files:")

        # In debug mode, print headers
        if args.debug:
            print(f"{'EXTENSION':<15} {'NAME':<30} {'SIZE':<10} {'PATH'}")
            print(f"{'-'*15} {'-'*30} {'-'*10} {'-'*30}")

        for file_path in results:
            if args.debug:
                # Print all attributes in debug mode
                attrs = get_file_attributes(file_path)
                print(f"{attrs['extension']:<15} {attrs['name']:<30} {attrs['size']:<10} {attrs['relative_path']}")
            else:
                # Standard output
                print(file_path)

            # Optionally display file contents
            if args.show_content:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        print("\n--- File Content ---")
                        print(content)
                        print("--- End Content ---\n")
                except Exception as e:
                    print(f"Error reading file: {e}")

if __name__ == "__main__":
    main()
