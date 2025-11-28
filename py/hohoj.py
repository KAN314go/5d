# -*- coding: utf-8 -*-
# hohoj.tv 恰逢
import json
import re
import sys
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=''):
        """初始化配置"""
        try:
            config = json.loads(extend) if extend and extend.strip() else {}
        except:
            config = {}
        self.proxies = config.get('proxy', {})

    def getName(self):
        return "hohoj"

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # 网站配置
    host = 'https://hohoj.tv'
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'referer': 'https://hohoj.tv/'
    }

    # 分类定义
    categories = [
        {'type_name': '有码', 'type_id': 'search?type=censored'},
        {'type_name': '女優', 'type_id': 'all_models'},
        {'type_name': '無碼', 'type_id': 'search?type=uncensored'},
        {'type_name': '中文字幕', 'type_id': 'search?type=chinese'},
        {'type_name': '歐美', 'type_id': 'search?type=europe'},
        {'type_name': '亂倫', 'type_id': 'main_ctg?id=8'},
        {'type_name': '強姦凌辱', 'type_id': 'main_ctg?id=2'},
        {'type_name': '兄弟受孕', 'type_id': 'main_ctg?id=12'},
        {'type_name': '多P群交', 'type_id': 'main_ctg?id=5'},
        {'type_name': '巨乳美乳', 'type_id': 'main_ctg?id=9'},
        {'type_name': '出軌', 'type_id': 'main_ctg?id=7'},
        {'type_name': '角色扮演', 'type_id': 'main_ctg?id=6'},
        {'type_name': '絲襪美腿', 'type_id': 'main_ctg?id=1'},
        {'type_name': '潮吹放尿', 'type_id': 'main_ctg?id=10'},
        {'type_name': '走光露出', 'type_id': 'main_ctg?id=11'},
        {'type_name': '制服誘惑', 'type_id': 'main_ctg?id=4'},
        {'type_name': '主奴調教', 'type_id': 'main_ctg?id=3'},
    ]

    def fetch(self, url, params=None):
        """统一请求方法"""
        try:
            response = requests.get(url, headers=self.headers, params=params, proxies=self.proxies, timeout=10)
            return response.text
        except Exception as e:
            print(f"[hohoj] 请求错误: {str(e)}")
            return ''

    def homeContent(self, filter):
        """首页内容"""
        try:
            html = self.fetch(self.host)
            return {
                'class': self.categories,
                'filters': {},
                'list': self.parse_videos(pq(html)('.video-item'))
            }
        except:
            return {'class': [], 'filters': {}, 'list': []}

    def homeVideoContent(self):
        pass

    def categoryContent(self, tid, pg, filter, extend):
        """分类内容"""
        try:
            # 构建URL和参数
            if tid == 'all_models':
                url = f"{self.host}/all_models"
            elif tid:
                url = f"{self.host}/{tid}"
            else:
                url = self.host
            
            params = {'page': pg}
            params.update(extend)
            params = {k: v for k, v in params.items() if v}
            
            # 获取数据
            html = self.fetch(url, params)
            data = pq(html)
            
            # 解析列表
            if tid == 'all_models':
                videos = self.parse_models(data('.model'))
            else:
                videos = self.parse_videos(data('.video-item'))
            
            # 获取总页数
            pagecount = data('.glide__bullets button, .pagination li').length or 1
            
            return {
                'list': videos,
                'page': pg,
                'pagecount': pagecount,
                'limit': 90,
                'total': 999999
            }
        except:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        """详情内容"""
        try:
            vid = ids[0]
            url = f"{self.host}{vid}" if vid.startswith('/') else f"{self.host}/{vid}"
            html = self.fetch(url)
            data = pq(html)
            
            # 提取视频ID
            video_id = vid.split('id=')[-1].split('&')[0] if 'id=' in vid else ''
            
            # 获取标题
            title = data('h1').text() or data('title').text()
            
            # 构建vod对象
            vod = {
                'vod_name': title,
                'vod_play_from': '主播放',
                'vod_play_url': f"{title}${video_id}",
                'vod_pic': data('.video-player img').attr('src') or data('meta[property="og:image"]').attr('content'),
                'vod_year': data('.info span').eq(-1).text(),
            }
            
            # 提取女优
            actors = []
            for a in data('.model a').items():
                name = a('.model-name').text().strip()
                href = a.attr('href')
                if name and href:
                    actors.append(f'[a=cr:{json.dumps({"id": href, "name": name})}/]{name}[/a]')
            if actors:
                vod['vod_actor'] = ' '.join(actors)
            
            # 提取标签
            tags = []
            for ctg in data('span.ctg').items():
                link = ctg('a')
                if link:
                    name = link.text().strip()
                    href = link.attr('href')
                    if name and href:
                        tags.append(f'[a=cr:{json.dumps({"id": href, "name": name})}/]{name}[/a]')
            
            if tags:
                vod['vod_remarks'] = ' '.join(tags)
                vod['vod_content'] = '标签: ' + ' '.join(tags)
            
            return {'list': [vod]}
        except:
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        """搜索内容"""
        try:
            html = self.fetch(f"{self.host}/search", {'text': key, 'page': pg})
            return {
                'list': self.parse_videos(pq(html)('.video-item')),
                'page': pg
            }
        except:
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """播放内容"""
        try:
            # 获取embed页面
            html = self.fetch(f"{self.host}/embed?id={id}")
            
            # 提取视频URL
            match = re.search(r'<video[^>]+src="([^"]+)"', html)
            video_url = match.group(1) if match else ''
            
            if not video_url:
                match = re.search(r'var\s+videoSrc\s*=\s*["\']([^"\']+)["\']', html)
                video_url = match.group(1) if match else ''
            
            if not video_url:
                video_url = pq(html)('video#my-video').attr('src') or ''
            
            if not video_url:
                return {'parse': 0, 'url': ''}
            
            return {
                'parse': 0,
                'url': video_url,
                'header': {
                    'user-agent': self.headers['user-agent'],
                    'referer': f"{self.host}/embed?id={id}",
                    'origin': self.host,
                }
            }
        except:
            return {'parse': 0, 'url': ''}

    def localProxy(self, param):
        pass

    def liveContent(self, url):
        pass

    # ==================== 辅助方法 ====================
    
    def parse_videos(self, items):
        """解析视频列表"""
        videos = []
        for i in items.items():
            link = i('a').attr('href')
            title = i('.video-item-title').text() or i('img').attr('alt')
            pic = i('img.img-placeholder').attr('src') or i('img').attr('src')
            
            if not link or not title:
                continue
            
            rating = i('.video-item-rating')
            views = rating.find('.fa-eye').parent().find('span').eq(0).text().strip()
            likes = rating.find('.fa-heart').parent().find('span').eq(0).text().strip()
            
            videos.append({
                'vod_id': link,
                'vod_name': title.strip(),
                'vod_pic': pic,
                'vod_remarks': f"{views} {likes}".strip(),
                'vod_tag': '无码' if i('.video-item-badge').length > 0 else '',
                'style': {"type": "rect", "ratio": 1.5}
            })
        return videos

    def parse_models(self, items):
        """解析女优列表"""
        models = []
        for i in items.items():
            link = i('a').attr('href')
            name = i('.model-name').text()
            pic = i('img').attr('src')
            
            if link and name:
                models.append({
                    'vod_id': link,
                    'vod_name': name,
                    'vod_pic': pic,
                    'vod_tag': 'folder',
                    'style': {"type": "rect", "ratio": 0.75}
                })
        return models
