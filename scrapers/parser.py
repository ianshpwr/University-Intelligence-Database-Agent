from bs4 import BeautifulSoup


class HTMLParser:

    @staticmethod
    def parse(html: str):
        return BeautifulSoup(html, "lxml")