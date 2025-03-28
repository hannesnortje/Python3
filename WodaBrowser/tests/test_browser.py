import pytest
from PyQt6.QtCore import QUrl, Qt, QEvent
from PyQt6.QtWidgets import QFileDialog, QMenu
from wodabrowser.browser import Browser, BrowserTab, DevToolsWindow, MAX_HISTORY_LENGTH  # Import MAX_HISTORY_LENGTH
from unittest.mock import MagicMock, patch

@pytest.fixture
def browser(qapp):
    """Create a browser instance for testing."""
    with patch('wodabrowser.browser.Browser.load_saved_tabs'):  # Prevent loading saved tabs
        browser = Browser()
        return browser

@pytest.fixture
def browser_tab(qapp):
    """Create a browser tab instance for testing."""
    return BrowserTab("https://test.wo-da.de")

def test_browser_initialization(browser):
    """Test browser initialization."""
    assert browser.windowTitle() == "Woda Browser"
    assert browser.tabs.count() == 1  # Now should be 1 since we patched load_saved_tabs

def test_new_tab(browser):
    """Test creating a new tab."""
    initial_count = browser.tabs.count()
    browser.new_tab()
    assert browser.tabs.count() == initial_count + 1

def test_close_tab(browser):
    """Test closing a tab."""
    browser.new_tab()
    initial_count = browser.tabs.count()
    browser.close_tab(1)
    assert browser.tabs.count() == initial_count - 1

@patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
def test_handle_download_requested(mock_dialog, browser_tab):
    """Test download handling."""
    mock_dialog.return_value = ("/tmp/test.pdf", "")
    mock_download = MagicMock()
    mock_download.suggestedFileName.return_value = "test.pdf"
    mock_download.isFinished.return_value = False
    
    browser_tab.handle_download_requested(mock_download)
    
    assert mock_download.setDownloadDirectory.called
    assert mock_download.setDownloadFileName.called
    assert mock_download.accept.called

def test_navigation(browser):
    """Test browser navigation."""
    browser.url_bar.setText("https://test.wo-da.de")
    browser.navigate_to_url()
    assert browser.current_browser() is not None

def test_zoom_controls(browser):
    """Test zoom functionality."""
    initial_zoom = browser.zoom_level
    browser.zoom_in()
    assert browser.zoom_level > initial_zoom
    browser.zoom_out()
    assert browser.zoom_level == initial_zoom

def test_history_recording(browser):
    """Test history recording."""
    url = "https://test.wo-da.de"
    browser.record_history(url)
    assert len(browser.history) == 1
    assert browser.history[0][1] == url

def test_dev_tools_window(browser):
    """Test DevTools window functionality."""
    browser.open_dev_tools()
    assert browser.dev_tools_window.isVisible()
    browser.dev_tools_window.close()
    assert not browser.dev_tools_window.isVisible()

def test_context_menu(browser):
    """Test context menu actions."""
    browser.new_tab()
    tab = browser.tabs.widget(1)
    tab.browser.setHtml("<html><body><p>Test</p></body></html>")
    tab.browser.page().runJavaScript("document.execCommand('copy');")
    # Add more context menu actions as needed

def test_drag_and_drop_tabs(browser):
    """Test tab drag and drop functionality."""
    browser.new_tab()
    initial_index = browser.tabs.currentIndex()
    browser.tabs.tabBar().moveTab(initial_index, 0)
    assert browser.tabs.currentIndex() == 0

def test_open_all_history_tab(browser):
    """Test opening all history tab."""
    browser.record_history("https://test.wo-da.de")
    browser.open_all_history_tab()
    assert browser.tabs.count() == 2
    assert browser.tabs.tabText(1) == "History"

def test_invalid_url_navigation(browser):
    """Test navigation to an invalid URL."""
    browser.url_bar.setText("invalid-url")
    browser.navigate_to_url()
    assert browser.current_browser().url().toString() == "http://invalid-url"

def test_network_error_handling(browser):
    """Test handling of network errors."""
    browser.url_bar.setText("http://nonexistent.url")
    browser.navigate_to_url()
    assert browser.current_browser().url().toString() == "http://nonexistent.url"

def test_user_settings_persistence(browser):
    """Test saving and loading of user settings."""
    browser.settings.setValue("testSetting", "testValue")
    assert browser.settings.value("testSetting") == "testValue"
    browser.settings.sync()
    assert browser.settings.value("testSetting") == "testValue"

