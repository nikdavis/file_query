# File Query (fq)

A SQL-like interface for querying files in your filesystem.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/file-query.git
cd file-query

# Install with pip
pip install -e .

# Or use UV
uv run python -m src.cli "your query"

# Install as a permanent tool with UV
uv tool install .
# This will install the 'fq' command
```

## Usage

### Command Line

The quickest way to run file-query is with UV:

```bash
uv run python -m src.cli "your query here"
```

After installation, you can use the shorthand command:

```bash
fq "your query here"
```

#### Basic Usage

```bash
# Find all Python files
fq "extension == 'py'"

# Find all text files and show their content
fq "extension == 'txt'" --show-content
```

#### Advanced Queries

File Query supports full SQL-like syntax:

```bash
# Find all Python files in the src directory
fq "SELECT * FROM 'src' WHERE extension == 'py'"

# Find all files larger than 100KB
fq "SELECT * FROM '.' WHERE size > 102400"

# Complex conditions
fq "SELECT * FROM '.' WHERE (extension == 'pdf' AND size > 1000000) OR (extension == 'txt' AND NOT name == 'README.txt')"
```

## Query Syntax

File Query uses a SQL-like syntax:

```sql
SELECT * FROM 'directory_path' WHERE condition
```

### Available Attributes

- `extension`: File extension (without the dot)
- `name`: Filename with extension
- `size`: File size in bytes
- `path`: Full file path

### Operators

- Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Logical: `AND`, `OR`, `NOT`

## Examples

```bash
# Find all PDF files
fq "extension == 'pdf'"

# Find all files not named "main.py"
fq "NOT name == 'main.py'"

# Find all large image files
fq "SELECT * FROM '.' WHERE (extension == 'jpg' OR extension == 'png') AND size > 500000"

# Find files with 'config' in their path
fq "path == '.*config.*'"

### Using wildcards with the LIKE operator

Find all Python files with "test" in their name:
```
fq "name LIKE '%test%.py'"
```

Find all files with a specific prefix:
```
fq "name LIKE 'config%'"
```

Find all markdown files in a specific year's folder:
```
fq "path LIKE '%/2023/%' AND extension == 'md'"
```
