# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class FlexItem(Item):
    def __setitem__(self, key, value):
        if key not in self.fields:
            self.fields[key] = Field()

        self._values[key] = value

class AppDataItem(FlexItem):
    pass

class AppIDItem(Item):
    appid = Field()

class AppDocItem(Item):
    appid = Field()
    desc = Field()
    size = Field()
    format = Field()
    url = Field()