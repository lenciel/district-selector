#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2
import sys
import traceback
import ConfigParser
import logging

import lxml.html as H
from lxml.html.clean import Cleaner
from lxml.builder import E
from lxml.builder import ElementMaker
from lxml.etree import SubElement,Element,CDATA,tostring

from datetime import datetime

class DistrictInfoCrawler():

    def __init__(self,inifile):

        # initial config
        self.__readIni(inifile);
        #initial logger
        self.__initLog();
        #initial http handler
        self.__httpHandler = urllib2.HTTPHandler(debuglevel=1)
        self.__opener = urllib2.build_opener(self.__httpHandler)

    def __postReq(self, url):

        res=self.__opener.open(urllib2.Request(url))

        # parse the content
        fullContent = res.read()
        #self.parsedContent = BeautifulSoup(fullContent)
        doc = H.document_fromstring(fullContent.decode('utf-8'))
        return doc

    def __readIni(self, inifile):
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(inifile))

    def __initLog(self):
        time_tuple = datetime.now().timetuple()
        time_now = "%d_%d_%d_%d_%d_%d" \
            % (time_tuple[0],time_tuple[1],time_tuple[2],time_tuple[3],time_tuple[4],time_tuple[5])
        self.logger = logging.getLogger("district_crawler")
        self.logger.setLevel(logging.INFO)
        self.fh = logging.FileHandler("district_crawler_"+time_now+".log")
        self.fh.setLevel(logging.INFO)
        self.logger.addHandler(self.fh)
        sys.stdout = StreamRedirector(self.logger, sys.stdout , '[terminal data] ')


    def crawlLatestEntry(self):
        district_list_doc = self.__postReq(self.config.get('Crawler','district_info_list_url'))
        return district_list_doc.xpath('/html/body/div/div/div[3]/div[2]/ul/li[1]/a')[0].attrib['href']


    def crawlDistrictInfo(self, latest_entry_point):
        district_info_doc = self.__postReq(self.config.get('Crawler','district_info_list_url') + latest_entry_point)
        return district_info_doc.xpath('//table/tbody/tr')

class StreamRedirector(object):

    def __init__(self, logger,stream, prefix=''):
        self.logger = logger
        self.stream = stream
        self.prefix = prefix
        self.data = ''

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

        self.data += data
        tmp = str(self.data)
        if '\x0a' in tmp or '\x0d' in tmp:
            tmp = tmp.rstrip('\x0a\x0d')
            self.logger.info('%s%s' % (self.prefix, tmp))
            self.data = ''


if __name__ == '__main__':
    raw_district_dict = []
    crawler = DistrictInfoCrawler('cfg.ini')
    latest_entry_endpoint = crawler.crawlLatestEntry()
    rows = crawler.crawlDistrictInfo(latest_entry_endpoint)
    for row in rows:
        columns = row.xpath('./td[1]/p/span/text() | ./td[2]/p/span/text()')
        code = columns[0].strip().encode('utf-8')
        name = columns[1].strip().encode('utf-8')

