"""Fetch and parse public-account metadata from a WeChat article page."""

from __future__ import annotations

import base64
import binascii
import html
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


ARTICLE_MAX_BYTES = 8 * 1024 * 1024
ARTICLE_TIMEOUT_SECONDS = 20
ARTICLE_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class WeChatArticleError(RuntimeError):
    """Base error for fetching or parsing a WeChat article."""


class InvalidWeChatArticleUrl(ValueError):
    """Raised when a URL is not a supported public WeChat article URL."""


class WeChatArticleFetchError(WeChatArticleError):
    """Raised when the public article page cannot be downloaded."""


class WeChatArticleMetadataError(WeChatArticleError):
    """Raised when required public-account metadata is absent."""


def validate_wechat_article_url(url: str) -> str:
    """Return a normalized supported WeChat article URL or raise."""
    normalized = (url or "").strip()
    try:
        parsed = urlparse(normalized)
        port = parsed.port
    except ValueError as exc:
        raise InvalidWeChatArticleUrl("公众号文章链接格式不正确") from exc

    if (
        parsed.scheme.lower() != "https"
        or (parsed.hostname or "").lower().rstrip(".") != "mp.weixin.qq.com"
        or parsed.username
        or parsed.password
        or port not in (None, 443)
    ):
        raise InvalidWeChatArticleUrl("请输入 https://mp.weixin.qq.com 的公众号文章链接")

    short_path = re.fullmatch(r"/s/[A-Za-z0-9_-]+/?", parsed.path or "")
    legacy_path = parsed.path.rstrip("/") == "/s" and bool(parsed.query)
    if not short_path and not legacy_path:
        raise InvalidWeChatArticleUrl("请输入正确的公众号文章链接")

    return normalized


def _decode_js_string(value: str) -> str:
    """Decode the small subset of JS string escapes used by article metadata."""

    def replace_hex(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    decoded = re.sub(r"\\x([0-9a-fA-F]{2})", replace_hex, value)
    decoded = re.sub(r"\\u([0-9a-fA-F]{4})", replace_hex, decoded)
    decoded = decoded.replace(r"\/", "/").replace(r"\"", '"').replace(r"\'", "'")
    return html.unescape(decoded).strip()


def _first_match(page_html: str, patterns: tuple[str, ...]) -> str:
    for pattern in patterns:
        match = re.search(pattern, page_html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _decode_js_string(match.group(1))
    return ""


def _meta_content(page_html: str, property_name: str) -> str:
    escaped_name = re.escape(property_name)
    return _first_match(
        page_html,
        (
            rf'<meta[^>]+property=["\']{escaped_name}["\'][^>]+content=["\']([^"\']*)["\']',
            rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']{escaped_name}["\']',
        ),
    )


def _validate_biz(biz: str) -> bool:
    if not biz:
        return False
    try:
        decoded = base64.b64decode(biz, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return False
    return bool(decoded.strip())


def parse_wechat_article_metadata(page_html: str, article_url: str) -> dict[str, Any]:
    """Parse the fields needed by the add-subscription form."""
    biz = _first_match(
        page_html,
        (
            r'\bvar\s+biz\s*=\s*["\']([^"\']+)',
            r'\bwindow\.biz\s*=\s*["\']([^"\']+)',
        ),
    )
    nickname = _first_match(
        page_html,
        (
            r'\bvar\s+nickname\s*=\s*htmlDecode\(\s*["\']([^"\']*)',
            r'\bvar\s+nickname\s*=\s*["\']([^"\']*)',
            r'\bwindow\.nickname\s*=\s*["\']([^"\']*)',
        ),
    )
    logo = _first_match(
        page_html,
        (
            r'\bvar\s+round_head_img\s*=\s*["\']([^"\']+)',
            r'\bvar\s+hd_head_img\s*=\s*["\']([^"\']+)',
        ),
    )

    if not nickname or not _validate_biz(biz):
        raise WeChatArticleMetadataError(
            "未能从文章中识别公众号信息，请确认文章仍可正常访问"
        )

    if logo.startswith("http://"):
        logo = f"https://{logo.removeprefix('http://')}"

    short_id_match = re.search(r"/s/([A-Za-z0-9_-]+)", article_url)
    return {
        "id": short_id_match.group(1) if short_id_match else "",
        "title": _meta_content(page_html, "og:title"),
        "author": _meta_content(page_html, "og:article:author"),
        "description": _meta_content(page_html, "og:description"),
        "topic_image": _meta_content(page_html, "twitter:image"),
        "mp_info": {
            "mp_name": nickname,
            "logo": logo,
            "biz": biz,
        },
    }


def fetch_wechat_article_metadata(
    url: str,
    *,
    timeout: int = ARTICLE_TIMEOUT_SECONDS,
    max_bytes: int = ARTICLE_MAX_BYTES,
) -> dict[str, Any]:
    """Download a public article without launching a browser and parse its metadata."""
    current_url = validate_wechat_article_url(url)
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "User-Agent": ARTICLE_USER_AGENT,
    }

    try:
        with requests.Session() as session:
            for _ in range(4):
                with session.get(
                    current_url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=False,
                    stream=True,
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location", "")
                        current_url = validate_wechat_article_url(
                            urljoin(current_url, location)
                        )
                        continue

                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    if "text/html" not in content_type:
                        raise WeChatArticleFetchError("公众号文章页面返回了非 HTML 内容")

                    body = bytearray()
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise WeChatArticleFetchError("公众号文章页面内容过大")

                    encoding = response.encoding or "utf-8"
                    page_html = bytes(body).decode(encoding, errors="replace")
                    return parse_wechat_article_metadata(page_html, current_url)
    except InvalidWeChatArticleUrl:
        raise
    except WeChatArticleError:
        raise
    except requests.RequestException as exc:
        raise WeChatArticleFetchError("公众号文章页面访问失败，请稍后重试") from exc

    raise WeChatArticleFetchError("公众号文章链接重定向次数过多")
