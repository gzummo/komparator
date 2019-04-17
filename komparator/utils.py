import re
import requests
import validators
import pytesseract
import urllib.parse as UrlParser
from bs4 import BeautifulSoup, SoupStrainer
from PIL import Image, ImageOps
from enum import Enum, auto


class SearchMode(Enum):
    REF = auto(),
    ASIN = auto(),
    NAME = auto()


def beautify(session, url, id=None):
    """
    Parse html using Beautiful Soup 4

    :param session: Session used throughout runtime
    :type session: requests.Session
    :param url: URL to get and parse
    :type url: str
    :param id: Id used to filter the html in order to parse only useful content, saves time
    :type id: str
    :return: BeautifulSoup object

    # Use this code block if blacklisted
    # from itertools import cycle
    # from fake_useragent import UserAgent
    # ua = init_ua()
    # headers = {"User-Agent": ua.random}
    # session.headers.update(headers)
    # proxy_cycle = get_proxy_cycle(session)
    # proxy = next(proxy_cycle)
    # proxies = {"http": proxy, "https": proxy}
    # session.proxies.update(proxies)
    """
    website = session.get(url)
    # Code 503 => high probability of captcha
    if website.status_code == 503:
        pass
    if website.status_code == 200:
        if id is None:
            extracted_url = BeautifulSoup(website.content, "lxml")
        else:
            only_with_id = SoupStrainer(id=re.compile(id))
            extracted_url = BeautifulSoup(website.content, "lxml", parse_only=only_with_id)

        return extracted_url
    else:
        return BeautifulSoup("", "lxml")


def init_session():
    """
    Initialise our session

    :return: Session used throughout runtime
    :rtype: requests.Session
    """
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"}
    session.headers.update(headers)
    return session


def solve_captcha(path):
    """
    In case we get a captcha

    :param path: Path to the image
    :type path: str
    :return: String representation of the text in the image
    :rtype: str

    .. todo:: Finish implementing captcha workaround
    """
    image = Image.open(path).convert("RGB")
    image = ImageOps.autocontrast(image)

    filename = "captcha.png"
    image.save(filename)

    text = pytesseract.image_to_string(Image.open(filename))
    return text


def is_result_item(tag):
    """
    Function that serves as filter when looking for result items in a bs4 object

    :param tag: html tag inside a bs4 object
    :type tag: bs4.element.Tag
    :return: True if the tag is a result item, False if not
    :rtype: bool
    """
    if tag.has_attr("data-index"):
        return True
    elif tag.has_attr("id") and "result_" in tag["id"]:
        return True
    else:
        return False


def get_base_url(url):
    """
    Get base URL from any URL

    :param url: URL to analyse
    :type url: str
    :return: Base URL
    :rtype: str
    """
    parsed_url = UrlParser.urlparse(url)
    return parsed_url.scheme + "://" + parsed_url.netloc


def is_valid_url(url):
    """
    Check if the url is valid and has the correct domain name

    :param url: URL to analyse
    :type url: str
    :return: True if it's valid, false if it isn't
    :rtype: bool
    """
    if validators.url(url):
        parsed_url = UrlParser.urlparse(url)
        if re.search("(?:www.)(\w*)", parsed_url.netloc).group(1) == "amazon":
            return True
    return False


# Uncomment functions below if blacklisted
# def init_ua():
#     """
#     In case we are blacklisted
#
#     :return: Object that can generate user agents
#     :rtype: UserAgent object
#     """
#     return UserAgent(verify_ssl=False)  # Parameter set as a temp solution until new fix.


# def get_proxy_list(session):
#     """
#     Get a list of proxies from free-proxy-list
#
#     :param session: Session used throughout runtime
#     :type session: requests.Session
#     :return: A list of proxies
#     :rtype: list
#     """
#     proxy_list = []
#     html = session.get("https://free-proxy-list.net/anonymous-proxy.html")
#     only_with_id = SoupStrainer(id="proxylisttable")
#     extracted_url = BeautifulSoup(html.content, "lxml", parse_only=only_with_id)
#     proxies = extracted_url.tbody.find_all("tr")
#
#     for proxy in proxies:
#         if proxy.find(class_="hx").string.strip() == "yes":
#             fields = proxy.find_all("td")
#             full_proxy = "http://{}:{}".format(fields[0].string.strip(), fields[1].string.strip())
#             proxy_list.append(full_proxy)
#
#     return proxy_list


# def get_proxy_cycle(session):
#     """
#     In case we are blacklisted
#
#     :param session: Session used throughout runtime
#     :type session: requests.Session
#     :return: A way to cycle through proxies
#     :rtype: itertools.cycle
#     """
#     return cycle(get_proxy_list(session))

