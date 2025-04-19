import os
import sys

def parse_query(query_str):
    from .grammar import query  # Import the fixed grammar
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

def execute_query(select, from_dirs, where_conditions):
    matched_files = []
    for directory in from_dirs:
        if not os.path.exists(directory):
            continue
        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
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
        # Add more attributes as needed
        return None

    # Evaluation function for expressions
    def eval_expr(expr):
        if isinstance(expr, list):
            if len(expr) == 3:
                # Basic condition: [attr, op, value]
                attr_val = get_file_attr(expr[0])
                op = expr[1]
                val = expr[2].strip("'")  # Remove quotes

                if op == "==": return str(attr_val) == val
                if op == "!=": return str(attr_val) != val
                if op == "<": return attr_val is not None and int(attr_val) < int(val)
                if op == "<=": return attr_val is not None and int(attr_val) <= int(val)
                if op == ">": return attr_val is not None and int(attr_val) > int(val)
                if op == ">=": return attr_val is not None and int(attr_val) >= int(val)
            elif expr[0] == "NOT":
                return not eval_expr(expr[1])
            elif expr[1] in ["AND", "OR"]:
                left = eval_expr(expr[0])
                right = eval_expr(expr[2])
                return left and right if expr[1] == "AND" else left or right
        return False

    return eval_expr(condition.asList())

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
