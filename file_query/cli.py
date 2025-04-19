#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
# Fix imports to work when installed as a package
from file_query.main import parse_query, QueryVisitor, execute_query

def main():
    parser = argparse.ArgumentParser(description="SQL-like queries for your filesystem")
    parser.add_argument("query", nargs="?", default="",
                        help="SQL query for finding files (default: lists all files in current directory)")
    parser.add_argument(
        "--show-content", "-c",
        action="store_true",
        help="Display content of the matching files"
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
        results = execute_query(visitor.select, visitor.from_dirs, visitor.where)

        # Display results
        if not results:
            print("No matching files found.")
            return

        print(f"Found {len(results)} matching files:")
        for file_path in results:
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
