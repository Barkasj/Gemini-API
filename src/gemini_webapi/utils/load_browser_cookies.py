from .logger import logger
import browser_cookie3 as bc3

BROWSER_MAPPING = {
    "firefox": bc3.firefox,
    "chrome": bc3.chrome,
    "chromium": bc3.chromium,
    "opera": bc3.opera,
    "opera_gx": bc3.opera_gx,
    "brave": bc3.brave,
    "edge": bc3.edge,
    "vivaldi": bc3.vivaldi,
    "safari": bc3.safari,
    "librewolf": bc3.librewolf,
}

def load_browser_cookies(domain_name: str = "", verbose=True, browser_name: str | None = None) -> dict:
    """
    Try to load cookies from all supported browsers or a specific browser and return combined cookiejar.
    Optionally pass in a domain name to only load cookies from the specified domain.

    Parameters
    ----------
    domain_name : str, optional
        Domain name to filter cookies by, by default will load all cookies without filtering.
    verbose : bool, optional
        If `True`, will print more infomation in logs.
    browser_name : str | None, optional
        Specific browser to load cookies from. If None, tries all supported browsers.
        Supported names: "firefox", "chrome", "chromium", "opera", "opera_gx", "brave", "edge", "vivaldi", "safari", "librewolf".

    Returns
    -------
    `dict`
        Dictionary with cookie name as key and cookie value as value.
    """

    cookies = {}

    if browser_name:
        browser_name_lower = browser_name.lower()
        if browser_name_lower in BROWSER_MAPPING:
            cookie_fn = BROWSER_MAPPING[browser_name_lower]
            try:
                for cookie in cookie_fn(domain_name=domain_name):
                    cookies[cookie.name] = cookie.value
            except bc3.BrowserCookieError:
                # This error can be common if the browser is not installed or has no cookies
                if verbose:
                    logger.info(f"No cookies found for {browser_name} or browser not installed.")
            except PermissionError as e:
                if verbose:
                    logger.warning(
                        f"Permission denied while trying to load cookies from {browser_name}. {e}"
                    )
            except Exception as e:
                if verbose:
                    logger.error(
                        f"Error happened while trying to load cookies from {browser_name}. {e}"
                    )
        else:
            logger.warning(
                f"Invalid browser name '{browser_name}'. Supported names are: {', '.join(BROWSER_MAPPING.keys())}. "
                "No cookies will be loaded."
            )
            return {}  # Return empty cookies as per requirement for invalid browser name
    else:
        # Original behavior: try all browsers
        for cookie_fn_name, cookie_fn in BROWSER_MAPPING.items():
            try:
                for cookie in cookie_fn(domain_name=domain_name):
                    cookies[cookie.name] = cookie.value
            except bc3.BrowserCookieError:
                # This error is expected if a browser is not installed or has no cookies for the domain
                pass
            except PermissionError as e:
                if verbose:
                    logger.warning(
                        f"Permission denied while trying to load cookies from {cookie_fn_name}. {e}"
                    )
            except Exception as e:
                # Catching generic Exception to avoid program crash for unexpected errors from a specific browser
                if verbose:
                    logger.error(
                        f"Error happened while trying to load cookies from {cookie_fn_name}. {e}"
                    )
    return cookies
