#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""

轻国旧站爬虫，获取全部日轻，包含插图
author by chaocai 
	
"""

from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests, sys, os, re, socket, uuid
 
class downloader():
	
    def __init__(self):
        #列表页地址前缀
        self.list_url = 'https://obsolete.lightnovel.us/forum-173-'
		#self.list_url = 'https://obsolete.lightnovel.us/forum-4-'
        #书籍页地址前缀
        self.book_url = 'https://obsolete.lightnovel.us/forum.php?mod=viewthread'
        #列表开始页码，从1开始
        self.list_start_page = 1
        #列表结束页码，需要加1
        self.list_end_page = 12
		#self.list_end_page = 400
        #设置请求默认重试次数
        self.http_retry = 2
        #设置请求超时时间
        self.http_timeout = 15
        #通用报错标识
        self.error_flag = 'error'
        #代理开关 0关1开
        self.proxy_switch = 1
        #楼层计数，用于给txt起名
        self.chapter_count = 1
        #登录cookie
        self.cookie = ''
        
    def main(self):
        """ 
		
        主函数 
		
        """
        #全局禁用https安全请求警告
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        #全局socket超时，防止卡死，并推荐阿里dns
        socket.setdefaulttimeout(20)
        for i in range(self.list_start_page, self.list_end_page):
            #遍历列表页
            print('开始获取列表，第' + str(i) + '页')
            try:
                list_html = self.get_request_html(self.list_url + str(i) + '.html')
            except Exception as e:
                print('请求列表出错：' + str(e))
                continue
            else:
                book_div_list = self.get_div_list(list_html, 'list')
                if book_div_list == self.error_flag:
                    continue
                else:
                    for book in book_div_list:
                        book_tag = self.get_book_div(book)
                        book_name = book_tag.string
                        book_id = str(book_tag['href'])
                        book_id = re.findall(r"thread-(.+?)-",book_id)[0]
                        book_author = str(book.find_all('cite')[0].a['href'])
                        book_author = re.findall(r"space-uid-(.+?)\.",book_author)[0]
                        book_url = self.book_url + '&tid=' + book_id + '&authorid=' + book_author
                        book_page = 1
                        self.get_chapter_list(book_name, book_url, book_page)
					   
    def get_request_html(self, url):
        """
		
        通用请求方法
        参数：url 请求地址
        返回：html 响应页面html
			
        """
        #构造请求头
        headers = {
			"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
			"Cookie": self.cookie
        }
        #设置翻墙的代理，v2ray为socks5端口+1
        proxies = {'http':'http://127.0.0.1:1081','https':'http://127.0.0.1:1081'}
        session = requests.Session()
        session.mount('http://', HTTPAdapter(max_retries=self.http_retry))
        session.mount('https://', HTTPAdapter(max_retries=self.http_retry))
        if self.proxy_switch == 0:
            request = session.get(url, verify=False, headers=headers, timeout=self.http_timeout)
        else:
            request = session.get(url, verify=False, headers=headers, proxies=proxies, timeout=self.http_timeout)
        html = request.text
        return html
	
    def get_div_list(self, html, type):
        """

        通用获取列表div list方法
        参数：html
              type 类型 'list' 列表中书籍div的list 'book' 书籍中章节div的list
        返回：div_list 列表tag
              
        """
        try:
            bf = BeautifulSoup(html)
            if type == 'list':
                div_list = bf.find_all('tbody',id = re.compile("^normalthread"))        
            else:
                div_list = bf.find_all('div',id = re.compile("^post_"))
            return div_list
        except Exception as e:
            print('获取' + type + '_div_list出错：' + str(e))
            return self.error_flag
			
    def get_book_div(self, tag):
        """
        
        进一步解析书籍div
        参数：tag 列表tag
        返回：book_div 书籍tag 
              
        """
        try:
            book_div = tag.tr.th.find_all('a',onclick = 'atarget(this)')[0]
            return book_div
        except Exception as e:
            print('获取列表书籍tag出错：' + str(e))
            return self.error_flag
			
		
    def get_book_page(self, html):
        """
        
        解析书籍页数
        参数：html 书籍html 
              name 书籍名称
              
        """
        try:
            bf = BeautifulSoup(html)
            page = bf.find_all('div',class_ = 'pg')[0].label.span.string
            page = int(re.sub("\D", "", page))
            return page
        except Exception as e:
            return 1
			
    def get_chapter_list(self, name, url, page):
        """
        
        解析书籍章节列表
        参数：name 书名 
              url 书籍地址
              page 书籍页码，用于拼接url
			  
        """
        print('开始获取书籍：' + name)
        self.mkdir(name)
        try:
            book_html = self.get_request_html(url)
        except Exception as e:
            print('请求书籍出错：' + str(e))
        else:    
            page = self.get_book_page(book_html) + 1
			#初始化楼层计数
            self.chapter_count = 1
            for book_page in range(1, page):
                print('开始获取第：' + str(book_page) + '页||||地址：' + url + '&page=' + str(book_page))
                page_url = url + '&page=' + str(book_page)
                page_html = self.get_request_html(page_url)
                chapter_div_list = self.get_div_list(page_html, 'book')
                for chapter in chapter_div_list :
                    try:
                        chapter_tag = chapter.find_all('td', id = re.compile("^postmessage_"))[0]
                        self.get_content(chapter_tag, name)
                    except Exception as e:
                        print('')

    def get_pic_list(self, tag, book_path):
        """
        
        解析章节内容图片
        参数：tag 章节内容tag
              book_path 书籍路径
        """
        try:
            div_list = tag.find_all('img')   
            for pic in div_list:
                print(pic)
                pic_src = str(pic['file'])
				#图片名为uuid，有可能会重复下载，由于没多少图片，自行筛选吧
                pic_name = str(uuid.uuid1()) + '.jpg'
                self.download_img(book_path + pic_name, pic_src)
        except Exception as e:
            print('获取图片出错：' + str(e))		  

    def get_content(self, tag, book_name):
        """
        
        解析书籍内容
        参数：tag 楼层tag
              book_name 书名
              
        """
        print('开始获取楼层：' + str(self.chapter_count) + '层||||书籍：' + book_name)
        #排除非法字符
        book_name = re.sub('[\:/*?."<>|]','',book_name)
        chapter_name = str(self.chapter_count)
        #文件校验，存在文件跳过，防止重复请求地址消耗资源
        if os.path.exists(book_name + '/' + chapter_name + '.txt'):
            print('已存在楼层' + chapter_name + '||||书籍：' + book_name)
            return
        try:
            self.get_pic_list(tag, book_name + '/')
            #去除nbsp空白符
            result = tag.text.replace('\xa0'*8,'\n\n')
            self.write(book_name + '/' + chapter_name + '.txt', result)
        except Exception as e:
            print('获取正文出错' + str(e))
        finally:
            self.chapter_count = self.chapter_count + 1
 
    def write(self, path, text):
        """
        
        通用写入文件方法
        参数：path 文件路径
              
        """
        #排除非法字符
        path = re.sub('[\:*?"<>|]','',path)
        #文件存在时跳过，防止重复写入
        if os.path.exists(path):
            return
        try:
            file = open(path, 'w')
            file.close()
        except Exception as e:
            print('创建文件出错' + str(e))
        else:
            with open(path, 'a' , encoding = 'utf-8') as f:
                f.writelines(text)
            
    def mkdir(self, path):
        """
        
        通用创建文件夹方法
        参数：path 文件夹路径
              
        """
        #排除非法字符
        path = re.sub('[\:/*?."<>|]','', path)
        folder = os.path.exists(path)
        if not folder:
            try:
                os.makedirs(path)  
            except Exception as e:
                print('创建文件夹出错：' + str(e))

    def download_img(self, path, src):
        """
        
        通用图片下载方法
        参数：path 下载图片路径
              src 图片地址
              
        """
        print('下载图片：' + src)
        #排除非法字符
        path = re.sub('[\:*?"<>|]','', path)
        #校验图片地址，防止重复写入图片
        if os.path.exists(path):
            return
        try:
            #构造请求头
            headers = {
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
                "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-encoding":"gzip, deflate, br",
                "Accept-Language":"zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection":"keep-alive"
            }
            #设置翻墙的代理，v2ray为socks5端口+1
            proxies = {'http':'http://127.0.0.1:1081','https':'http://127.0.0.1:1081'}
            session = requests.Session()
            session.mount('http://', HTTPAdapter(max_retries=self.http_retry))
            session.mount('https://', HTTPAdapter(max_retries=self.http_retry))
            if self.proxy_switch == 0:
                request = session.get(src, verify=False, headers=headers, timeout=self.http_timeout)
            else:
                request = session.get(src, verify=False, headers=headers, proxies=proxies, timeout=self.http_timeout)
        except Exception as e:
            print('图片下载出错' + str(e))
        else:
            fp = open(path, 'wb')
            fp.write(request.content)
            fp.close()
 
dl = downloader()
dl.main()
