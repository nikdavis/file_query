import os
import sys
from file_query_text.grammar import query  # Import the fixed grammar
import gitignore_parser
import os.path


def parse_query(query_str):
    try:
        # Increase recursion limit temporarily to handle complex queries
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(2000)

        parsed = query.parseString(query_str, parseAll=True)

        # Restore original recursion limit
        sys.setrecursionlimit(old_limit)
        return parsed
    except Exception as e:
        print(f"Parse error: {e}")
        return None

class QueryVisitor:
    def __init__(self):
        self.select = []
        self.from_dirs = []
        self.where = None

    def visit(self, parsed_query):
        self.select = parsed_query.get("select", ["*"])
        self.from_dirs = parsed_query.get("from_dirs", [])
        self.where = parsed_query.get("where", None)

def execute_query(select, from_dirs, where_conditions, respect_gitignore=True, show_hidden=False):
    matched_files = []

    # Set up gitignore matching if requested
    gitignore_matchers = {}

    for directory in from_dirs:
        if not os.path.exists(directory):
            continue

        # Initialize gitignore matcher for this directory
        if respect_gitignore:
            # Find the repository root (where .git directory is)
            repo_root = directory
            while repo_root != os.path.dirname(repo_root):  # Stop at filesystem root
                if os.path.exists(os.path.join(repo_root, '.git')):
                    break
                repo_root = os.path.dirname(repo_root)

            # If we found a git repo, check for .gitignore
            gitignore_path = os.path.join(repo_root, '.gitignore')
            if os.path.exists(gitignore_path):
                if repo_root not in gitignore_matchers:
                    try:
                        gitignore_matchers[repo_root] = gitignore_parser.parse_gitignore(gitignore_path)
                    except Exception as e:
                        print(f"Warning: Error parsing .gitignore at {gitignore_path}: {e}")

        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)

                # Skip hidden files or files in hidden directories unless explicitly requested
                if not show_hidden:
                    # Check if file name starts with dot
                    if os.path.basename(file_path).startswith('.'):
                        continue

                    # Check if any parent directory starts with dot
                    rel_path = os.path.relpath(file_path, directory)
                    path_parts = rel_path.split(os.sep)
                    if any(part.startswith('.') for part in path_parts[:-1]):  # Check all except the filename
                        continue

                # Check if file is ignored by gitignore rules
                if respect_gitignore:
                    # Find which repo this file belongs to
                    file_repo_root = None
                    for repo_root in gitignore_matchers:
                        if file_path.startswith(repo_root):
                            file_repo_root = repo_root
                            break

                    # Skip if file is ignored by gitignore
                    if file_repo_root and gitignore_matchers[file_repo_root](file_path):
                        continue

                if evaluate_conditions(file_path, where_conditions):
                    matched_files.append(file_path)
    return matched_files

def evaluate_conditions(file_path, condition):
    if not condition:
        return True

    def get_file_attr(attr_name):
        if attr_name == "extension":
            return os.path.splitext(file_path)[1][1:]
        if attr_name == "name":
            return os.path.basename(file_path)
        if attr_name == "size":
            return os.path.getsize(file_path)
        if attr_name == "path":
            return file_path
        # Add more attributes as needed
        return None

    # Evaluation function for expressions
    def eval_expr(expr):
        if not isinstance(expr, list):
            return expr  # For simple terms like 'AND', 'OR'

        if len(expr) == 3:
            # Handle three types of expressions:

            # 1. Basic condition: [attr, op, value]
            if isinstance(expr[0], str) and isinstance(expr[1], str):
                attr_val = get_file_attr(expr[0])
                op = expr[1]
                val = expr[2].strip("'") if isinstance(expr[2], str) else expr[2]  # Remove quotes if string

                if op == "=" or op == "==": return str(attr_val) == val
                if op == "!=" or op == "<>": return str(attr_val) != val
                if op == "<": return attr_val is not None and int(attr_val) < int(val)
                if op == "<=": return attr_val is not None and int(attr_val) <= int(val)
                if op == ">": return attr_val is not None and int(attr_val) > int(val)
                if op == ">=": return attr_val is not None and int(attr_val) >= int(val)

            # 2. Logical operations from infixNotation: [left, op, right]
            elif expr[1] == "AND":
                return eval_expr(expr[0]) and eval_expr(expr[2])
            elif expr[1] == "OR":
                return eval_expr(expr[0]) or eval_expr(expr[2])

        # 3. NOT operation: ['NOT', expr]
        elif len(expr) == 2 and expr[0] == "NOT":
            return not eval_expr(expr[1])

        return False

    return eval_expr(condition.asList())

# Function to get all attributes for a file
def get_file_attributes(file_path):
    """Get all available attributes for a file."""
    cwd = os.getcwd()
    try:
        # Make path relative to current directory
        rel_path = os.path.relpath(file_path, cwd)
    except ValueError:
        # Handle case when on different drives (Windows)
        rel_path = file_path

    attributes = {
        "extension": os.path.splitext(file_path)[1][1:],
        "name": os.path.basename(file_path),
        "size": os.path.getsize(file_path),
        "path": file_path,
        "relative_path": rel_path,
    }
    return attributes

# Example usage
if __name__ == "__main__":
    # Get project root directory for demonstration
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    src_dir = os.path.join(project_root, "src")
    tests_dir = os.path.join(project_root, "tests")
    query_str = f"SELECT * FROM '{src_dir}', '{tests_dir}' WHERE extension == 'py'"
    parsed = parse_query(query_str)
    if parsed:
        visitor = QueryVisitor()
        visitor.visit(parsed)
        results = execute_query(visitor.select, visitor.from_dirs, visitor.where)
        print("Matching files:")
        for file in results:
            # Skip files in .venv directory
            if ".venv" not in file:
                print(file)
