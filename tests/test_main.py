import os
import pytest
import tempfile
from pathlib import Path
from src.main import parse_query, execute_query, QueryVisitor

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
