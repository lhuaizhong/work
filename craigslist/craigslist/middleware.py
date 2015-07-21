from twisted.internet.error import TimeoutError as ServerTimeoutError, DNSLookupError, \
                                   ConnectionRefusedError, ConnectionDone, ConnectError, \
                                   ConnectionLost, TCPTimedOutError
from twisted.internet.defer import TimeoutError as UserTimeoutError


import logging
from scrapy.exceptions import NotConfigured
from scrapy.utils.response import response_status_message

from agents import AGENTS

import random
import base64
import os

PROXIES = []
PROXIES_PW = {}

"""
Custom proxy provider.
"""
class CustomHttpProxyMiddleware(object):

    EXCEPTIONS_TO_RETRY = (ServerTimeoutError, UserTimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError,
                           IOError)

    def __init__(self, settings):
        if not settings.getbool('RETRY_ENABLED'):
            raise NotConfigured
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')
        #log.msg('!!! __file__:' + __file__)
        proxy_file = os.path.join(os.path.dirname(__file__), 'proxies.txt')
        #log.msg('!!! file:' + proxy_file)
        self.proxy_ttl = 0
        with open(proxy_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    s = line.split('@')[0]
                    PROXIES.append(s)
                    if '@' in line:
                        PROXIES_PW[s] = line.split('@')[-1]
        self.proxy = None
        self.PROXIES_PW_DEFAULT = settings.get('PROXY_ACCOUNT')
        #print PROXIES
        #print PROXIES_PW
        #print 'PROXIES_PW_DEFAULT', PROXIES_PW_DEFAULT

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # TODO implement complex proxy providing algorithm
        #proxy_ttl = 0
        #if 'proxy_ttl' in request.meta:
        #    request.meta['proxy_ttl'] += 1
        #    proxy_ttl = request.meta['proxy_ttl']

        #log.msg('!!! proxy_ttl:' + str(self.proxy_ttl))
        #if proxy_ttl>0 and proxy_ttl<=10:
        #    log.msg("Proxy is using %s No.%d" % (request.meta['proxy'], request.meta['proxy_ttl']), level=log.DEBUG)
        if PROXIES:
            self.proxy_ttl +=1
            if not self.proxy or self.proxy_ttl>=10:
                p = random.choice(PROXIES)
                self.proxy = p
                self.proxy_ttl = 0
            else:
                p = self.proxy
            try:
                request.meta['proxy'] = "http://%s" % p
                request.meta['proxy_ttl'] = 1
                proxy_user_pass = PROXIES_PW.get(p, None)
                if not proxy_user_pass:
                    proxy_user_pass = self.PROXIES_PW_DEFAULT
                if proxy_user_pass:
                    #proxy_user_pass = 'lumitec:lumitecadmin'
                    basic_auth = 'Basic ' + base64.encodestring(proxy_user_pass)
                    request.headers['Proxy-Authorization'] = basic_auth
                agent = random.choice(AGENTS)
                request.headers['User-Agent'] = agent
                logging.debug("Proxy is setting to %s Agent:%s" % (request.meta['proxy'], agent))
            except Exception, e:
                logging.debug("Exception %s" % e)

    def process_response(self, request, response, spider):
        if 'dont_retry' in request.meta:
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response


    def use_proxy(self, request):
        """
        using direct download for depth <= 2
        using proxy with probability 0.3
        """
        if "depth" in request.meta and int(request.meta['depth']) <= 2:
            return False
        i = random.randint(1, 10)
        return i <= 2

    def process_exception(self, request, exception, spider):
        #log('### exception:(%s) @ [%s]' % (str(exception), request.meta['proxy']))
        #print '###exception:', exception
        #log.msg("###exception: %s, PROXIES len=%d" % (p[7:],len(PROXIES)), level=log.DEBUG)
        self.remove_proxy(request)
        #
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and 'dont_retry' not in request.meta:
            return self._retry(request, exception, spider)
        return None

    def rotate_proxy(self, request):
        if PROXIES:
            p = random.choice(PROXIES)
            try:
                request.meta['proxy'] = "http://%s" % p
                request.meta['proxy_ttl'] = 1
                proxy_user_pass = PROXIES_PW.get(p, None)
                if not proxy_user_pass:
                    proxy_user_pass = self.PROXIES_PW_DEFAULT
                if proxy_user_pass:
                    #proxy_user_pass = 'lumitec:lumitecadmin'
                    basic_auth = 'Basic ' + base64.encodestring(proxy_user_pass)
                    request.headers['Proxy-Authorization'] = basic_auth
                agent = random.choice(AGENTS)
                request.headers['User-Agent'] = agent
                logging.debug("Proxy is setting to %s Agent:%s" % (request.meta['proxy'], agent))
            except Exception, e:
                logging.debug("Exception %s" % e)

    def remove_proxy(self, request):
        p = request.meta.get('proxy', None)
        if p and len(PROXIES)>3 and p[7:] in PROXIES:
            PROXIES.remove(p[7:])
            #print '###AGENT:', request.headers['User-Agent']
            logging.debug("###REMOVE ERROR PROXY: %s, PROXIES len=%d" % (p[7:],len(PROXIES)))

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        if retries <= self.max_retry_times:
            #logging.debug(format="(Proxies)Retrying %(request)s (failed %(retries)d times): %(reason)s", spider=spider, request=request, retries=retries, reason=reason)
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            self.remove_proxy(request)
            self.rotate_proxy(request)
            #if 'proxy' in request.meta:
            #    retryreq.meta['proxy'] = request.meta['proxy']
            #if 'proxy_ttl' in request.meta:
            #    retryreq.meta['proxy_ttl'] = request.meta['proxy_ttl']
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust
            return retryreq
        else:
            #log.msg(format="Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
            #        level=log.DEBUG, spider=spider, request=request, retries=retries, reason=reason)
            #logging.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s" % {spider=spider, request=request, retries=retries, reason=reason})
            pass

"""
change request header nealy every time
"""
class CustomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent
