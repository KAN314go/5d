# coding=utf-8
#!/usr/bin/python
import sys
sys.path.append('..')
from base.spider import Spider
import json
import time
import urllib.parse
import re
import requests
from lxml import etree
from urllib.parse import urljoin

class Spider(Spider):
    
    def getName(self):
        return "苹果视频"
    
    def init(self, extend=""):
        self.host = "https://618041.xyz"
        self.api_host = "https://h5.xxoo168.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': self.host
        }
        self.special_categories = ['13', '14', '33', '53', '32', '52', '9']
        self.classes = [
            {'type_id': '618041.xyz_1', 'type_name': '全部视频'},
            {'type_id': '618041.xyz_13', 'type_name': '香蕉精品'},
            {'type_id': '618041.xyz_22', 'type_name': '制服诱惑'},
            {'type_id': '618041.xyz_6', 'type_name': '国产视频'},
            {'type_id': '618041.xyz_8', 'type_name': '清纯少女'},
            {'type_id': '618041.xyz_9', 'type_name': '辣妹大奶'},
            {'type_id': '618041.xyz_10', 'type_name': '女同专属'},
            {'type_id': '618041.xyz_11', 'type_name': '素人出演'},
            {'type_id': '618041.xyz_12', 'type_name': '角色扮演'},
            {'type_id': '618041.xyz_20', 'type_name': '人妻熟女'},
            {'type_id': '618041.xyz_23', 'type_name': '日韩剧情'},
            {'type_id': '618041.xyz_21', 'type_name': '经典伦理'},
            {'type_id': '618041.xyz_7', 'type_name': '成人动漫'},
            {'type_id': '618041.xyz_14', 'type_name': '精品二区'},
            {'type_id': '618041.xyz_53', 'type_name': '动漫中字'},
            {'type_id': '618041.xyz_52', 'type_name': '日本无码'},
            {'type_id': '618041.xyz_33', 'type_name': '中文字幕'},
            {'type_id': '618041.xyz_32', 'type_name': '国产自拍'}
        ]
        self.log(f"苹果视频爬虫初始化完成，主站: {self.host}")

    def html(self, content):
        try:
            return etree.HTML(content)
        except:
            self.log("HTML解析失败")
            return None

    def regStr(self, pattern, string, index=1):
        try:
            match = re.search(pattern, string, re.IGNORECASE)
            if match and len(match.groups()) >= index:
                return match.group(index)
        except:
            pass
        return ""

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def _get_classes(self):
        return self.classes

    def homeContent(self, filter):
        result = {'class': self._get_classes()}
        try:
            rsp = self.fetch(self.host, headers=self.headers)
            doc = self.html(rsp.text)
            videos = self._get_videos(doc, limit=20)
            result['list'] = videos
        except Exception as e:
            self.log(f"首页获取出错: {str(e)}")
            result['list'] = []
        return result

    def homeVideoContent(self):
        return {'class': self._get_classes()}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            domain, type_id = tid.split('_')
            url = f"https://{domain}/index.php/vod/type/id/{type_id}.html"
            if pg and pg != '1':
                url = url.replace('.html', f'/page/{pg}.html')
            self.log(f"访问分类URL: {url}")
            rsp = self.fetch(url, headers=self.headers)
            doc = self.html(rsp.text)
            videos = self._get_videos(doc, category_id=type_id, limit=20)
            pagecount = 999
            total = 19980
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 20,
                'total': total
            }
        except Exception as e:
            self.log(f"分类内容获取出错: {str(e)}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            search_url = f"{self.host}/index.php/vod/type/id/1/wd/{urllib.parse.quote(key)}/page/{pg}.html"
            self.log(f"搜索URL: {search_url}")
            rsp = self.fetch(search_url, headers=self.headers)
            if not rsp or rsp.status_code != 200:
                self.log("搜索请求失败")
                return {'list': []}
            doc = self.html(rsp.text)
            if not doc:
                self.log("搜索页面解析失败")
                return {'list': []}
            videos = self._get_videos(doc, limit=20)
            pagecount = 5
            total = 100
            page_elements = doc.xpath('//div[@class="mypage"]/a')
            if page_elements:
                try:
                    last_page = None
                    for elem in page_elements:
                        href = elem.xpath('./@href')[0]
                        if '尾页' in elem.text or 'page/' in href:
                            last_page = href
                            break
                    if last_page:
                        page_match = re.search(r'/page/(\d+)\.html', last_page)
                        if page_match:
                            pagecount = int(page_match.group(1))
                            total = pagecount * 20
                except:
                    pass
            return {
                'list': videos,
                'page': int(pg),
                'pagecount': pagecount,
                'limit': 20,
                'total': total
            }
        except Exception as e:
            self.log(f"搜索出错: {str(e)}")
            return {'list': []}

    def detailContent(self, ids):
        try:
            vid = ids[0]
            if vid.startswith('special_'):
                parts = vid.split('_')
                if len(parts) >= 4:
                    category_id = parts[1]
                    video_id = parts[2]
                    encoded_url = '_'.join(parts[3:])
                    play_url = urllib.parse.unquote(encoded_url)
                    self.log(f"特殊分区视频，直接使用链接: {play_url}")
                    parsed_url = urllib.parse.urlparse(play_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    video_url = query_params.get('v', [''])[0]
                    pic_url = query_params.get('b', [''])[0]
                    title_encrypted = query_params.get('m', [''])[0]
                    title = self._xor128(title_encrypted)
                    desc = query_params.get('desc', ['暂无简介'])[0]
                    self.log(f"特殊分区标题解密: {title}, 简介: {desc}")
                    return {
                        'list': [{
                            'vod_id': vid,
                            'vod_name': title,
                            'vod_pic': pic_url,
                            'vod_remarks': '',
                            'vod_year': '',
                            'vod_content': desc,
                            'vod_play_from': '直接播放',
                            'vod_play_url': f"第1集${play_url}"
                        }]
                    }
            if '_' in vid and len(vid.split('_')) > 2:
                domain, category_id, video_id = vid.split('_')
            else:
                domain, video_id = vid.split('_')
            detail_url = f"https://{domain}/index.php/vod/detail/id/{video_id}.html"
            self.log(f"访问详情URL: {detail_url}")
            rsp = self.fetch(detail_url, headers=self.headers)
            doc = self.html(rsp.text)
            video_info = self._get_detail(doc, rsp.text, vid)
            if video_info:
                self.log(f"详情页面提取标题: {video_info['vod_name']}, 简介: {video_info['vod_content']}")
            return {'list': [video_info]} if video_info else {'list': []}
        except Exception as e:
            self.log(f"详情获取出错: {str(e)}")
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            self.log(f"获取播放链接: flag={flag}, id={id}")
            result = {'parse': 0, 'playUrl': '', 'url': '', 'title': '', 'desc': ''}
            info = self._fetch_detail_info(id)
            result.update({'title': info['title'], 'desc': info['desc']})
            self.log(f"播放页标题: {result['title']}, 简介: {result['desc']}")

            if id.startswith('special_'):
                parts = id.split('_')
                if len(parts) >= 4:
                    category_id = parts[1]
                    video_id = parts[2]
                    encoded_url = '_'.join(parts[3:])
                    play_url = urllib.parse.unquote(encoded_url)
                    self.log(f"特殊分区视频，直接使用链接: {play_url}")
                    parsed_url = urllib.parse.urlparse(play_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    video_url = query_params.get('v', [''])[0]
                    if video_url:
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        elif not video_url.startswith('http'):
                            video_url = urljoin(self.host, video_url)
                        self.log(f"从特殊链接中提取到视频地址: {video_url}")
                        result.update({'url': video_url})
                        return result

            if id.startswith('http'):
                self.log("ID 是一个完整URL，直接解析参数")
                parsed_url = urllib.parse.urlparse(id)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                video_url = query_params.get('v', [''])[0]
                if not video_url:
                    for key in query_params:
                        if key in ['url', 'src', 'file']:
                            video_url = query_params[key][0]
                            break
                if video_url:
                    video_url = urllib.parse.unquote(video_url)
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    elif not video_url.startswith('http'):
                        video_url = urljoin(self.host, video_url)
                    self.log(f"从 URL 参数中提取到视频地址: {video_url}")
                    result.update({'url': video_url})
                    return result
                else:
                    self.log("URL 中没有找到视频参数，尝试从页面提取")
                    rsp = self.fetch(id, headers=self.headers)
                    if rsp and rsp.status_code == 200:
                        video_url = self._extract_direct_video_url(rsp.text)
                        if video_url:
                            self.log(f"从页面提取到视频地址: {video_url}")
                            result.update({'url': video_url})
                            return result
                    self.log("无法从页面提取视频链接，返回原始URL")
                    result.update({'parse': 1, 'url': id})
                    return result

            if id.count('_') >= 2:
                parts = id.split('_')
                video_id = parts[-1]
                category_id = parts[1]
            else:
                video_id = id.split('_')[-1]
                category_id = ''

            self.log(f"视频ID: {video_id}, 分类ID: {category_id}")

            if category_id in self.special_categories:
                self.log("特殊分类，尝试从详情页提取直接播放链接")
                play_page_url = f"{self.host}/index.php/vod/play/id/{video_id}.html"
                rsp = self.fetch(play_page_url, headers=self.headers)
                if rsp and rsp.status_code == 200:
                    video_url = self._extract_direct_video_url(rsp.text)
                    if video_url:
                        self.log(f"从播放页面提取到视频地址: {video_url}")
                        result.update({'url': video_url})
                        return result
                self.log("从播放页面提取失败，尝试API方式")
                return self._get_video_by_api(id, video_id, result)
            else:
                self.log("使用API方式获取视频地址")
                return self._get_video_by_api(id, video_id, result)

        except Exception as e:
            self.log(f"播放链接获取出错: {str(e)}")
            if '_' in id:
                domain, play_id = id.split('_')
                play_url = f"https://{domain}/html/kkyd.html?m={play_id}"
            else:
                play_url = f"{self.host}/html/kkyd.html?m={id}"
            result.update({'parse': 1, 'url': play_url})
            return result

    def _fetch_detail_info(self, id):
        try:
            parsed = urllib.parse.urlparse(id)
            params = urllib.parse.parse_qs(parsed.query)
            if 'vv' in params:
                encrypted = params['vv'][0]
                title = self._xor128(encrypted)
            else:
                title = self._xor128(params.get('m', [''])[0])
            desc = params.get('desc', ['暂无简介'])[0]
            pic = params.get('b', [''])[0]
            return {
                'title': title or '未知标题',
                'desc': desc,
                'pic': pic
            }
        except Exception as e:
            self.log(f"获取详情信息出错: {str(e)}")
            return {
                'title': '未知标题',
                'desc': '暂无简介',
                'pic': ''
            }

    def _xor128(self, text):
        try:
            return ''.join(chr(128 ^ ord(c)) for c in text)
        except:
            return text

    def _get_video_by_api(self, id, video_id, result):
        try:
            api_url = f"{self.api_host}/api/v2/vod/reqplay/{video_id}"
            self.log(f"请求API获取视频地址: {api_url}")
            api_headers = self.headers.copy()
            api_headers.update({
                'Referer': f"{self.host}/",
                'Origin': self.host,
                'X-Requested-With': 'XMLHttpRequest'
            })
            api_response = self.fetch(api_url, headers=api_headers)
            if api_response and api_response.status_code == 200:
                data = api_response.json()
                self.log(f"API响应: {data}")
                if data.get('retcode') == 3:
                    video_url = data.get('data', {}).get('httpurl_preview', '')
                else:
                    video_url = data.get('data', {}).get('httpurl', '')
                if video_url:
                    video_url = video_url.replace('?300', '')
                    self.log(f"从API获取到视频地址: {video_url}")
                    result.update({'url': video_url})
                    return result
                else:
                    self.log("API响应中没有找到视频地址")
            else:
                self.log(f"API请求失败，状态码: {api_response.status_code if api_response else '无响应'}")
            if '_' in id:
                domain, play_id = id.split('_')
                play_url = f"https://{domain}/html/kkyd.html?m={play_id}"
            else:
                play_url = f"{self.host}/html/kkyd.html?m={id}"
            self.log(f"API请求失败，回退到播放页面: {play_url}")
            result.update({'parse': 1, 'url': play_url})
            return result
        except Exception as e:
            self.log(f"API方式获取视频出错: {str(e)}")
            if '_' in id:
                domain, play_id = id.split('_')
                play_url = f"https://{domain}/html/kkyd.html?m={play_id}"
            else:
                play_url = f"{self.host}/html/kkyd.html?m={id}"
            result.update({'parse': 1, 'url': play_url})
            return result

    def _extract_direct_video_url(self, html_content):
        try:
            patterns = [
                r'v=([^&]+\.(?:m3u8|mp4))',
                r'"url"\s*:\s*["\']([^"\']+\.(?:mp4|m3u8))["\']',
                r'src\s*=\s*["\']([^"\']+\.(?:mp4|m3u8))["\']',
                r'http[^\s<>"\'?]+\.(?:mp4|m3u8)'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    extracted_url = match.replace('\\', '')
                    extracted_url = urllib.parse.unquote(extracted_url)
                    if extracted_url.startswith('//'):
                        extracted_url = 'https:' + extracted_url
                    elif extracted_url.startswith('http'):
                        return extracted_url
            return None
        except Exception as e:
            self.log(f"提取直接播放URL出错: {str(e)}")
            return None

    def _get_videos(self, doc, category_id=None, limit=None):
        try:
            videos = []
            elements = doc.xpath('//a[@class="vodbox"]')
            self.log(f"找到 {len(elements)} 个vodbox元素")
            for elem in elements:
                video = self._extract_video(elem, category_id)
                if video:
                    videos.append(video)
            return videos[:limit] if limit and videos else videos
        except Exception as e:
            self.log(f"获取影片列表出错: {str(e)}")
            return []

    def _extract_video(self, element, category_id=None):
        try:
            link = element.xpath('./@href')[0]
            if link.startswith('/'):
                link = self.host + link
            is_special_link = 'ar-kk.html' in link or 'ar.html' in link
            if is_special_link and category_id in self.special_categories:
                parsed_url = urllib.parse.urlparse(link)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                video_url = query_params.get('v', [''])[0]
                if video_url:
                    video_id_match = re.search(r'/([a-f0-9-]+)/video\.m3u8', video_url)
                    if video_id_match:
                        video_id = video_id_match.group(1)
                    else:
                        video_id = str(hash(link) % 1000000)
                else:
                    video_id = str(hash(link) % 1000000)
                final_vod_id = f"special_{category_id}_{video_id}_{urllib.parse.quote(link)}"
            else:
                vod_id = self.regStr(r'm=(\d+)', link)
                if not vod_id:
                    vod_id = str(hash(link) % 1000000)
                final_vod_id = f"618041.xyz_{vod_id}"
                if category_id:
                    final_vod_id = f"618041.xyz_{category_id}_{vod_id}"
            title_elem = element.xpath('.//p[@class="km-script"]/text()')
            if not title_elem:
                title_elem = element.xpath('.//p[contains(@class, "script")]/text()')
                if not title_elem:
                    title_elem = element.xpath('.//p/text()')
                    if not title_elem:
                        title_elem = element.xpath('.//h3/text()')
                        if not title_elem:
                            title_elem = element.xpath('.//h4/text()')
                            if not title_elem:
                                self.log(f"未找到标题元素，跳过该视频")
                                return None
            title_encrypted = title_elem[0].strip()
            title = self._xor128(title_encrypted)
            self.log(f"提取视频标题: {title}")
            pic_elem = element.xpath('.//img/@data-original')
            if not pic_elem:
                pic_elem = element.xpath('.//img/@src')
            pic = pic_elem[0] if pic_elem else ''
            if pic:
                if pic.startswith('//'):
                    pic = 'https:' + pic
                elif pic.startswith('/'):
                    pic = self.host + pic
            return {
                'vod_id': final_vod_id,
                'vod_name': title,
                'vod_pic': pic,
                'vod_remarks': '',
                'vod_year': ''
            }
        except Exception as e:
            self.log(f"提取影片信息出错: {str(e)}")
            return None

    def _get_detail(self, doc, html_content, vid):
        try:
            title_encrypted = self._get_text(doc, ['//h1/text()', '//title/text()', '//h2/text()', '//h3/text()'])
            title = self._xor128(title_encrypted)
            pic = self._get_text(doc, ['//div[contains(@class,"dyimg")]//img/@src', '//img[contains(@class,"poster")]/@src'])
            if pic and pic.startswith('/'):
                pic = self.host + pic
            desc = self._get_text(doc, ['//div[contains(@class,"yp_context")]/text()', '//div[contains(@class,"introduction")]//text()', '//p[contains(@class,"description")]/text()'])
            actor = self._get_text(doc, ['//span[contains(text(),"主演")]/following-sibling::*/text()'])
            director = self._get_text(doc, ['//span[contains(text(),"导演")]/following-sibling::*/text()'])
            play_from = []
            play_urls = []
            player_link_patterns = [
                re.compile(r'href="(.*?ar\.html.*?)"'),
                re.compile(r'href="(.*?kkyd\.html.*?)"'),
                re.compile(r'href="(.*?ar-kk\.html.*?)"')
            ]
            player_links = []
            for pattern in player_link_patterns:
                matches = pattern.findall(html_content)
                player_links.extend(matches)
            if player_links:
                episodes = []
                for link in player_links:
                    full_url = urljoin(self.host, link)
                    episodes.append(f"第1集${full_url}")
                if episodes:
                    play_from.append("默认播放源")
                    play_urls.append('#'.join(episodes))
            if not play_from:
                self.log("未找到播放源元素，无法定位播放源列表")
                return {
                    'vod_id': vid,
                    'vod_name': title,
                    'vod_pic': pic,
                    'type_name': '',
                    'vod_year': '',
                    'vod_area': '',
                    'vod_remarks': '',
                    'vod_actor': actor,
                    'vod_director': director,
                    'vod_content': desc,
                    'vod_play_from': '默认播放源',
                    'vod_play_url': f"第1集${vid}"
                }
            return {
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': pic,
                'type_name': '',
                'vod_year': '',
                'vod_area': '',
                'vod_remarks': '',
                'vod_actor': actor,
                'vod_director': director,
                'vod_content': desc,
                'vod_play_from': '$$$'.join(play_from),
                'vod_play_url': '$$$'.join(play_urls)
            }
        except Exception as e:
            self.log(f"获取详情出错: {str(e)}")
            return None

    def _get_text(self, doc, selectors):
        for selector in selectors:
            try:
                texts = doc.xpath(selector)
                for text in texts:
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return ''

    def log(self, message):
        print(f"[苹果视频] {message}")

    def fetch(self, url, headers=None, method='GET', data=None, timeout=10):
        try:
            if headers is None:
                headers = self.headers
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            else:
                response = requests.post(url, headers=headers, data=data, timeout=timeout, verify=False)
            return response
        except Exception as e:
            self.log(f"网络请求失败: {url}, 错误: {str(e)}")
            return None

if __name__ == '__main__':
    from base.spider import Spider as BaseSpider
    BaseSpider.register(Spider())