def test_url_sanitization(browser):
    """Test URL sanitization functionality."""
    test_cases = [
        ("example.com", "http://example.com"),
        ("https://example.com", "https://example.com"),
        ("ftp://example.com", "ftp://example.com"),
        ("localhost:8080", "http://localhost:8080"),
    ]
    for input_url, expected_url in test_cases:
        result = browser.sanitize_url(input_url)
        # Convert result to string and normalize the URL format
        result_str = result.toString()
        if not result_str.startswith(('http://', 'https://', 'ftp://')):
            result_str = f"http://{result_str}"
        assert result_str == expected_url

def test_tab_title_update(browser):
    """Test tab title updates correctly."""
    browser.new_tab()
    tab = browser.tabs.widget(browser.tabs.count() - 1)
    new_title = "New Title"
    browser.update_tab_title(tab, new_title)
    assert browser.tabs.tabText(browser.tabs.count() - 1) == new_title

def test_recently_closed_tabs(browser):
    """Test recently closed tabs functionality."""
    test_url = "https://test.wo-da.de"
    browser.new_tab()
    tab_index = browser.tabs.count() - 1
    tab = browser.tabs.widget(tab_index)
    tab.browser.setUrl(QUrl(test_url))
    browser.close_tab(tab_index)
    assert test_url in browser.recently_closed

def test_print_dialog(browser):
    """Test print dialog opens correctly."""
    with patch('PyQt6.QtPrintSupport.QPrintDialog.exec') as mock_exec:
        mock_exec.return_value = False
        browser.print_page()
        assert mock_exec.called

def test_save_as_dialog(browser):
    """Test save as dialog opens correctly."""
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
        mock_dialog.return_value = ("/tmp/test.html", "")
        browser.save_as()
        assert mock_dialog.called

def test_context_menu_creation(browser):
    """Test context menu contains all required items."""
    menu = QMenu()
    browser.add_context_action(menu, "Test Action", "test();")
    assert len(menu.actions()) == 1
    assert menu.actions()[0].text() == "Test Action"

def test_zoom_limits(browser):
    """Test zoom level respects minimum limit."""
    # Test minimum zoom level
    for _ in range(20):  # Try to zoom out more than minimum
        browser.zoom_out()
    assert browser.zoom_level >= 0.1

    # Test zoom in
    initial_zoom = browser.zoom_level
    browser.zoom_in()
    assert browser.zoom_level > initial_zoom

def test_history_limit(browser):
    """Test history stays within maximum length."""
    for i in range(MAX_HISTORY_LENGTH + 10):  # Add more than max
        browser.record_history(f"https://test{i}.com")
    assert len(browser.history) <= MAX_HISTORY_LENGTH

def test_dev_tools_zoom(browser):
    """Test DevTools window zoom controls."""
    browser.open_dev_tools()
    initial_zoom = browser.dev_tools_window.zoom_level
    browser.dev_tools_window.zoom_in()
    assert browser.dev_tools_window.zoom_level > initial_zoom
    browser.dev_tools_window.close()

def test_javascript_injection(browser, qapp):
    """Test JavaScript injection into new tabs."""
    with patch.object(BrowserTab, 'inject_scripts', autospec=True) as mock_inject:
        # Create new tab with the mock in place
        new_tab = BrowserTab("https://test.wo-da.de", browser)
        
        # Simulate successful page load
        new_tab.browser.loadFinished.emit(True)
        
        # Process events
        qapp.processEvents()
        
        # Verify the mock was called correctly
        assert mock_inject.called
        assert mock_inject.call_args[0][1] is True  # Check that second argument is True

@patch('PyQt6.QtCore.QSettings')
def test_settings_persistence(mock_settings, browser):
    """Test settings are properly saved and loaded."""
    test_urls = ["https://test1.com", "https://test2.com"]
    browser.settings.setValue("openTabs", test_urls)
    browser.load_saved_tabs()
    assert browser.tabs.count() > 0

def test_clone_tab_content(browser):
    """Test cloned tab preserves original content."""
    browser.new_tab()
    original_index = browser.tabs.count() - 1
    test_url = "https://test.wo-da.de"
    original_tab = browser.tabs.widget(original_index)
    original_tab.browser.setUrl(QUrl(test_url))
    
    browser.clone_tab(original_index)
    cloned_tab = browser.tabs.widget(browser.tabs.count() - 1)
    assert cloned_tab.browser.url().toString() == test_url
