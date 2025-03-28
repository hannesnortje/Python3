import pytest
from wodabrowser.browser import CodeExecutor
from PyQt6.QtCore import QByteArray, QVariant
from unittest.mock import patch, MagicMock, mock_open

@pytest.fixture
def executor(qapp):
    """Create a code executor instance for testing."""
    return CodeExecutor()

def test_execute_signal_with_pdf(executor):
    """Test PDF download handling."""
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
        mock_dialog.return_value = ("/tmp/test.pdf", "")
        
        # Mock PDF data
        pdf_data = {
            'type': 'downloadPDF',
            'filename': 'test.pdf',
            'data': 'data:application/pdf;base64,TEST=='
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            executor.executeSignal(pdf_data)
            mock_file.assert_called_once()

def test_execute_signal_with_invalid_input(executor):
    """Test handling of invalid input."""
    result = executor.executeSignal("invalid input")
    assert result is None

def test_execute_python_code(executor):
    """Test executing Python code."""
    code = "print('Hello, World!')"
    expected_output = "Hello, World!\n"

    def handle_code_result(result):
        assert result == expected_output

    executor.codeResultReady.connect(handle_code_result)
    executor.execute_python_code(code)

def test_execute_python_code_with_error(executor):
    """Test executing Python code with an error."""
    code = "print(1 / 0)"  # This will raise a ZeroDivisionError
    expected_output = "division by zero"

    def handle_code_result(result):
        assert expected_output in result

    executor.codeResultReady.connect(handle_code_result)
    executor.execute_python_code(code)

def test_execute_complex_python_code(executor, qapp):  # Add qapp to process events
    """Test executing complex Python code."""
    code = """
import json
data = {
    "message": "Python execution successful!",
    "value": 12345,
    "list": ["item1", "item2", "item3"]
}
print(json.dumps(data))
"""
    expected_output = '{"message": "Python execution successful!", "value": 12345, "list": ["item1", "item2", "item3"]}\n'
    result_received = []

    def handle_code_result(result):
        print("Received result:", result)  # Add debugging information
        result_received.append(result)

    executor.codeResultReady.connect(handle_code_result)
    executor.execute_python_code(code)
    qapp.processEvents()  # Process events to ensure signal is handled

    assert len(result_received) == 1
    assert result_received[0] == expected_output

def test_execute_python_code_from_js(executor, qapp):
    """Test executing Python code from JavaScript."""
    code = "print('Hello from JS!')"
    expected_output = "Hello from JS!\n"

    def handle_code_result(result):
        assert result == expected_output

    executor.codeResultReady.connect(handle_code_result)
    executor.executeSignal(QVariant({"type": "executePython", "code": code}))
    qapp.processEvents()  # Process events to ensure the signal is handled
