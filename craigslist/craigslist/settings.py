# Scrapy settings for glassdoor project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'craigslist'

SPIDER_MODULES = ['craigslist.spiders']
NEWSPIDER_MODULE = 'craigslist.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'glassdoor (+http://www.yourdomain.com)'
#USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'

TELNETCONSOLE_ENABLED = False

WEBSERVICE_ENABLED = False

COOKIES_ENABLED = True
#COOKIES_DEBUG = True

#CLOSESPIDER_ITEMCOUNT = 1000
#LOG_LEVEL = 'INFO'

#DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True

#PROXY_ACCOUNT = ''

#RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 408, 403]
DOWNLOADER_MIDDLEWARES = {
#    'scrapy.downloadermiddlewares.retry.RetryMiddleware':90,
#    'craigslist.middleware.CustomHttpProxyMiddleware': 100,
}

FEED_EXPORTERS = {
    'csv': 'craigslist.feedexport.CSVkwItemExporter'
}

#EXPORT_HEADLINE = 'False'
#CSV_DELIMITER = '|'

EXPORT_FIELDS = [
    'url',
    'title',
    'price',
    'body',
    'bedrooms',
    'posting_id',
    'posting_time',
    'posting_update',
]

#EXPORT_ITEM = '_RIGHTMOVE_SALE'
