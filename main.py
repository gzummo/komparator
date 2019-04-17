#!usr/bin/env python3
import eventlet
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO

from komparator.utils import init_session, is_valid_url
from komparator.scraper import Scraper
from komparator.comparator import Comparator


eventlet.monkey_patch()  # Need to monkey patch asap
App = Flask(__name__)
Socketio = SocketIO(App, async_mode="eventlet", ping_timeout=120)


@App.route("/api/find-cheaper", methods=["POST"])
@cross_origin()
def get_cheaper_product():
    """
    Look for a product cheaper than the starting product

    :return: URL of product page, if a cheaper product was found
    .. todo:: Identify captcha scenario
              Identify blacklist scenario
    """
    session = init_session()

    if request.json.get("url") is None:
        return jsonify({"error": "URL field is empty"})
    else:
        url = request.json["url"]
        if not is_valid_url(url):
            return jsonify({"error": "URL is not valid"})

    if request.json.get("sid") is None:
        return jsonify({"error": "Socket connexion failed"})
    else:
        sid = request.json["sid"]

    # Getting data from the product link sent by the user
    scraper = Scraper(session, url)

    # Comparing with search results
    if scraper.product_data:
        comparator = Comparator(session, Socketio, sid, scraper.product_data)

        if comparator.found_cheaper:
            return jsonify({"info": comparator.result, "url": "{}/dp/{}".format(comparator.result["hostname"], comparator.result["asin"])})
        else:
            return jsonify({"error": "Could not find a cheaper product :/"})
    else:
        return jsonify({"error": "Couldn't find product info"})


if __name__ == "__main__":
    Socketio.run(App)

