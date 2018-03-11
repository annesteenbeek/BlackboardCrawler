# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from tinydb import TinyDB, Query
from scrapy.pipelines.files import FilesPipeline
from scrapy import Request
import os

class MyFilePipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        foldername = item['course'][0]+'/' + '/'.join(item['folder'])
        for count, url in enumerate(item.get(self.files_urls_field, [])):
            request = Request(url)
            request.meta['foldername'] = foldername
            request.meta['filename'] = item['file_names']
            yield request
    
    def file_path(self, request, response=None, info=None):
        folder_name = request.meta['foldername']
        complete_filename = os.path.splitext(request.meta['filename'])
        file_name = complete_filename[0]
        file_ext = complete_filename[1].lower()

        return '%s/%s%s' % (folder_name, file_name, file_ext)
