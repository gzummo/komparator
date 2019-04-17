import re
from multiprocessing.pool import ThreadPool

from komparator.scraper import Scraper
from komparator.utils import SearchMode, beautify, is_result_item


class Comparator:
    def __init__(self, session, socketio, sid, source_data):
        """
        :param session: Session is used to keep the same TCP connexion, saves a bit of time
        :type session: requests.Session
        :param socketio: Instance of the flask_socketio server, used to send updates to the client
        :type socketio: flask_socketio.SocketIO
        :param sid: Session ID of the client, used to send updates exclusively to the client
        :type sid: str
        :param source_data: Source product information
        :type source_data: dict
        """
        self.session = session
        self.source = source_data
        self.found_cheaper = False
        self.results_data_list = []
        self.progress = [0, 0]
        self.socketio = socketio
        self.sid = sid

        if self.source["ref"]:
            self.search_mode = SearchMode.REF
        elif self.source["asin"]:
            self.search_mode = SearchMode.ASIN
        else:
            self.search_mode = SearchMode.NAME

        self.result = self.compare_products(self.source)

    def compare_products(self, source):
        """
        Compare source product to other similar products

        :param source: Source product information
        :type source: dict
        :return: Cheapest product found
        :rtype: dict
        """
        cheapest_product = {}
        ref_result_data_list = {}

        # Search term will change depending on whether we find a ref number or not
        if self.search_mode == SearchMode.REF:
            ref_result_data_list = self.search_by_term(source["hostname"], source["ref"].replace(" ", "+"))
        elif self.search_mode == SearchMode.ASIN:
            ref_result_data_list = self.search_by_term(source["hostname"], source["asin"])
        else:
            ref_result_data_list = self.search_by_term(source["hostname"], source["name"])

        if len(ref_result_data_list) == 0:
            self.socketio.emit("update", {"data": 0})
            return {}

        for result_data in ref_result_data_list:
            if cheapest_product:
                if self.search_mode == SearchMode.REF and result_data["ref"] == source["ref"]:
                    if result_data["price"] < cheapest_product["price"] and result_data["currency"] == cheapest_product["currency"]:
                        cheapest_product = result_data
                elif self.search_mode != SearchMode.REF and result_data["price"] < cheapest_product["price"] and result_data["currency"] == cheapest_product["currency"]:
                    cheapest_product = result_data
            else:
                if result_data["ref"] == source["ref"]:
                    cheapest_product = result_data

        if cheapest_product["price"] < source["price"]:
            self.found_cheaper = True
            cheapest_product["source_price"] = source["price"]

        return cheapest_product

    def search_by_term(self, url, term):
        """
        Crawl search result page in order to scrap product information

        :param url: Base URL
        :type url: str
        :param term: Search term
        :type term: str
        :return: List of search result data
        :rtype: List of dictionaries
        """
        search_results = []
        search_url = "{}/s?ref=nb_sb_noss_1&k={}".format(url, term)
        extracted_results = beautify(self.session, search_url)

        if re.search("(?:www.\w*.)(\w*)", url).group(1) == "com":
            search_results = extracted_results.find(class_="s-result-list sg-row").find_all("div")
        else:
            search_results = extracted_results.find_all(is_result_item)

        if len(search_results) != 0:
            self.progress[1] = len(search_results)
            # Multi-threading to save time
            pool = ThreadPool(4)
            pool.map(self.get_search_result_data, search_results)
            pool.close()
            pool.join()

        return self.results_data_list

    def get_search_result_data(self, search_result):
        """
        Method that each thread will execute to get data from a product page and append it to ``self.results_data_list``

        :param search_result: Info on a product from the search results
        :type search_result: dict
        """
        asin = search_result["data-asin"]
        result_data = Scraper(self.session, "{}/dp/{}".format(self.source["hostname"], asin)).product_data
        self.results_data_list.append(result_data)
        # Update scraping progress to the client, ``self.progress`` is used to imitate a fraction
        self.progress[0] += 1
        self.socketio.emit("update", {"data": self.progress[0]/self.progress[1]*100}, room=self.sid)

