# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field


class DowloadItem(Item):
    file_urls = Field()
    files = Field()
    file_names = Field()
    folder = Field()
    course = Field()
