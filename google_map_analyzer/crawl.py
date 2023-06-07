import requests
import re
from bs4 import BeautifulSoup


def get_html(url):
    response = requests.get(url)
    return response.text


def find_social_links(url):

    social_networks = ["instagram.", "twitter.", "tiktok.", "facebook.", "lin.ee"]
    post_patterns = [
        "instagram.com/p/",
        "twitter.com/.*/status",
        "tiktok.com/.*/video/",
        "facebook.com/.*/posts",
    ]
    social_links = set()

    # 与えられたURLがSNSのものであればそれをそのまま返す
    for social_network in social_networks:
        if social_network in url:
            # URLが投稿URLでないことを確認
            if not any(re.search(pattern, url) for pattern in post_patterns):
                return [url]

    html = get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    # HTML内にSNSのリンクがあればそれを返す
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        for social_network in social_networks:
            if social_network in href:
                # リンクが投稿リンクでないことを確認
                if not any(re.search(pattern, href) for pattern in post_patterns):
                    social_links.add(href)

    return list(social_links)


# print(find_social_links("https://rui-jewelry.com/"))
