import unittest
from unittest.mock import patch, MagicMock
import browser_cookie3 # Import for type hinting and error types

# Adjust the import path based on your project structure
from src.gemini_webapi.utils.load_browser_cookies import load_browser_cookies, BROWSER_MAPPING
from src.gemini_webapi.utils.logger import logger # To potentially check logs

# Disable logging for tests unless specifically testing log output
logger.setLevel("CRITICAL")

class TestLoadBrowserCookies(unittest.TestCase):

    def create_mock_cookie(self, name, value, domain):
        mock_cookie = MagicMock()
        mock_cookie.name = name
        mock_cookie.value = value
        mock_cookie.domain = domain
        return mock_cookie

    @patch('browser_cookie3.chrome')
    def test_load_specific_browser_chrome_success(self, mock_chrome):
        # Mock chrome to return a specific cookie
        mock_cookie = self.create_mock_cookie("__Secure-1PSID", "test_psid_val", "google.com")
        mock_chrome.return_value = [mock_cookie]

        cookies = load_browser_cookies(domain_name="google.com", browser_name="chrome")
        self.assertEqual(cookies, {"__Secure-1PSID": "test_psid_val"})
        mock_chrome.assert_called_once_with(domain_name="google.com")

    @patch('browser_cookie3.firefox')
    def test_load_specific_browser_firefox_success(self, mock_firefox):
        mock_cookie = self.create_mock_cookie("__Secure-1PSID", "test_psid_val_ff", "google.com")
        mock_firefox.return_value = [mock_cookie]

        cookies = load_browser_cookies(domain_name="google.com", browser_name="firefox")
        self.assertEqual(cookies, {"__Secure-1PSID": "test_psid_val_ff"})
        mock_firefox.assert_called_once_with(domain_name="google.com")

    @patch('browser_cookie3.edge')
    def test_load_specific_browser_edge_not_found(self, mock_edge):
        # Mock edge to return no cookies
        mock_edge.return_value = []
        cookies = load_browser_cookies(domain_name="google.com", browser_name="edge")
        self.assertEqual(cookies, {})
        mock_edge.assert_called_once_with(domain_name="google.com")

    @patch('browser_cookie3.chrome')
    def test_load_specific_browser_chrome_error(self, mock_chrome):
        # Mock chrome to raise an error
        mock_chrome.side_effect = browser_cookie3.BrowserCookieError("Chrome error")
        cookies = load_browser_cookies(domain_name="google.com", browser_name="chrome", verbose=False) # verbose=False to suppress error log in test output
        self.assertEqual(cookies, {})
        mock_chrome.assert_called_once_with(domain_name="google.com")

    def test_load_invalid_browser_name(self):
        browser_name = "nonexistentbrowser"
        expected_warning = (
            f"Invalid browser name '{browser_name}'. Supported names are: {', '.join(BROWSER_MAPPING.keys())}. "
            "No cookies will be loaded."
        )
        with patch.object(logger, 'warning') as mock_log_warning:
            cookies = load_browser_cookies(domain_name="google.com", browser_name=browser_name)
            self.assertEqual(cookies, {})
            mock_log_warning.assert_called_once_with(expected_warning)


    @patch('browser_cookie3.librewolf')
    @patch('browser_cookie3.safari')
    @patch('browser_cookie3.vivaldi')
    @patch('browser_cookie3.edge')
    @patch('browser_cookie3.brave')
    @patch('browser_cookie3.opera_gx')
    @patch('browser_cookie3.opera')
    @patch('browser_cookie3.chromium')
    @patch('browser_cookie3.chrome')
    @patch('browser_cookie3.firefox')
    def test_load_no_specific_browser_tries_all_mapped(self, mock_firefox, mock_chrome, mock_chromium, mock_opera, mock_opera_gx, mock_brave, mock_edge, mock_vivaldi, mock_safari, mock_librewolf):
        # Mock one browser to return cookies, others to return empty or error
        mock_ff_cookie = self.create_mock_cookie("__Secure-1PSID", "firefox_psid", "google.com")
        mock_firefox.return_value = [mock_ff_cookie]
        mock_chrome.return_value = []
        mock_chromium.return_value = []
        mock_opera.side_effect = browser_cookie3.BrowserCookieError("Opera error")
        mock_opera_gx.return_value = []
        mock_brave.return_value = []
        mock_edge.side_effect = browser_cookie3.BrowserCookieError("Edge error")
        mock_vivaldi.return_value = []
        mock_safari.side_effect = browser_cookie3.BrowserCookieError("Safari error")
        mock_librewolf.return_value = []


        # Expected cookies only from firefox
        expected_cookies = {"__Secure-1PSID": "firefox_psid"}

        cookies = load_browser_cookies(domain_name="google.com", browser_name=None, verbose=False)
        self.assertEqual(cookies, expected_cookies)

        mock_firefox.assert_called_once_with(domain_name="google.com")
        mock_chrome.assert_called_once_with(domain_name="google.com")
        mock_chromium.assert_called_once_with(domain_name="google.com")
        mock_opera.assert_called_once_with(domain_name="google.com")
        mock_opera_gx.assert_called_once_with(domain_name="google.com")
        mock_brave.assert_called_once_with(domain_name="google.com")
        mock_edge.assert_called_once_with(domain_name="google.com")
        mock_vivaldi.assert_called_once_with(domain_name="google.com")
        mock_safari.assert_called_once_with(domain_name="google.com")
        mock_librewolf.assert_called_once_with(domain_name="google.com")


    @patch('browser_cookie3.chrome')
    def test_permission_error_handling(self, mock_chrome):
        mock_chrome.side_effect = PermissionError("Permission denied for Chrome")
        with patch.object(logger, 'warning') as mock_log_warning:
            cookies = load_browser_cookies(domain_name="google.com", browser_name="chrome", verbose=True) # verbose=True to check log
            self.assertEqual(cookies, {})
            # The warning message includes the browser name from the mapping key, which is lowercased.
            mock_log_warning.assert_called_with("Permission denied while trying to load cookies from chrome. Permission denied for Chrome")

    @patch('browser_cookie3.librewolf')
    @patch('browser_cookie3.safari')
    @patch('browser_cookie3.vivaldi')
    @patch('browser_cookie3.edge')
    @patch('browser_cookie3.brave')
    @patch('browser_cookie3.opera_gx')
    @patch('browser_cookie3.opera')
    @patch('browser_cookie3.chromium')
    @patch('browser_cookie3.chrome')
    @patch('browser_cookie3.firefox')
    def test_load_no_specific_browser_merges_cookies(self, mock_firefox, mock_chrome, mock_chromium, mock_opera, mock_opera_gx, mock_brave, mock_edge, mock_vivaldi, mock_safari, mock_librewolf):
        mock_chrome_psid = self.create_mock_cookie("__Secure-1PSID", "chrome_psid", "google.com")
        mock_chrome_other = self.create_mock_cookie("OTHER_COOKIE", "chrome_other_val", "google.com")
        mock_chrome.return_value = [mock_chrome_psid, mock_chrome_other]

        mock_ff_another = self.create_mock_cookie("ANOTHER_COOKIE", "firefox_another_val", "google.com")
        # Test override: firefox has a different value for __Secure-1PSID
        mock_ff_psid_override = self.create_mock_cookie("__Secure-1PSID", "firefox_override_psid", "google.com")
        mock_firefox.return_value = [mock_ff_another, mock_ff_psid_override]


        mock_chromium.return_value = []
        mock_opera.side_effect = browser_cookie3.BrowserCookieError("Opera error")
        mock_opera_gx.return_value = []
        mock_brave.return_value = []
        mock_edge.return_value = []
        mock_vivaldi.return_value = []
        mock_safari.side_effect = browser_cookie3.BrowserCookieError("Safari error")
        mock_librewolf.return_value = []


        # Cookies from Chrome and Firefox should be merged.
        # The order of BROWSER_MAPPING iteration matters for which cookie gets precedence if names clash.
        # Based on the BROWSER_MAPPING in the file, 'firefox' comes before 'chrome'.
        # So, firefox's __Secure-1PSID should take precedence if both provide it.
        # Let's check BROWSER_MAPPING to be sure: firefox is first, then chrome.
        # So, the last one processed for a given cookie name wins.
        # The loop is `for cookie_fn_name, cookie_fn in BROWSER_MAPPING.items():`
        # So chrome's value for __Secure-1PSID should overwrite firefox's if both are present.
        # The provided code has firefox then chrome in BROWSER_MAPPING.
        # The iteration order of dicts is insertion order from Python 3.7+.
        # In BROWSER_MAPPING: firefox is first, then chrome.
        # So, chrome's value for __Secure-1PSID will be processed AFTER firefox's, and will overwrite it.

        expected_cookies = {
            "__Secure-1PSID": "chrome_psid", # Chrome's value should win due to iteration order
            "OTHER_COOKIE": "chrome_other_val",
            "ANOTHER_COOKIE": "firefox_another_val"
        }
        cookies = load_browser_cookies(domain_name="google.com", browser_name=None, verbose=False)
        self.assertEqual(cookies, expected_cookies)

        # Assert all mocks were called
        mock_firefox.assert_called_once_with(domain_name="google.com")
        mock_chrome.assert_called_once_with(domain_name="google.com")
        mock_chromium.assert_called_once_with(domain_name="google.com")
        mock_opera.assert_called_once_with(domain_name="google.com")
        mock_opera_gx.assert_called_once_with(domain_name="google.com")
        mock_brave.assert_called_once_with(domain_name="google.com")
        mock_edge.assert_called_once_with(domain_name="google.com")
        mock_vivaldi.assert_called_once_with(domain_name="google.com")
        mock_safari.assert_called_once_with(domain_name="google.com")
        mock_librewolf.assert_called_once_with(domain_name="google.com")

if __name__ == '__main__':
    unittest.main()
