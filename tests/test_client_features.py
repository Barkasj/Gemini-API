import os
import unittest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock # Added MagicMock

from src.gemini_webapi.client import GeminiClient # Corrected import path
from gemini_webapi import AuthError, set_log_level, logger # GeminiClient was imported from here before, changed to specific path
from gemini_webapi.constants import Model
from gemini_webapi.exceptions import UsageLimitExceeded, ModelInvalid

logging.getLogger("asyncio").setLevel(logging.ERROR)
set_log_level("DEBUG")


class TestGeminiClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.geminiclient = GeminiClient(
            os.getenv("SECURE_1PSID"), os.getenv("SECURE_1PSIDTS")
        )

        try:
            await self.geminiclient.init(timeout=60, auto_refresh=False)
        except AuthError as e:
            self.skipTest(e)

    @logger.catch(reraise=True)
    async def test_successful_request(self):
        response = await self.geminiclient.generate_content(
            "Tell me a fact about today in history and illustrate it with a youtube video",
            model=Model.G_2_5_FLASH,
        )
        logger.debug(response.text)

    @logger.catch(reraise=True)
    async def test_thinking_model(self):
        response = await self.geminiclient.generate_content(
            "1+1=?",
            model=Model.G_2_5_FLASH,
        )
        logger.debug(response.thoughts)
        logger.debug(response.text)

    @logger.catch(reraise=True)
    async def test_switch_model(self):
        for model in Model:
            if model.advanced_only:
                logger.debug(f"Model {model.model_name} requires an advanced account")
                continue

            try:
                response = await self.geminiclient.generate_content(
                    "What's you language model version? Reply version number only.",
                    model=model,
                )
                logger.debug(f"Model version ({model.model_name}): {response.text}")
            except UsageLimitExceeded:
                logger.debug(f"Model {model.model_name} usage limit exceeded")
            except ModelInvalid:
                logger.debug(f"Model {model.model_name} is not available anymore")

    @logger.catch(reraise=True)
    async def test_upload_files(self):
        response = await self.geminiclient.generate_content(
            "Introduce the contents of these two files. Is there any connection between them?",
            files=["assets/sample.pdf", Path("assets/banner.png")],
        )
        logger.debug(response.text)

    @logger.catch(reraise=True)
    async def test_continuous_conversation(self):
        chat = self.geminiclient.start_chat()
        response1 = await chat.send_message("Briefly introduce Europe")
        logger.debug(response1.text)
        response2 = await chat.send_message("What's the population there?")
        logger.debug(response2.text)

    @logger.catch(reraise=True)
    async def test_retrieve_previous_conversation(self):
        chat = self.geminiclient.start_chat()
        await chat.send_message("Fine weather today")
        self.assertTrue(len(chat.metadata) == 3)
        previous_session = chat.metadata
        logger.debug(previous_session)
        previous_chat = self.geminiclient.start_chat(metadata=previous_session)
        response = await previous_chat.send_message("What was my previous message?")
        logger.debug(response)

    @logger.catch(reraise=True)
    async def test_chatsession_with_image(self):
        chat = self.geminiclient.start_chat()
        response1 = await chat.send_message(
            "What's the difference between these two images?",
            files=["assets/banner.png", "assets/favicon.png"],
        )
        logger.debug(response1.text)
        response2 = await chat.send_message(
            "Use image generation tool to modify the banner with another font and design."
        )
        logger.debug(response2.text)
        logger.debug(response2.images)

    @logger.catch(reraise=True)
    async def test_send_web_image(self):
        response = await self.geminiclient.generate_content(
            "Send me some pictures of cats"
        )
        self.assertTrue(response.images)
        logger.debug(response.text)
        for image in response.images:
            self.assertTrue(image.url)
            logger.debug(image)

    @logger.catch(reraise=True)
    async def test_image_generation(self):
        response = await self.geminiclient.generate_content(
            "Generate some pictures of cats"
        )
        self.assertTrue(response.images)
        logger.debug(response.text)
        for image in response.images:
            self.assertTrue(image.url)
            logger.debug(image)

    @logger.catch(reraise=True)
    async def test_card_content(self):
        response = await self.geminiclient.generate_content("How is today's weather?")
        logger.debug(response.text)

    @logger.catch(reraise=True)
    async def test_extension_google_workspace(self):
        response = await self.geminiclient.generate_content(
            "@Gmail What's the latest message in my mailbox?"
        )
        logger.debug(response)

    @logger.catch(reraise=True)
    async def test_extension_youtube(self):
        response = await self.geminiclient.generate_content(
            "@Youtube What's the latest activity of Taylor Swift?"
        )
        logger.debug(response)

    @logger.catch(reraise=True)
    async def test_reply_candidates(self):
        chat = self.geminiclient.start_chat()
        response = await chat.send_message("Recommend a science fiction book for me.")

        if len(response.candidates) == 1:
            logger.debug(response.candidates[0])
            self.skipTest("Only one candidate was returned. Test skipped")

        for candidate in response.candidates:
            logger.debug(candidate)

        new_candidate = chat.choose_candidate(index=1)
        self.assertEqual(response.chosen, 1)
        followup_response = await chat.send_message("Tell me more about it.")
        logger.warning(new_candidate.text)
        logger.warning(followup_response.text)


# New Test Class for Cookie Loading
MOCK_LOAD_BROWSER_COOKIES_PATH = "src.gemini_webapi.client.load_browser_cookies"
MOCK_GET_ACCESS_TOKEN_PATH = "src.gemini_webapi.client.get_access_token"


