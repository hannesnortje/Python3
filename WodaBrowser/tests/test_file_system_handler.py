import pytest
import os
from wodabrowser.file_system_handler import FileSystemHandler
from unittest.mock import patch, mock_open

@pytest.fixture
def fs_handler(qapp):
    """Create a file system handler instance for testing."""
    return FileSystemHandler()

def test_read_file(fs_handler):
    """Test reading a file."""
    with patch("builtins.open", mock_open(read_data="test content")):
        fs_handler.readFile("test.txt")
        # Since this is async, we'd need to check the signal emission

def test_create_file(fs_handler, tmp_path):
    """Test creating a file."""
    test_file = tmp_path / "test.txt"
    fs_handler.createFile(str(test_file), "test content")
    assert test_file.exists()
    assert test_file.read_text() == "test content"

def test_delete_file(fs_handler, tmp_path):
    """Test deleting a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    fs_handler.deleteFile(str(test_file))
    assert not test_file.exists()

def test_create_directory(fs_handler, tmp_path):
    """Test creating a directory."""
    test_dir = tmp_path / "test_dir"
    fs_handler.createDirectory(str(test_dir))
    assert test_dir.exists()
    assert test_dir.is_dir()

def test_change_file_content(fs_handler, tmp_path):
    """Test changing file content."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("old content")
    fs_handler.changeFileContent(str(test_file), "new content")
    assert test_file.read_text() == "new content"

def test_large_file_operations(fs_handler, tmp_path):
    """Test reading and writing large files."""
    test_file = tmp_path / "large_test.txt"
    large_content = "A" * 10**6  # 1 MB of data
    fs_handler.createFile(str(test_file), large_content)
    assert test_file.exists()
    assert test_file.read_text() == large_content
    fs_handler.readFile(str(test_file))
    # Since this is async, we'd need to check the signal emission
