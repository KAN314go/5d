# -*- coding: utf-8 -*-
# 修复版：搜索功能 + 播放链接 + 分类 + 首页推荐 - 适配 634.tv
import sys
sys.path.append('..')
from base.spider import Spider
from bs4 import BeautifulSoup
import requests
import re
import json
import time
import html
import urllib.parse

class Spider(Spider):

    def init(self, extend=""):
        self.host = "https://www.634.tv"
        self.proxy_base = "https://jjpz.hafrey.dpdns.org/?url="
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': self.host,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }

    def getName(self):
        return "634.tv"

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def get_html(self, url):
        try:
            encoded_url = urllib.parse.quote(url)
            proxy_url = self.proxy_base + encoded_url
            res = requests.get(proxy_url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            return res.text
        except Exception as e:
            print(f"获取 {url} 失败: {str(e)}")
            return ""

    def unescape_js_string(self, s):
        try:
            s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
            s = s.replace('\\/', '/').replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
            s = s.replace('\\"', '"').replace("\\'", "'")
            return s
        except:
            return s

    def extract_player_data(self, html_content):
        try:
            player_patterns = [
                r'var\s+player_aaaa\s*=\s*({.*?});',
                r'player_aaaa\s*=\s*({.*?});',
                r'var\s+player_\w+\s*=\s*({.*?});'
            ]
            for pattern in player_patterns:
                match = re.search(pattern, html_content, re.DOTALL)
                if match:
                    player_str = match.group(1)
                    try:
                        player_str = self.unescape_js_string(player_str)
                        player_data = json.loads(player_str)
                        return player_data
                    except:
                        url_match = re.search(r'"url"\s*:\s*"([^"]+)"', player_str)
                        if url_match:
                            return {'url': self.unescape_js_string(url_match.group(1))}
            iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+player[^"\']*)["\']', html_content)
            if iframe_match:
                iframe_src = iframe_match.group(1)
                if 'url=' in iframe_src:
                    url_match = re.search(r'url=([^&]+)', iframe_src)
                    if url_match:
                        video_url = html.unquote(url_match.group(1))
                        return {'url': video_url}
            url_patterns = [
                r'"url"\s*:\s*"([^"]+)"',
                r"url\s*:\s*'([^']+)'",
                r'var\s+url\s*=\s*"([^"]+)"',
                r"var\s+url\s*=\s*'([^']+)'"
            ]
            for pattern in url_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if '.m3u8' in match or '.mp4' in match:
                        return {'url': self.unescape_js_string(match)}
            return {}
        except Exception as e:
            print(f"提取播放器数据失败: {str(e)}")
            return {}

    def homeContent(self, filter):
        classes = [
            {"type_name": "麻豆视频", "type_id": "1"},
            {"type_name": "日本视频", "type_id": "2"},
            {"type_name": "欧美视频", "type_id": "3"},
            {"type_name": "动漫视频", "type_id": "4"},
            {"type_name": "国产视频", "type_id": "5"}
        ]
        filters = {
            "1": [
                {"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    {"n": "麻豆原创", "v": "6"},
                    {"n": "91制片厂", "v": "7"},
                    {"n": "天美传媒", "v": "8"},
                    {"n": "蜜桃影像", "v": "9"},
                    {"n": "星空传媒", "v": "10"},
                    {"n": "皇家华人", "v": "11"},
                    {"n": "精东影业", "v": "12"},
                    {"n": "乐播传媒", "v": "13"},
                    {"n": "成人头条", "v": "14"},
                    {"n": "兔子先生", "v": "15"},
                    {"n": "杏吧原创", "v": "16"},
                    {"n": "玩偶姐姐", "v": "17"},
                    {"n": "糖心Vlog", "v": "18"},
                    {"n": "萝莉社", "v": "20"},
                    {"n": "色控传媒", "v": "21"},
                    {"n": "华语原创", "v": "22"}
                ]},
                {"key": "by", "name": "排序", "value": [
                    {"n": "时间排序", "v": "time"},
                    {"n": "人气排序", "v": "hits"},
                    {"n": "评分排序", "v": "score"}
                ]},
                {"key": "letter", "name": "字母", "value": [{"n": c, "v": c} for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'] + [{"n": "0-9", "v": "0-9"}]}
            ],
            "2": [
                {"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    {"n": "中文字幕", "v": "23"},
                    {"n": "日本无码", "v": "24"},
                    {"n": "日本有码", "v": "25"},
                    {"n": "丝袜美腿", "v": "26"},
                    {"n": "强奸乱伦", "v": "27"},
                    {"n": "巨乳美乳", "v": "31"},
                    {"n": "美女萝莉", "v": "32"},
                    {"n": "熟女人妻", "v": "33"},
                    {"n": "口爆颜射", "v": "34"},
                    {"n": "岛国素人", "v": "35"},
                    {"n": "岛国女优", "v": "36"},
                    {"n": "重口调教", "v": "37"},
                    {"n": "岛国群交", "v": "38"}
                ]},
                {"key": "by", "name": "排序", "value": [
                    {"n": "时间排序", "v": "time"},
                    {"n": "人气排序", "v": "hits"},
                    {"n": "评分排序", "v": "score"}
                ]},
                {"key": "letter", "name": "字母", "value": [{"n": c, "v": c} for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'] + [{"n": "0-9", "v": "0-9"}]}
            ],
            "3": [
                {"key": "by", "name": "排序", "value": [
                    {"n": "时间排序", "v": "time"},
                    {"n": "人气排序", "v": "hits"},
                    {"n": "评分排序", "v": "score"}
                ]},
                {"key": "letter", "name": "字母", "value": [{"n": c, "v": c} for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'] + [{"n": "0-9", "v": "0-9"}]}
            ],
            "4": [
                {"key": "by", "name": "排序", "value": [
                    {"n": "时间排序", "v": "time"},
                    {"n": "人气排序", "v": "hits"},
                    {"n": "评分排序", "v": "score"}
                ]},
                {"key": "letter", "name": "字母", "value": [{"n": c, "v": c} for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'] + [{"n": "0-9", "v": "0-9"}]}
            ],
            "5": [
                {"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    {"n": "国产精品", "v": "39"},
                    {"n": "抖阴视频", "v": "40"},
                    {"n": "国模私拍", "v": "41"},
                    {"n": "颜射瞬间", "v": "42"},
                    {"n": "女神学生", "v": "43"},
                    {"n": "美熟少妇", "v": "44"},
                    {"n": "娇妻素人", "v": "45"},
                    {"n": "空姐模特", "v": "46"},
                    {"n": "国产乱伦", "v": "47"},
                    {"n": "自慰群交", "v": "48"},
                    {"n": "野合车震", "v": "49"},
                    {"n": "职场同事", "v": "50"},
                    {"n": "国产名人", "v": "51"}
                ]},
                {"key": "by", "name": "排序", "value": [
                    {"n": "时间排序", "v": "time"},
                    {"n": "人气排序", "v": "hits"},
                    {"n": "评分排序", "v": "score"}
                ]},
                {"key": "letter", "name": "字母", "value": [{"n": c, "v": c} for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'] + [{"n": "0-9", "v": "0-9"}]}
            ]
        }
        return {'class': classes, 'filters': filters}

    def homeVideoContent(self):
        html = self.get_html(self.host)
        soup = BeautifulSoup(html, "html.parser")
        videos = []
        for item in soup.select('.stui-vodlist li'):
            try:
                a_thumb = item.select_one('.stui-vodlist__thumb')
                if not a_thumb:
                    continue
                title_elem = item.select_one('.stui-vodlist__detail h4 a')
                title = title_elem.get_text(strip=True) if title_elem else '未知'
                img = a_thumb.get('data-original') or a_thumb.get('src') if a_thumb else ''
                link = a_thumb.get('href', '')
                if not link.startswith('http'):
                    link = self.host + link if link else ''
                vid_match = re.search(r'id/(\d+)', link)
                if vid_match:
                    vid = vid_match.group(1)
                    remark_elem = item.select_one('p.text')
                    remark = remark_elem.get_text(strip=True) if remark_elem else ''
                    videos.append({'vod_id': vid, 'vod_name': title, 'vod_pic': img, 'vod_remarks': remark})
            except:
                continue
        return {'list': videos}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            params = []
            class_val = extend.get('class') if extend.get('class') else ""
            by_val = extend.get('by')
            letter_val = extend.get('letter')
            if class_val and class_val != "":
                base_url = f"{self.host}/index.php/vod/show/id/{class_val}"
                cat_id_for_by = class_val
            else:
                base_url = f"{self.host}/index.php/vod/show/id/{tid}"
                cat_id_for_by = tid
            if by_val:
                params.insert(0, f"by/{by_val}")
                params.insert(1, f"id/{cat_id_for_by}")
            else:
                if class_val and class_val != "":
                    params.append(f"id/{class_val}")
            if letter_val and letter_val != "":
                params.append(f"letter/{letter_val}")
            if params:
                url = f"{self.host}/index.php/vod/show/{'/'.join(params)}/page/{pg}.html"
            else:
                url = f"{base_url}/page/{pg}.html"
            print(f"[CATEGORY] URL: {url}")
            html = self.get_html(url)
            soup = BeautifulSoup(html, "html.parser")
            videos = []
            for item in soup.select('.stui-vodlist li'):
                try:
                    a_thumb = item.select_one('.stui-vodlist__thumb')
                    if not a_thumb:
                        continue
                    title_elem = item.select_one('.stui-vodlist__detail h4 a')
                    title = title_elem.get_text(strip=True) if title_elem else '未知'
                    img = a_thumb.get('data-original') or a_thumb.get('src') if a_thumb else ''
                    link = a_thumb.get('href', '')
                    if not link.startswith('http'):
                        link = self.host + link if link else ''
                    vid_match = re.search(r'id/(\d+)', link)
                    if vid_match:
                        vid = vid_match.group(1)
                        remark_elem = item.select_one('p.text')
                        remark = remark_elem.get_text(strip=True) if remark_elem else ''
                        videos.append({'vod_id': vid, 'vod_name': title, 'vod_pic': img, 'vod_remarks': remark})
                except:
                    continue
            pagecount = int(pg)
            try:
                pagination = soup.select_one('.stui-page')
                if pagination:
                    last_a = pagination.find('a', text=re.compile('末页|尾页|Last')) or pagination.select('a')[-1] if pagination.select('a') else None
                    if last_a:
                        last_href = last_a.get('href')
                        last_pg_match = re.search(r'/page/(\d+)', last_href)
                        if last_pg_match:
                            pagecount = int(last_pg_match.group(1))
            except:
                pass
            return {'list': videos, 'page': pg, 'pagecount': pagecount, 'limit': 30, 'total': 99999}
        except Exception as e:
            print(f"[CATEGORY] 错误: {e}")
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 30, 'total': 0}

    def detailContent(self, ids):
        try:
            vid = ids[0]
            url = f"{self.host}/index.php/vod/detail/id/{vid}.html"
            html = self.get_html(url)
            soup = BeautifulSoup(html, "html.parser")
            title = soup.select_one('h1.title').get_text(strip=True) if soup.select_one('h1.title') else '未知'
            pic = soup.select_one('.stui-content__thumb img').get('data-original') or soup.select_one('.stui-content__thumb img').get('src') if soup.select_one('.stui-content__thumb img') else ''
            desc = soup.select_one('.stui-content__desc').get_text(strip=True) if soup.select_one('.stui-content__desc') else ''
            director = ''
            actor = ''
            director_elem = soup.find('span', string=re.compile('导演：'))
            if director_elem:
                director = '/'.join([a.get_text(strip=True) for a in director_elem.find_parent('div').select('a')])
            actor_elem = soup.find('span', string=re.compile('主演：'))
            if actor_elem:
                actor = '/'.join([a.get_text(strip=True) for a in actor_elem.find_parent('div').select('a')])
            play_from_list = []
            play_url_list = []
            source_tabs = soup.select('.stui-content__playlist .tab-item')
            play_lists = soup.select('.stui-content__playlist-content')
            for idx, tab in enumerate(source_tabs):
                if idx >= len(play_lists):
                    break
                source_name = tab.get_text(strip=True)
                play_list = play_lists[idx]
                episodes = []
                for ep in play_list.select('a'):
                    ep_name = ep.get_text(strip=True)
                    ep_href = ep.get('href', '')
                    sid_match = re.search(r'sid/(\d+)', ep_href)
                    nid_match = re.search(r'nid/(\d+)', ep_href)
                    if sid_match and nid_match:
                        sid = sid_match.group(1)
                        nid = nid_match.group(1)
                        ep_url = f"{vid}@@{sid}@@{nid}"
                        episodes.append(f"{ep_name}${ep_url}")
                if episodes:
                    play_from_list.append(source_name)
                    play_url_list.append('#'.join(episodes))
            if not play_from_list:
                default_episodes = []
                for ep in soup.select('.stui-content__playlist a'):
                    ep_name = ep.get_text(strip=True)
                    ep_href = ep.get('href', '')
                    sid_match = re.search(r'sid/(\d+)', ep_href)
                    nid_match = re.search(r'nid/(\d+)', ep_href)
                    if sid_match and nid_match:
                        sid = sid_match.group(1)
                        nid = nid_match.group(1)
                        ep_url = f"{vid}@@{sid}@@{nid}"
                        default_episodes.append(f"{ep_name}${ep_url}")
                if default_episodes:
                    play_from_list = ['默认线路']
                    play_url_list = ['#'.join(default_episodes)]
            play_from = '$$$'.join(play_from_list)
            play_url = '$$$'.join(play_url_list)
            vod_info = {
                'vod_id': vid,
                'vod_name': title,
                'vod_pic': pic,
                'vod_content': desc,
                'vod_director': director,
                'vod_actor': actor,
                'vod_play_from': play_from,
                'vod_play_url': play_url
            }
            return {'list': [vod_info]}
        except Exception as e:
            print(f"[DETAIL] 错误: {e}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            from urllib.parse import quote
            encoded_key = quote(key)
            if pg == "1":
                url = f"{self.host}/index.php/vod/search/wd/{encoded_key}.html"
            else:
                url = f"{self.host}/index.php/vod/search/page/{pg}/wd/{encoded_key}.html"
            print(f"[SEARCH] URL: {url}")
            html = self.get_html(url)
            if not html:
                print("[SEARCH] 获取 HTML 失败")
                return {'list': []}
            soup = BeautifulSoup(html, "html.parser")
            videos = []
            
            # 修复：搜索结果使用 stui-vodlist__media 而不是 stui-vodlist
            vodlist_media = soup.find('ul', class_='stui-vodlist__media')
            if vodlist_media:
                items = vodlist_media.find_all('li', recursive=False)
                for item in items:
                    try:
                        # 查找主链接和图片
                        a_thumb = item.select_one('a.stui-vodlist__thumb')
                        if not a_thumb:
                            continue
                        
                        # 提取标题
                        title_elem = item.select_one('h3.title a')
                        if not title_elem:
                            title_elem = item.select_one('a')
                        
                        title = title_elem.get_text(strip=True) if title_elem else '未知'
                        
                        # 提取图片URL
                        img = a_thumb.get('data-original') or a_thumb.get('src') or a_thumb.get('style', '')
                        if 'url(' in img:
                            # 从style中提取背景图片
                            match = re.search(r'url\("?([^"\']+)"?\)', img)
                            if match:
                                img = match.group(1)
                        
                        # 提取视频ID - 搜索结果的链接是play链接，需要提取ID
                        link = a_thumb.get('href', '')
                        if not link.startswith('http'):
                            link = self.host + link if link else ''
                        
                        # 从play链接提取vid
                        vid_match = re.search(r'id/(\d+)', link)
                        if not vid_match:
                            continue
                        
                        vid = vid_match.group(1)
                        
                        # 提取备注信息
                        remark_elem = item.select_one('span.pic-text')
                        remark = remark_elem.get_text(strip=True) if remark_elem else ''
                        
                        videos.append({
                            'vod_id': vid, 
                            'vod_name': title, 
                            'vod_pic': img, 
                            'vod_remarks': remark
                        })
                    except Exception as e:
                        print(f"[SEARCH] 解析单项失败: {e}")
                        continue
            else:
                # 备用方案：如果没有找到stui-vodlist__media，尝试其他选择器
                print("[SEARCH] 未找到 stui-vodlist__media，尝试备用选择器")
                items = soup.select('.stui-vodlist li, ul li')
                for item in items:
                    try:
                        a_thumb = item.select_one('.stui-vodlist__thumb, a.v-thumb')
                        if not a_thumb:
                            continue
                        
                        title_elem = item.select_one('.stui-vodlist__detail h4 a, h3.title a, a')
                        title = title_elem.get_text(strip=True) if title_elem else '未知'
                        
                        img = a_thumb.get('data-original') if a_thumb else ''
                        
                        link = title_elem.get('href') if title_elem else ''
                        if not link.startswith('http'):
                            link = self.host + link if link else ''
                        
                        vid_match = re.search(r'id/(\d+)', link)
                        if not vid_match:
                            continue
                        
                        vid = vid_match.group(1)
                        
                        remark_elem = item.select_one('p.text, span.pic-text')
                        remark = remark_elem.get_text(strip=True) if remark_elem else ''
                        
                        videos.append({
                            'vod_id': vid, 
                            'vod_name': title, 
                            'vod_pic': img, 
                            'vod_remarks': remark
                        })
                    except Exception as e:
                        print(f"[SEARCH] 备用方案解析失败: {e}")
                        continue
            
            # 解析分页
            pagecount = int(pg)
            try:
                pagination = soup.select_one('.stui-page')
                if pagination:
                    # 查找最后一页链接
                    last_a = pagination.find('a', text=re.compile('末页|尾页|Last'))
                    if not last_a and pagination.select('a'):
                        last_a = pagination.select('a')[-1]
                    
                    if last_a:
                        last_href = last_a.get('href')
                        if last_href:
                            last_pg_match = re.search(r'/page/(\d+)', last_href)
                            if last_pg_match:
                                pagecount = int(last_pg_match.group(1))
            except Exception as e:
                print(f"[SEARCH] 分页解析失败: {e}")
            
            print(f"[SEARCH] 找到 {len(videos)} 个视频，共 {pagecount} 页")
            return {
                'list': videos, 
                'page': pg, 
                'pagecount': pagecount, 
                'limit': 30, 
                'total': 99999
            }
        except Exception as e:
            print(f"[SEARCH] 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            parts = id.split('@@')
            if len(parts) != 3:
                return {"parse": 0, "url": "", "header": self.headers}
            vid, sid, nid = parts
            play_url = f"{self.host}/index.php/vod/play/id/{vid}/sid/{sid}/nid/{nid}.html"
            html_content = self.get_html(play_url)
            url = ""
            player_data = self.extract_player_data(html_content)
            if player_data and player_data.get('url'):
                url = player_data['url']
            if not url:
                iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+player[^"\']*)["\']', html_content)
                if iframe_match:
                    iframe_src = iframe_match.group(1)
                    if not iframe_src.startswith('http'):
                        iframe_src = self.host + iframe_src
                    if 'url=' in iframe_src:
                        url_match = re.search(r'url=([^&]+)', iframe_src)
                        if url_match:
                            url = html.unquote(url_match.group(1))
                    else:
                        iframe_html = self.get_html(iframe_src)
                        if iframe_html:
                            player_data = self.extract_player_data(iframe_html)
                            if player_data and player_data.get('url'):
                                url = player_data['url']
            if not url:
                patterns = [
                    r'"url"\s*:\s*"([^"]*\.m3u8[^"]*)"',
                    r'"url"\s*:\s*"([^"]*\.mp4[^"]*)"',
                    r"url\s*:\s*'([^']*\.m3u8[^']*)'",
                    r"url\s*:\s*'([^']*\.mp4[^']*)'",
                    r'src\s*=\s*"([^"]*\.m3u8[^"]*)"',
                    r'src\s*=\s*"([^"]*\.mp4[^"]*)"'
                ]
                for pattern in patterns:
                    match = re.search(pattern, html_content, re.IGNORECASE)
                    if match:
                        potential_url = match.group(1)
                        potential_url = self.unescape_js_string(potential_url)
                        if '.m3u8' in potential_url or '.mp4' in potential_url:
                            url = potential_url
                            break
            if url:
                if url.startswith('//'):
                    url = 'https:' + url
                elif url and not url.startswith('http'):
                    url = self.host + url
                url = self.unescape_js_string(url)
            headers = self.headers.copy()
            headers['Referer'] = play_url
            print(f"[PLAYER] 提取到的播放链接: {url}")
            return {"parse": 0, "url": url, "header": headers}
        except Exception as e:
            print(f"[PLAYER] 错误: {e}")
            return {"parse": 0, "url": "", "header": self.headers}

    def localProxy(self, param):
        pass