class TestGeminiClientCookieLoading(unittest.TestCase):

    def create_mock_cookies_data(self, psid_val="test_psid", psidts_val="test_psidts"):
        cookies = {}
        if psid_val:
            cookies["__Secure-1PSID"] = psid_val
        if psidts_val:
            cookies["__Secure-1PSIDTS"] = psidts_val
        return cookies

    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_with_explicit_cookies_no_browser_load(self, mock_load_cookies, mock_get_token):
        mock_get_token.return_value = ("mock_token", self.create_mock_cookies_data())

        client = GeminiClient(secure_1psid="explicit_psid", secure_1psidts="explicit_psidts")

        mock_load_cookies.assert_not_called()
        self.assertEqual(client.cookies["__Secure-1PSID"], "explicit_psid")

    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_auto_load_true_preferred_browser_set(self, mock_load_cookies, mock_get_token):
        mock_load_cookies.return_value = self.create_mock_cookies_data("browser_psid")
        mock_get_token.return_value = ("mock_token", self.create_mock_cookies_data("browser_psid"))

        client = GeminiClient(preferred_browser="firefox")

        mock_load_cookies.assert_called_once_with(domain_name="google.com", browser_name="firefox", verbose=True)
        self.assertEqual(client.cookies["__Secure-1PSID"], "browser_psid")

    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_auto_load_true_no_preferred_browser(self, mock_load_cookies, mock_get_token):
        mock_load_cookies.return_value = self.create_mock_cookies_data("any_browser_psid")
        mock_get_token.return_value = ("mock_token", self.create_mock_cookies_data("any_browser_psid"))

        client = GeminiClient()

        mock_load_cookies.assert_called_once_with(domain_name="google.com", browser_name=None, verbose=True)
        self.assertEqual(client.cookies["__Secure-1PSID"], "any_browser_psid")

    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_auto_load_false(self, mock_load_cookies, mock_get_token):
        mock_get_token.return_value = ("mock_token", {})

        client = GeminiClient(auto_load_cookies=False)

        mock_load_cookies.assert_not_called()
        self.assertEqual(client.cookies, {})

    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_auto_load_true_browser_load_fails_no_psid(self, mock_load_cookies, mock_get_token):
        mock_load_cookies.return_value = {"OTHER_COOKIE": "some_val"}
        mock_get_token.return_value = ("mock_token", {})

        client = GeminiClient()

        mock_load_cookies.assert_called_once_with(domain_name="google.com", browser_name=None, verbose=True)
        self.assertEqual(client.cookies, {})

    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH, side_effect=ImportError("browser-cookie3 not installed"))
    def test_init_auto_load_true_browser_cookie3_not_installed(self, mock_load_cookies_import_error, mock_get_token):
        mock_get_token.return_value = ("mock_token", {})

        client = GeminiClient(auto_load_cookies=True)

        mock_load_cookies_import_error.assert_called_once_with(domain_name="google.com", browser_name=None, verbose=True)
        self.assertEqual(client.cookies, {})

    @patch.dict(os.environ, {
        "GEMINI_AUTO_LOAD_COOKIES": "false",
        "GEMINI_PREFERRED_BROWSER": "edge"
    })
    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_load_from_env_variables(self, mock_load_cookies, mock_get_token):
        mock_get_token.return_value = ("mock_token", {})

        client = GeminiClient()

        self.assertFalse(client.auto_load_cookies)
        self.assertEqual(client.preferred_browser, "edge")
        mock_load_cookies.assert_not_called()

    @patch.dict(os.environ, {
        "GEMINI_AUTO_LOAD_COOKIES": "true",
        "GEMINI_PREFERRED_BROWSER": "env_browser"
    })
    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_constructor_overrides_env(self, mock_load_cookies, mock_get_token):
        mock_load_cookies.return_value = self.create_mock_cookies_data("browser_psid")
        mock_get_token.return_value = ("mock_token", self.create_mock_cookies_data("browser_psid"))

        client = GeminiClient(auto_load_cookies=False, preferred_browser="constructor_browser")

        self.assertFalse(client.auto_load_cookies)
        self.assertEqual(client.preferred_browser, "constructor_browser")
        mock_load_cookies.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_fallback_to_defaults_no_constructor_no_env(self, mock_load_cookies, mock_get_token):
        mock_load_cookies.return_value = self.create_mock_cookies_data("default_psid")
        mock_get_token.return_value = ("mock_token", self.create_mock_cookies_data("default_psid"))

        client = GeminiClient()

        self.assertTrue(client.auto_load_cookies)
        self.assertIsNone(client.preferred_browser)
        mock_load_cookies.assert_called_once_with(domain_name="google.com", browser_name=None, verbose=True)

    @patch.dict(os.environ, {
        "GEMINI_AUTO_LOAD_COOKIES": "not_a_boolean",
        "GEMINI_PREFERRED_BROWSER": "env_browser_2"
    })
    @patch(MOCK_GET_ACCESS_TOKEN_PATH)
    @patch(MOCK_LOAD_BROWSER_COOKIES_PATH)
    def test_init_env_invalid_boolean_evaluates_to_false(self, mock_load_cookies, mock_get_token): # Renamed for clarity
        mock_load_cookies.return_value = self.create_mock_cookies_data("fallback_psid")
        mock_get_token.return_value = ("mock_token", self.create_mock_cookies_data("fallback_psid"))

        client = GeminiClient()

        self.assertFalse(client.auto_load_cookies) # "not_a_boolean".lower() == 'true' is False
        self.assertEqual(client.preferred_browser, "env_browser_2")
        mock_load_cookies.assert_not_called() # Because auto_load_cookies is False


if __name__ == "__main__":
    unittest.main()
