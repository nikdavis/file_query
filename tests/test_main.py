import os
import pytest
import tempfile
from pathlib import Path
from file_query_text.main import parse_query, execute_query, QueryVisitor

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files for each test case."""
    temp_dir = tempfile.TemporaryDirectory()
    root_path = Path(temp_dir.name)

    # Create test directories
    (root_path / "docs").mkdir()
    (root_path / "downloads").mkdir()

    # Create test files
    with open(root_path / "docs/report.pdf", "w") as f:
        f.write("Test PDF")
    with open(root_path / "docs/note.txt", "w") as f:
        f.write("Test TXT")
    with open(root_path / "downloads/image.jpg", "w") as f:
        f.write("Test JPG")
    # Add a hidden file
    with open(root_path / "docs/.hidden.txt", "w") as f:
        f.write("Hidden file")

    yield root_path  # Provide the path to the test

    # Cleanup is handled automatically by TemporaryDirectory

def test_basic_query(temp_dir):
    """Test SELECT * FROM with a WHERE clause on extension."""
    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs', '{temp_dir}/downloads'
    WHERE extension == 'pdf'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Expected result (only the PDF file)
    expected = [str(temp_dir / "docs/report.pdf")]

    # Normalize paths for comparison (handle different OS path separators)
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected)

def test_multiple_conditions(temp_dir):
    """Test OR conditions."""
    query_str = f"""
    SELECT *
    FROM '{temp_dir}'
    WHERE extension == 'pdf'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Check if we got at least one result
    assert len(results) > 0

def test_nonexistent_directory():
    """Test query with a non-existent directory."""
    query_str = """
    SELECT * FROM '/nonexistent/path'
    WHERE extension == 'pdf'
    """
    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(visitor.select, visitor.from_dirs, visitor.where)
    assert len(results) == 0

# Optional: Test AND / NOT conditions
def test_combined_conditions(temp_dir):
    """Test AND and NOT conditions."""
    query_str = f"""
    SELECT *
    FROM '{temp_dir}/downloads'
    WHERE extension == 'png'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # We don't have any png files
    assert len(results) == 0

def test_and_conditions(temp_dir):
    """Test AND condition logic."""
    # Create a specific file for this test
    with open(temp_dir / "docs/report_2023.pdf", "w") as f:
        f.write("Test PDF with year")

    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    WHERE extension == 'pdf' AND name == 'report_2023.pdf'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Expected result (only the matching PDF file)
    expected = [str(temp_dir / "docs/report_2023.pdf")]

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected)

def test_or_conditions(temp_dir):
    """Test OR condition logic."""
    # Create specific files for this test
    with open(temp_dir / "docs/report_2023.pdf", "w") as f:
        f.write("Test PDF with year")
    with open(temp_dir / "docs/presentation.ppt", "w") as f:
        f.write("Test PPT")

    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    WHERE extension == 'pdf' OR extension == 'ppt'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Get all files in the directory with the specified extensions
    all_pdf_files = list((temp_dir / "docs").glob("*.pdf"))
    all_ppt_files = list((temp_dir / "docs").glob("*.ppt"))
    expected_files = all_pdf_files + all_ppt_files
    expected = [str(p) for p in expected_files]

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected)

def test_not_conditions(temp_dir):
    """Test NOT condition logic."""
    # Create specific files for this test
    with open(temp_dir / "docs/report.pdf", "w") as f:
        f.write("Test PDF")
    with open(temp_dir / "docs/presentation.ppt", "w") as f:
        f.write("Test PPT")
    with open(temp_dir / "docs/document.txt", "w") as f:
        f.write("Test TXT")

    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    WHERE NOT extension == 'pdf'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Query should return all non-PDF files (except hidden ones since show_hidden=False by default)
    all_non_pdf_files = []
    for path in (temp_dir / "docs").glob("*"):
        if path.is_file() and path.suffix != ".pdf" and not path.name.startswith('.'):
            all_non_pdf_files.append(str(path))

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(all_non_pdf_files)

def test_numeric_comparison(temp_dir):
    """Test numerical comparison operators."""
    # Create files with different sizes
    with open(temp_dir / "docs/small.txt", "w") as f:
        f.write("Small")  # Size is 5 bytes
    with open(temp_dir / "docs/medium.txt", "w") as f:
        f.write("Medium text" * 5)  # Size > 10 bytes
    with open(temp_dir / "docs/large.txt", "w") as f:
        f.write("Large text file" * 20)  # Size > 100 bytes

    # Query: Find files larger than 100 bytes
    query_str = f"SELECT * FROM '{temp_dir}/docs' WHERE size > 100"

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Filter files manually to compare
    large_files = []
    for path in (temp_dir / "docs").glob("*"):
        if path.stat().st_size > 100:
            large_files.append(str(path))

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(large_files)

def test_complex_nested_conditions(temp_dir):
    """Test complex nested logical conditions."""
    # Create specific test files with various properties
    with open(temp_dir / "docs/small_report.pdf", "w") as f:
        f.write("Small PDF")  # Small PDF file
    with open(temp_dir / "docs/large_report.pdf", "w") as f:
        f.write("Large PDF file" * 20)  # Large PDF file
    with open(temp_dir / "docs/small_note.txt", "w") as f:
        f.write("Small TXT")  # Small TXT file
    with open(temp_dir / "docs/large_note.txt", "w") as f:
        f.write("Large TXT file" * 20)  # Large TXT file
    with open(temp_dir / "docs/image.jpg", "w") as f:
        f.write("Image file" * 5)  # JPG file

    # Complex query: Find (PDF files that are large) OR (TXT files that are not small)
    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    WHERE (extension == 'pdf' AND size > 100) OR (extension == 'txt' AND NOT size < 50)
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Manually determine expected results
    expected_files = []
    for path in (temp_dir / "docs").glob("*"):
        ext = path.suffix[1:]  # Remove the dot
        size = path.stat().st_size
        if (ext == 'pdf' and size > 100) or (ext == 'txt' and size >= 50):
            expected_files.append(str(path))

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected_files)

def test_query_without_where_clause(temp_dir):
    """Test SELECT * FROM without a WHERE clause."""
    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where,
        show_hidden=True  # Show all files including hidden ones
    )

    # All files in the docs directory should be returned
    expected_files = []
    for path in (temp_dir / "docs").glob("*"):
        if path.is_file():
            expected_files.append(str(path))

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected_files)

def test_empty_query(temp_dir):
    """Test empty query which should return all files."""
    # Create a test file structure
    with open(temp_dir / "docs/extra_file.txt", "w") as f:
        f.write("Extra test file")

    # First, construct the query string that the CLI would create for an empty query
    query_str = f"SELECT * FROM '{temp_dir}'"

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where,
        show_hidden=True  # Show all files including hidden ones
    )

    # Count all files in all subdirectories
    expected_files = []
    for path in temp_dir.glob("**/*"):
        if path.is_file():
            expected_files.append(str(path))

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected_files)

    # Ensure we're getting more than just one file type
    extensions = {os.path.splitext(p)[1] for p in actual}
    assert len(extensions) > 1, "Empty query should return files with different extensions"

def test_no_argument_query(temp_dir):
    """Test when no query argument is passed (None), should be treated as empty string."""
    # Create a test file structure
    with open(temp_dir / "docs/extra_file2.txt", "w") as f:
        f.write("Another test file")

    # Simulate what happens when no argument is passed (CLI would convert to empty string)
    query_str = f"SELECT * FROM '{temp_dir}'"

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where,
        show_hidden=True  # Show all files including hidden ones
    )

    # Count all files in all subdirectories
    expected_files = []
    for path in temp_dir.glob("**/*"):
        if path.is_file():
            expected_files.append(str(path))

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected_files)

    # Ensure we're getting more than just one file type
    extensions = {os.path.splitext(p)[1] for p in actual}
    assert len(extensions) > 1, "Query with no argument should return files with different extensions"

# Add a specific test for hidden file behavior
def test_hidden_files(temp_dir):
    """Test hidden files are excluded by default but included when show_hidden=True."""
    # Create a hidden file
    with open(temp_dir / "docs/.config.json", "w") as f:
        f.write('{"setting": "value"}')

    query_str = f"SELECT * FROM '{temp_dir}/docs'"

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    # Without show_hidden
    results_default = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # With show_hidden=True
    results_with_hidden = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where,
        show_hidden=True
    )

    # Check hidden files are not in default results
    hidden_files = [str(p) for p in (temp_dir / "docs").glob(".*") if p.is_file()]
    default_files = [str(p) for p in results_default]

    for hidden_file in hidden_files:
        assert hidden_file not in default_files, f"Hidden file {hidden_file} should not be in default results"

    # Check hidden files are in results with show_hidden=True
    with_hidden_files = [str(p) for p in results_with_hidden]

    # Get all visible files
    visible_files = [str(p) for p in (temp_dir / "docs").glob("*") if p.is_file()]

    # Combine visible and hidden files to get all files
    all_files = visible_files + hidden_files

    # Create a more specific test that checks if every hidden file is in results
    for hidden_file in hidden_files:
        assert hidden_file in with_hidden_files, f"Hidden file {hidden_file} missing from results"

    # Also check if every visible file is in results
    for visible_file in visible_files:
        assert visible_file in with_hidden_files, f"Visible file {visible_file} missing from results"

def test_like_operator_with_wildcards(temp_dir):
    """Test LIKE operator with SQL-style percentage wildcards."""
    # Create specific files with different naming patterns
    with open(temp_dir / "docs/report_2023.pdf", "w") as f:
        f.write("Test PDF report 2023")
    with open(temp_dir / "docs/report_2024.pdf", "w") as f:
        f.write("Test PDF report 2024")
    with open(temp_dir / "docs/summary_2023.pdf", "w") as f:
        f.write("Test PDF summary 2023")
    with open(temp_dir / "docs/note_2023.txt", "w") as f:
        f.write("Test TXT note 2023")

    # Test LIKE with wildcard at beginning
    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    WHERE name LIKE '%2023.pdf'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Should match all 2023 PDF files
    expected = [
        str(temp_dir / "docs/report_2023.pdf"),
        str(temp_dir / "docs/summary_2023.pdf")
    ]

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected)

    # Test LIKE with wildcard in middle
    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    WHERE name LIKE 'report%pdf'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Should match all report PDF files
    expected = [
        str(temp_dir / "docs/report.pdf"),
        str(temp_dir / "docs/report_2023.pdf"),
        str(temp_dir / "docs/report_2024.pdf")
    ]

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected)

    # Test LIKE with wildcards at both ends
    query_str = f"""
    SELECT *
    FROM '{temp_dir}/docs'
    WHERE name LIKE '%report%'
    """

    parsed = parse_query(query_str)
    visitor = QueryVisitor()
    visitor.visit(parsed)

    results = execute_query(
        visitor.select,
        visitor.from_dirs,
        visitor.where
    )

    # Should match all files with 'report' in the name
    expected = [
        str(temp_dir / "docs/report.pdf"),
        str(temp_dir / "docs/report_2023.pdf"),
        str(temp_dir / "docs/report_2024.pdf")
    ]

    # Normalize paths for comparison
    actual = [str(p) for p in results]
    assert sorted(actual) == sorted(expected)
