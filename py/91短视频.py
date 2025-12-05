import json
import re
import sys
from base64 import b64decode, b64encode
from urllib.parse import urlparse, parse_qs, unquote, quote
import requests
from Crypto.Cipher import AES
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider as BaseSpider

img_cache = {}

class Spider(BaseSpider):
    def init(self, extend=""):
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
        self.host = self.get_working_host()
        self.headers.update({'Origin': self.host, 'Referer': f"{self.host}/"})

    def getName(self):
        return "💋 91短视频"

    def isVideoFormat(self, url):
        return any(ext in (url or '') for ext in ['.m3u8', '.mp4', '.ts'])

    def manualVideoCheck(self):
        return False

    def destroy(self):
        global img_cache
        img_cache.clear()

    def get_working_host(self):
        urls = ['https://91-short.com', 'https://www.91-short.com']
        for url in urls:
            try:
                if requests.get(url, headers=self.headers, proxies=self.proxies, timeout=5).status_code == 200:
                    return url
            except: continue
        return urls[0]

    def homeContent(self, filter):
        # 固定分类列表
        classes = [
            {'type_name': '推荐', 'type_id': '/short/recommend_home_list'},
            {'type_name': '最新', 'type_id': '/'},
            {'type_name': '美女正妹', 'type_id': '/short/label_related_list/Ug_pu_kskqY%3D'},
            {'type_name': '91大神', 'type_id': '/short/label_related_list/otDa4t6lDDQ%3D'},
            {'type_name': '国产高清', 'type_id': '/short/home_category_list/hd'},
            {'type_name': '排行', 'type_id': '/short/ranking_list'},
            {'type_name': '国产AV', 'type_id': '/short/label_related_list/1Bd0Zzp8D_E%3D'},
            {'type_name': '门事件', 'type_id': '/short/label_related_list/3QW8lOdBcls%3D'},
            {'type_name': '大象传媒', 'type_id': '/short/label_related_list/F16wCJ3LmWY%3D'},
            {'type_name': '情趣综艺', 'type_id': '/short/label_related_list/-0S1LwkskU4%3D'}
        ]
        
        try:
            res = requests.get(self.host, headers=self.headers, proxies=self.proxies, timeout=15)
            return {'class': classes, 'list': self.getlist(self.getpq(res.text)('.module-item, .video-item'))}
        except: return {'class': classes, 'list': []}

    def homeVideoContent(self):
        try:
            res = requests.get(self.host, headers=self.headers, proxies=self.proxies, timeout=15)
            return {'list': self.getlist(self.getpq(res.text)('.module-item, .video-item'))}
        except: return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            pg = int(pg) if pg else 1
            u = tid if tid.startswith('http') else f"{self.host}{tid}" if tid.startswith('/') else f"{self.host}/{tid}"
            
            if tid == '/':
                url = f"{self.host}/?page={pg}"
            else:
                if '?' in u: url = f"{u}&page={pg}"
                else: url = f"{u}?page={pg}"

            res = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=15)
            return {'list': self.getlist(self.getpq(res.text)('.module-item, .video-item'), tid), 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        except: return {'list': [], 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        try:
            u = ids[0] if ids[0].startswith('http') else f"{self.host}{ids[0]}"
            res = requests.get(u, headers=self.headers, proxies=self.proxies, timeout=15)
            html = res.text
            data = self.getpq(html)
            purl = ''
            
            ifr = data('iframe').attr('src')
            if ifr:
                if not ifr.startswith('http'): ifr = f"{self.host}{ifr}"
                try:
                    qs = parse_qs(urlparse(ifr).query)
                    if 'url' in qs:
                        ex = qs['url'][0]
                        if '.m3u8' in ex or '.mp4' in ex: purl = ex
                except: pass
            
            if not purl:
                m = re.search(r'[?&]url=([^&"\']+\.m3u8[^&"\']*)', html)
                if m: purl = unquote(m.group(1))
            if not purl:
                m = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', html)
                if m: purl = m.group(1)

            v = {'vod_play_from': '91短视频', 'vod_play_url': f"播放${purl}" if purl else f"解析失败${u}", 'vod_content': ''}
            
            try:
                tags, seen = [], set()
                links = data('.video-info-aux a, .tag-link, .module-info-tag a, .tags a')
                cands = [{'n': k.text().strip(), 'i': k.attr('href')} for k in links.items() if k.text().strip() and k.attr('href')]
                for i in cands:
                    if i['n'] not in seen:
                        t = json.dumps({'id': i['i'], 'name': i['n']})
                        tags.append(f"[a=cr:{t}/]{i['n']}[/a]")
                        seen.add(i['n'])
                v['vod_content'] = ' '.join(tags) if tags else (data('h1').text() or data('title').text())
            except: v['vod_content'] = '标签获取失败'

            return {'list': [v]}
        except: return {'list': [{'vod_play_from': '91短视频', 'vod_play_url': '获取失败'}]}

    def searchContent(self, key, quick, pg="1"):
        try:
            pg = int(pg) if pg else 1
            url = f"{self.host}/search?wd={quote(key)}&page={pg}"
            res = requests.get(url, headers=self.headers, proxies=self.proxies, timeout=15)
            return {'list': self.getlist(self.getpq(res.text)('.module-item, .video-item')), 'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999}
        except: return {'list': [], 'page': pg, 'pagecount': 9999}

    def playerContent(self, flag, id, vipFlags):
        return {'parse': 0, 'url': id, 'header': self.headers}

    def localProxy(self, param):
        try:
            if param.get('type') == 'img':
                url = param.get('url')
                if url in img_cache: return [200, 'image/jpeg', img_cache[url]]
                r = requests.get(self.d64(url), headers=self.headers, proxies=self.proxies, timeout=10)
                dec = self.aesimg(r.content)
                img_cache[url] = dec
                return [200, 'image/jpeg', dec]
        except: pass
        return [404, 'text/plain', b'']

    def aesimg(self, data):
        key = b'Jui7X#cdleN^3eZb'
        try:
            cipher = AES.new(key, AES.MODE_ECB)
            if len(data) % 16 == 0:
                 dec = cipher.decrypt(data)
                 if self._is_image(dec): return dec
            try:
                b64 = b64decode(data)
                if len(b64) % 16 == 0:
                    dec = cipher.decrypt(b64)
                    if self._is_image(dec): return dec
            except: pass
        except: pass
        return data

    def _is_image(self, data):
        if len(data) < 4: return False
        return data.startswith(b'\xff\xd8') or data.startswith(b'\x89PNG') or data.startswith(b'GIF8')

    def getlist(self, data, tid=''):
        v = []
        for k in data.items():
            a = k.find('a').eq(0)
            i = k.find('img').eq(0)
            h = a.attr('href')
            t = a.attr('title') or i.attr('alt') or k.find('.module-item-title').text()
            p = i.attr('data-cover') or i.attr('data-src') or i.attr('src')
            r = k.find('.module-item-text').text() or k.find('.video-duration').text() or ''
            if h and t:
                if not h.startswith('http'): h = f"{h}"
                if p:
                    if p.startswith('//'): p = f"https:{p}"
                    elif not p.startswith('http'): p = f"{self.host}{p}"
                    p = f"{self.getProxyUrl()}&url={self.e64(p)}&type=img"
                v.append({'vod_id': h, 'vod_name': t.strip(), 'vod_pic': p, 'vod_remarks': r, 'style': {"type": "rect", "ratio": 1.33}})
        return v

    def e64(self, text):
        return b64encode(str(text).encode()).decode()

    def d64(self, text):
        return b64decode(str(text).encode()).decode()

    def getpq(self, data):
        try: return pq(data)
        except: return pq(data.encode('utf-8'))
