import re

from komparator.utils import beautify, get_base_url


class Scraper:
    def __init__(self, session, url):
        """
        param session: Session is used to keep the same TCP connexion, saves a bit of time
        :type session: requests.Session
        :param url: URL used to scrap informations
        :type url: str
        """
        self.url = url
        extracted_url = beautify(session, self.url, "cerberus-data-metrics|productTitle|prodDetails")
        self.product_data = self.get_product_data(extracted_url)

    def get_product_data(self, soup):
        """
        Literally get product data from an html page

        :param soup: Parsed html
        :type soup: BeautifulSoup object
        :return: Product data
        :rtype: dict
        """
        if soup.prettify() == "":
            return {}

        metrics = soup.find("div", id="cerberus-data-metrics")

        fields_regex = {
            "name": "productTitle",
            "ref": "\s*Item model number\s*|Manufacturer reference:|Modellnummer:",
            "price": "^priceblock_ourprice$|^priceblock_dealprice$|^priceblock_saleprice$",
            "currency": "",
            "asin": ""
        }

        product_data = {"hostname": get_base_url(self.url)}

        for key, value in fields_regex.items():
            if key == "name":
                product_data[key] = soup.find(id=value).string.strip()
            elif key == "ref":
                ref = soup.find(class_="item-model-number")
                if ref:
                    product_data[key] = ref.contents[1].string.strip()
                else:
                    ref = soup.find(string=re.compile(value))
                    if ref:
                        if ref.next_element.string.strip():
                            product_data[key] = ref.next_element.string.strip()
                        else:
                            product_data[key] = list(ref.parent.parent.stripped_strings)[1]
                    else:
                        product_data[key] = ""

            elif key == "price" and metrics:
                product_data[key] = metrics["data-asin-price"]
            elif key == "currency" and metrics:
                product_data[key] = metrics["data-asin-currency-code"]
            elif key == "asin" and metrics:
                product_data[key] = metrics["data-asin"]

        return product_data

