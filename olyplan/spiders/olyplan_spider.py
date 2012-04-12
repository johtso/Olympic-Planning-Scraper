from datetime import date, timedelta
import re

from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest
from scrapy.selector import HtmlXPathSelector
from scrapy import log

from olyplan.items import AppDataItem, AppDocItem

from dateutil.parser import parse as dtparse

class OlyplanSpider(BaseSpider):
    search_form_url = ("http://planning.london2012.com/publicaccess/tdc/DcApplication/"
                       "application_searchform.aspx")
    results_page_url = ("http://planning.london2012.com/publicaccess/tdc/DcApplication/"
                        "application_searchresults.aspx")
    app_page_url = ("http://planning.london2012.com/publicaccess/tdc/DcApplication/"
                    "application_detailview.aspx")
    num_apps = 0
    num_apps_scraped = 0
    
    search_span = timedelta(days=50)

    name = "olyplan"
    allowed_domains = ["planning.london2012.com"]
    start_urls = [search_form_url]

    def start_requests(self):
        """Check arguments before starting any requests

        """
        self.parse_date_args()
        return BaseSpider.start_requests(self)

    def parse(self, response):
        """Generate multiple search requests.

        Requests will be made to cover date_range_start to date_range_end.
        Each search will cover a range of search_span.

        """
        self.form_response = response

        # self.log("headers: %s" % (response.headers,))
        range_start = self.date_range_start
        range_end = self.date_range_end
        search_span = self.search_span
        
        # Set initial search range dates
        search_from = range_start
        search_to = search_from + search_span

        search_requests = []

        while search_from < range_end:
            if search_to > range_end:
                search_to = range_end

            search_requests.append(self.search_request(response, search_from, search_to))
            
            search_from = search_to + timedelta(days=1)
            search_to = search_from + search_span
        
        return search_requests

    def parse_results(self, response):
        """Parse a search results page.

        """
        hxs = HtmlXPathSelector(response)

        # Grab number of results from page and check if limit was hit
        number_of_results = self.extract_number_of_results(hxs)
        self.log("Search returned %s results" % (number_of_results,), level=log.WARNING)
        
        # Split search into 2 if max results was hit
        if number_of_results == 100:
            self.log("Request hit result limit of 100, spawning 2 new requests", level=log.WARNING)
            halved_searches = self.halve_search(response)
            for search in halved_searches:
                yield search
        
        else:
            appids = hxs.select("//a[@title='View Details']/@href").re("caseno=(?P<extract>.*)$")

            self.num_apps += len(appids)
            
            for appid in appids:
                yield self.app_page_request(appid)

    def parse_app_page(self, response):
        """Parse an application page

        """
        appid = response.meta['appid']

        hxs = HtmlXPathSelector(response)

        items = []

        appdocs = self.extract_app_docs(hxs, appid)

        for appdoc in appdocs:
            items.append(appdoc)

        number_of_docs = len(appdocs)

        appdata = self.extract_app_data(hxs, appid)
        appdata['number_of_docs'] = number_of_docs
        items.append(appdata)
        
        self.num_apps_scraped += 1
        
        self.log("%s out of %s" % (self.num_apps_scraped, self.num_apps), level=log.WARNING)
        
        return items

    def extract_app_docs(self, hxs, appid):
        docrows = hxs.select('//table[@id="tbldocumentList"]/tr')[1:]

        appdocs = []

        for docrow in docrows:
            #self.log(str(docrow), level=log.WARNING)
            desc, size, format = docrow.select('td/text()')[:-1].extract()
            url = docrow.select('td[last()]/button/@path').extract()[0]

            appdoc = AppDocItem()
            appdoc['appid'] = appid
            appdoc['desc'] = desc
            appdoc['size'] = size
            appdoc['format'] = format
            appdoc['url'] = url
            appdocs.append(appdoc)

        return appdocs    

    def extract_app_data(self, hxs, appid):
        data = {}

        details = hxs.select('//input[@class="cDetailInput"]')

        for detail in details:
            value = detail.select('@value').extract()[0]
            name = detail.select('@name').extract()[0]

            data[name] = value

        details = hxs.select('//textarea[@class="cDetailInput"]')

        for detail in details:
            text = detail.select('text()').extract()[0]
            name = detail.select('@name').extract()[0]

            data[name] = text

        appdata = AppDataItem()

        for key in data:
            appdata[key] = data[key]
            appdata['appid'] = appid
        
        return appdata

    def app_page_request(self, appid):
        return Request(url="%s?caseno=%s" % (self.app_page_url, appid),
                       meta={'appid': appid},
                       callback=self.parse_app_page)

    def parse_date_args(self):
        """Check for start [and end] date arguments passed to the spider
        and parse into date objects.

        If there is no start date, raise an exception.
        If there is no end date, default to today's date.

        """
        # Check that a start argument was passed to the spider
        if hasattr(self, 'start'):
            # Convert the start date string into a date object
            self.date_range_start = dtparse(self.start, dayfirst=True).date()
        else:
            log.msg("No start date supplied", level=log.CRITICAL)
            raise Exception("No start date supplied")
            
        if hasattr(self, 'end'):
            self.date_range_end = dtparse(self.end, dayfirst=True).date()
        else:
            self.date_range_end = date.today()
            
        self.log("Scraping date range: %s ----> %s" % (self.date_range_start,
                                                       self.date_range_end),
                 level=log.WARNING)


    
    def search_request(self, response, search_from, search_to):
        """Generate a search request using a response from the search form url
        and add the date range to the POST data.

        """
        self.log("Searching for: %s -> %s" % (search_from, search_to), level=log.WARNING)

        search_request = FormRequest.from_response(response,
                    formdata={'srchDateReceivedStart': search_from.strftime('%d/%m/%Y'),
                              'srchDateReceivedEnd': search_to.strftime('%d/%m/%Y')},
                    meta={'search_from': search_from, 'search_to': search_to,
                          'dont_redirect': True},
                    callback=self.request_bigpage,)
        
        # self.log('search_req: %s' % (search_request,), level=log.WARNING)
        return search_request
    
    def halve_search(self, response):
        """Takes a search request and returns two separate requests
        each for half the date range.

        """
        orig_search_from = response.request.meta['search_from']
        orig_search_to = response.request.meta['search_to']
        
        orig_range = orig_search_to - orig_search_from
        midpoint = orig_search_from + (orig_range/2)

        one_day = timedelta(days=1)

        new_requests = [self.search_request(self.form_response, orig_search_from, midpoint),
                        self.search_request(self.form_response, midpoint+one_day, orig_search_to)]

        return new_requests

    def request_bigpage(self, response):
        """Generate a request for a result page with page size of 100.
        This will allow all results from a search to be harvested from a single page.

        """
        search_from = response.request.meta['search_from']
        search_to = response.request.meta['search_to']

        self.log("Requesting big page for: %s -> %s" % (search_from, search_to),
                 level=log.WARNING)

        session_id = self.extract_sessionid(response)
        header = "ASP.NET_SessionId=%s" % (session_id,)

        return Request(url="%s?pagesize=100" % (self.results_page_url,),
                           headers={'Cookie': header},
                           dont_filter=True,
                           meta={'search_from': search_from, 'search_to': search_to},
                           callback=self.parse_results)
    
    def extract_sessionid(self, response):
        """Takes a response and extracts the session id from the set-cookie header

        """
        sessionid = re.search('ASP\.NET_SessionId=(.*);', response.headers['Set-Cookie']).group(1)
        return sessionid
    
    def extract_number_of_results(self, hxs):
        number_of_results = hxs.select("//td[@class='cFormContent']/text()")\
                       .re('(?P<extract>\d+|One)')[0]
        
        if number_of_results == 'One':
            number_of_results = 1
        else:
            number_of_results = int(number_of_results)

        return number_of_results