import requests
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlparse, parse_qs
import re


def search_web(query, limit=8):
    url = "https://www.bing.com/news/search"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    params = {
        "q": query,
        "format": "rss",
        "mkt": "en-US"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=25
        )
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall(".//item")

        results = []

        for item in items[:limit]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            description = item.findtext("description", "").strip()

            description = unescape(
                re.sub(r"<[^>]+>", " ", description)
            )
            description = re.sub(r"\s+", " ", description).strip()

            if "bing.com/news/apiclick.aspx" in link:
                params = parse_qs(urlparse(link).query)
                link = params.get("url", [link])[0]

            if title and link:
                results.append({
                    "title": unescape(title),
                    "link": link,
                    "description": description
                })

        return results, None

    except requests.RequestException as error:
        return [], f"خطای اتصال به موتور جست‌وجو: {error}"
    except ET.ParseError:
        return [], "پاسخ موتور جست‌وجو قابل پردازش نیست."
    except Exception as error:
        return [], f"خطای جست‌وجو: {error}"
