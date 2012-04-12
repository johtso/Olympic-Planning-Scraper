from scrapy.contrib.loader import XPathItemLoader
from olyplan.items import AppID
from scrapy.contrib.loader.processor import TakeFirst, MapCompose

class AppIDLoader(XPathItemLoader):
    default_item_class = AppID

    search_criteria_in = MapCompose(unicode.strip)