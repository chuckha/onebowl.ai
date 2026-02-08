import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from recipe_scrapers import scrape_html

from models import RawRecipe


class FetchError(Exception):
    pass


def _check_url_for_ssrf(url: str) -> None:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise FetchError("Invalid URL: no hostname found.")

    try:
        addrinfos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise FetchError(f"Could not resolve hostname: {exc}") from exc

    for family, _, _, _, sockaddr in addrinfos:
        ip_str = sockaddr[0]
        addr = ipaddress.ip_address(ip_str)
        if addr.is_private or addr.is_reserved or addr.is_loopback or addr.is_link_local:
            raise FetchError("URLs pointing to private/internal networks are not allowed.")


def fetch_recipe(url: str) -> RawRecipe:
    _check_url_for_ssrf(url)

    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "OneBowl/1.0"})
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Could not fetch URL: {exc}") from exc

    html = resp.text

    try:
        return _scrape_structured(html, url)
    except Exception:
        return _scrape_fallback(html, url)


def _scrape_structured(html: str, url: str) -> RawRecipe:
    scraper = scrape_html(html, org_url=url)
    title = scraper.title()
    ingredients = scraper.ingredients()
    instructions = scraper.instructions()
    if not ingredients:
        raise ValueError("No ingredients found via structured scraper")
    return RawRecipe(
        title=title,
        ingredients=ingredients,
        instructions=instructions,
        source_url=url,
    )


def _scrape_fallback(html: str, url: str) -> RawRecipe:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    content = soup.find("main") or soup.find("article") or soup.find("body")
    if content is None:
        raise FetchError("Could not extract any content from the page.")

    text = content.get_text(separator="\n", strip=True)
    if len(text) < 50:
        raise FetchError("Page does not appear to contain a recipe.")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown Recipe"

    return RawRecipe(
        title=title,
        ingredients=[],
        instructions=text,
        source_url=url,
    )
