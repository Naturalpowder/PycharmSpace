import requests
from lxml import etree
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from lxml import html as h

filePath = 'C:/Users/96206/Desktop/ArchDaily/residential-architecture/'
url = 'https://dashboard.gooood.cn/api/wp/v2/posts?page=%d&per_page=20'
detail_url = 'https://www.gooood.cn/%s.htm'
keyword = 'residential-architecture'
search_type = 'type'
header_base = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'cookie': 'language=zh_CN',
}


class ArchDaily:
    def __init__(self):
        search = Search()
        serial = search.search_dict(search_type, keyword)
        self.params = {search_type: serial}

    def main_page(self, page):
        url_page = url % page
        request = requests.get(url_page, self.params, headers=header_base)
        request.encoding = 'utf-8'
        lib = json.loads(request.text.replace('&#8211', '-'))
        self.parse(lib)

    def parse(self, lib):
        for item in lib:
            arrs = item['gallery']
            info = {'title': item['title']['rendered'],
                    'cover': item['featured_image']['source_url'],
                    'url': detail_url % item['slug'],
                    'full_img': [arrs[index]['full_url'] for index in range(len(arrs))]
                    }
            # self.parse_content(info['title'], item['content']['rendered'])
            # self.detail_page(info['url'])
            path = self.mkdir(filePath, item['slug'])
            arrs = info['full_img']
            with ThreadPoolExecutor(max_workers=100) as executor:
                tasks = [executor.submit(self.image_download, img_href, path, str(arrs.index(img_href))) for img_href in
                         arrs]
                for task in as_completed(tasks):
                    task.result()

    @staticmethod
    def image_download(img_href, folder, name):
        path = folder + name + '.jpg'
        if not os.path.exists(path):
            r = requests.get(img_href, header_base)
            with open(path, 'wb') as f:
                f.write(r.content)

    @staticmethod
    def parse_content(title, content):
        print('----%s----' % title)
        doc = h.fromstring(content)
        arrs = doc.xpath('//p/text()')
        result = []
        for item in arrs:
            if '▼' in item:
                result.append(item)
        print('title=' + str(len(result)))
        # print(etree.tostring(doc))
        imgs = doc.xpath('//a[@class="colorbox_gallery"]/img')
        print('imgs=' + str(len(imgs)))
        print(imgs[0])

    @staticmethod
    def detail_page(href):
        print(href)
        params = {'lang': 'cn'}
        request = requests.get(href, params, headers=header_base)
        request.encoding = 'utf-8'
        doc = h.fromstring(request.text)
        arrs = doc.xpath('//p/text()')
        for item in arrs:
            if '▼' in item:
                print(item)
        imgs = doc.xpath('//a[@class="colorbox_gallery"]/img/@src')
        print(imgs)

    @staticmethod
    def mkdir(path, name):
        folder = os.path.exists(path + name)
        if not folder:
            os.makedirs(path + name)
            print('----Create New Folder:%s----' % name)
        else:
            print('----Existed!----')
        return path + name + '/'


class Search:
    def __init__(self):
        self.library = {'type': self.url_dict(key='type', max_value=3),
                        'material': self.url_dict(key='material', max_value=4),
                        'country': self.url_dict(key='country', max_value=2)}

    @staticmethod
    def url_dict(key, max_value):
        return ['https://dashboard.gooood.cn/api/wp/v2/%s?page=%d&per_page=100&hide_empty=true' % (key, num + 1) for
                num in range(max_value)]

    def search_dict(self, key, select_type):
        result = -1
        values = self.library[key]
        for href in values:
            request = requests.get(href, header_base)
            id_dict = self.parse_json(request.text)
            temp = id_dict.get(select_type)
            if temp is not None:
                result = temp
        return result

    @staticmethod
    def parse_json(text):
        result = {}
        lib = json.loads(text)
        for value in lib:
            result[value['slug']] = value['id']
        return result


if __name__ == '__main__':
    archdaily = ArchDaily()
    for i in range(20):
        archdaily.main_page(i + 1)
