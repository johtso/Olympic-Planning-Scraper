# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html
import csv

from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy import log


from olyplan.items import AppIDItem

class OlyPipeline(object):
    def __init__(self):
        self.appdata = []
        self.appdata_titles = set()
        # dispatcher.connect(self.spider_opened, signals.spider_opened)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

        appdocfields = ('appid', 'desc', 'size', 'format', 'url')

        self.appdoc_writer = csv.DictWriter(open('appdocs.csv', 'wb'),
            appdocfields,
            restval=None,
            extrasaction='raise'
            )
        
        headerrow = {}
        for field in appdocfields:
            headerrow[field] = field
        
        self.appdoc_writer.writerow(headerrow)

    def process_item(self, item, spider):
        name = item.__class__.__name__

        if name == "AppDocItem":
            self.process_appdoc_item(item)
        elif name == "AppDataItem":
            self.process_appdata_item(item)
            
        return item
    
    def spider_closed(self, spider):

        spider.log("Writing appdata to file...", level=log.INFO)

        fieldnames = list(self.appdata_titles)
        appdata_writer = csv.DictWriter(open('appdata.csv', 'wb'),
            fieldnames,
            restval=None,
            extrasaction='raise',
            # quoting=csv.QUOTE_NONNUMERIC,
            # encoding="utf-8"
            )
        
        headerrow = {}
        for field in fieldnames:
            headerrow[field] = field

        appdata_writer.writerow(headerrow)

        for row in self.appdata:
            row = self.utf_8_encoder(row)
            appdata_writer.writerow(row)

        spider.log("Appdata successfully written to file!", level=log.INFO)

    def process_appdata_item(self, item):
        data = dict(item)
        self.appdata.append(data)
        self.appdata_titles.update(data.keys())
    
    def process_appdoc_item(self, item):
        doc = self.utf_8_encoder(dict(item))

        self.appdoc_writer.writerow(doc)

    def utf_8_encoder(self, unicode_dict):
        utf8_dict = {}
        for key in unicode_dict:
            if isinstance(unicode_dict[key], unicode):
                utf8_dict[key] = unicode_dict[key].encode("utf-8")
            else:
                utf8_dict[key] = unicode_dict[key]
        return utf8_dict
