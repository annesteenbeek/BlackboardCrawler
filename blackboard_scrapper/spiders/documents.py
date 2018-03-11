import json
import re
import scrapy
from scrapy import FormRequest, Selector, Request
from scrapy import Item, Field
from scrapy.utils.response import open_in_browser
from scrapy.shell import inspect_response
from blackboard_scrapper.items import DowloadItem


class DocumentsSpider(scrapy.Spider):
    name = 'documents'
    login_url = "/webapps/login/"
    course_mod = '/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_1_1&forwardUrl=edit_module%2F_4_1%2Fbbcourseorg%3Fcmd%3Dedit&recallUrl=%2Fwebapps%2Fportal%2Fexecute%2Ftabs%2FtabAction%3Ftab_tab_group_id%3D_1_1'
    rest_api = {'login': "/webapps/login/",
                'courses': "/learn/api/public/v1/users/%s/courses",
                'course_contents': "/learn/api/public/v1/courses/%s/contents",
                'children': "/learn/api/public/v1/courses/%s/contents/%s/children",
                'contents': "/webapps/blackboard/content/listContent.jsp?course_id=%s&content_id=%s"}
    user_id = None

    custom_settings = {
        'ITEM_PIPELINES': {
            'blackboard_scrapper.pipelines.MyFilePipeline': 1
        },
        'FILES_STORE': 'storage/files'
    }
    def start_requests(self):
        self.blackboard_base_url = raw_input("Please enter your Blackboard base url (eg. https://blackboard.utwente.nl):\n")
        username = raw_input("Please enter your Blackboard username:\n")  
        password = raw_input("Plase enter your Blackboard password:\n") 
        print "Attempting login"
        next_page = self.blackboard_base_url + self.login_url
        yield FormRequest(next_page,
                          formdata={'user_id': username,
                                    'password': password},
                          callback=self.goto_course_listing)

    def goto_course_listing(self, response):
        # TODO: Check if login was correct
        next_page = self.blackboard_base_url + self.course_mod
        yield Request(next_page, callback=self.inspect_course_listing)

    def inspect_course_listing(self, response):
        # get id of table that contains student ID
        table_id = response.selector.xpath('//table[@class="attachments"]/@id').extract_first()
        student_id = re.search('(?<=Student).*', table_id).group(0)
        if student_id:
            self.user_id = student_id
        else:
            raise Exception("Unable to retrieve userID")
        course_table_ids = response.selector.xpath('//tbody[@id="%s_body"]/tr/@id').extract()
        # TODO: loop trough courses, to possibly make crawler api independent
        next_page = response.urljoin(self.rest_api['courses'] % self.user_id)
        yield Request(next_page,
                      method='GET',
                      callback=self.parse_course_list)
   
    def parse_course_list(self, response):
        '''Recursively check list of all courses, check availability, pass on course
        for further processing'''
        result = json.loads(response.body_as_unicode())
        for course in result['results']:
            if course['availability']['available'] == 'Yes':
                course_id = course['courseId']
                next_page = self.rest_api['course_contents'] % course_id
                next_page = response.urljoin(next_page)
                request = Request(next_page,
                                  method='GET',
                                  callback=self.parse_course_contents)
                request.meta['course_id'] = course_id
                request.meta['folder'] = [] # initialize folder array
                yield request
        if 'paging' in result:
            next_page = response.urljoin(result['paging']['nextPage'])
            yield Request(next_page,
                          method='GET',
                          callback=self.parse_course_list)

    def parse_course_contents(self, response):
        result = json.loads(response.body_as_unicode())
        for content in result['results']:
            content_id = content['id']
            course_id = response.meta['course_id']
            # Folder, handle recursively
            if ('hasChildren' in content.keys() and
                content['availability']['available'] == 'Yes'):
                next_page = self.rest_api['children'] % (course_id, content_id)
                next_page = self.blackboard_base_url + next_page
                next_folder = response.meta['folder']+ [content['title']]

                request = Request(next_page,
                                  self.parse_course_contents)
                request.meta['course_id'] = course_id
                request.meta['content_id'] = content_id
                request.meta['folder'] = next_folder
                yield request

                # Also scrape page for documents
                url = self.rest_api['contents'] % (course_id, content_id)
                url = self.blackboard_base_url + url
                request = Request(url,
                                self.parse_attachments)
                request.meta['folder'] = next_folder
                yield request

    def parse_attachments(self, response):
        link_extractor = '//ul[contains(@class,"attachments")]/li/a/'
        course_name = response.selector.xpath('//a[@id="courseMenu_link"]/text()').extract()
        attachments =  response.selector.xpath(link_extractor + '@href').extract()
        file_names = response.selector.xpath(link_extractor + 'text()').extract()
        folder = response.meta['folder']
        urls = [self.blackboard_base_url + file_url for file_url in attachments]

        for i, url in enumerate(urls):
            yield DowloadItem(
                file_urls=[url],
                course = course_name,
                file_names = file_names[i].replace(u'\xa0', u' ').lstrip(),
                folder = folder
                )
