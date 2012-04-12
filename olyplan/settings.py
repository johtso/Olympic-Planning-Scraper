# Scrapy settings for olyplan project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'olyplan'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['olyplan.spiders']
NEWSPIDER_MODULE = 'olyplan.spiders'
DEFAULT_ITEM_CLASS = 'olyplan.items.ApplicationItem'
#USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)
USER_AGENT = ("Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US)"
              " AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.86 Safari"
              "/534.13")
# CONCURRANT_SPIDERS = 1
CONCURRANT_REQUESTS_PER_SPIDER = 3
DOWNLOAD_DELAY = 1

LOG_LEVEL = 'WARNING'

#HTTPCACHE_ENABLED = True

DOWNLOADER_MIDDLEWARES = {
    'scrapy.contrib.downloadermiddleware.cookies.CookiesMiddleware': None,
}

ITEM_PIPELINES = [
    'olyplan.pipelines.OlyPipeline',
]