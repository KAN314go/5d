# coding=utf-8
#!/usr/bin/python

import sys
sys.path.append('..')
from base.spider import Spider
import json
import urllib.parse
import re
import traceback

class Spider(Spider):
    def __init__(self):
        super().__init__()
        self.base = 'https://www.uaa001.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty'
        }

    def getName(self):
        return "UAA[听]"

    def init(self, extend=""):
        self.extend = extend or ''
        return {'class': 'audio'}

    def isVideoFormat(self, url):
        return bool(re.search(r'\.(m3u8|mp3|m4a)(\\?|$)'.format(str(url))))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def homeContent(self, filter):
        """首页内容：分类+推荐列表"""
        try:
            result = {}
            # 手动分类（可动态扩展）
            cateManual = {
                "有声小说": "有声小说",
                "淫词艳曲": "淫词艳曲",
                "激情骚麦": "激情骚麦",
                "寸止训练": "寸止训练",
                "ASMR": "ASMR"
            }
            classes = []
            for key in cateManual:
                classes.append({
                    'type_name': key,
                    'type_id': cateManual[key]
                })
            result['class'] = classes

            # 添加首页推荐（取热门有声小说页1）
            recommend_url = 'https://www.uaa001.com/api/audio/app/audio/search?category=&orderType=1&page=1&searchType=1&size=20'
            rsp = self.fetch(recommend_url, headers=self.headers)
            data = json.loads(rsp.text)
            videos = []
            self.log(f"首页推荐找到 {len(data.get('model', {}).get('data', []))} 个项")
            for item in data.get('model', {}).get('data', []):
                videos.append({
                    "vod_id": item['id'],
                    "vod_name": item['title'],
                    "vod_pic": item['coverUrl'],
                    "vod_remarks": item['categories']
                })
            result['list'] = videos[:12]  # 限制12个
            self.log(f"首页返回 {len(result['list'])} 个推荐")
            return result
        except Exception as e:
            self.log(f"homeContent error: {e}")
            self.log(traceback.format_exc())
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        try:
            result = self.homeContent(False)
            return {'list': result.get('list', [])}
        except Exception as e:
            self.log(f'homeVideoContent error: {e}')
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类内容"""
        try:
            result = {}
            url = f'https://www.uaa001.com/api/audio/app/audio/search?category={tid}&orderType=1&page={pg}&searchType=1&size=42'
            rsp = self.fetch(url, headers=self.headers)
            content = rsp.text
            data = json.loads(content)
            videos = []
            model_data = data.get('model', {}).get('data', [])
            self.log(f"分类 {tid} 页 {pg} 找到 {len(model_data)} 个项")
            for item in model_data:
                videos.append({
                    "vod_id": item['id'],
                    "vod_name": item['title'],
                    "vod_pic": item['coverUrl'],
                    "vod_remarks": item['categories']
                })
            result['list'] = videos
            result['page'] = int(pg)
            result['pagecount'] = 999  # 模拟多页
            result['limit'] = 42
            result['total'] = 99999
            return result
        except Exception as e:
            self.log(f"categoryContent {tid}:{pg} error: {e}")
            self.log(traceback.format_exc())
            return {'list': [], 'page': 0, 'pagecount': 0, 'limit': 42, 'total': 0}

    def detailContent(self, array):
        """详情内容"""
        tid = array[0]
        try:
            url = f'https://www.uaa001.com/api/audio/app/audio/intro?id={tid}'
            rsp = self.fetch(url, headers=self.headers)
            content = rsp.text
            data = json.loads(content)
            model = data['model']
            self.log(f"详情 {tid} 获取成功")

            # 构建播放列表
            play_list = []
            chapters = model.get('chapters', [])
            if chapters:
                for chapter in chapters:
                    chapter_id = chapter.get('id', '')
                    chapter_title = chapter.get('title', f'第{chapter.get("order", 1)}集')
                    chapter_url = self.getChapterUrl(chapter_id)
                    if chapter_url:
                        play_list.append(f'{chapter_title}${chapter_url}')
            if not play_list and model.get('latestReadChapterUrl'):
                play_list.append(f'第1集${model["latestReadChapterUrl"]}')

            play_url = '#'.join(play_list) if play_list else model.get('chapterUrl', '')

            # 备注：收听/收藏
            remarks_parts = []
            if 'playCount' in model:
                play_count = self.format_count(model['playCount'])
                remarks_parts.append(f'收听:{play_count}')
            if 'collectCount' in model:
                collect_count = self.format_count(model['collectCount'])
                remarks_parts.append(f'收藏:{collect_count}')
            vod_remarks = ' | '.join(remarks_parts) or model.get('updateState', '')

            vod = {
                "vod_id": tid,
                "vod_name": model['title'],
                "vod_pic": model['coverUrl'],
                "vod_content": model.get('intro', ''),
                "vod_actor": model.get('author', '未知'),
                "vod_remarks": vod_remarks,
                "vod_play_from": "UAA",
                "vod_play_url": play_url
            }
            return {'list': [vod]}
        except Exception as e:
            self.log(f"detailContent {tid} error: {e}")
            self.log(traceback.format_exc())
            return {'list': [{'vod_id': tid, 'vod_name': '获取失败', 'vod_remarks': str(e)}]}

    def format_count(self, count):
        """格式化计数"""
        try:
            count = int(count)
            if count >= 10000:
                return f"{count/10000:.1f}万"
            elif count >= 1000:
                return f"{count/1000:.1f}K"
            else:
                return str(count)
        except:
            return str(count)

    def getChapterUrl(self, chapter_id):
        """章节URL"""
        if not chapter_id:
            return ''
        try:
            url = f'https://www.uaa001.com/api/audio/app/audio/chapter?id={chapter_id}'
            rsp = self.fetch(url, headers=self.headers)
            data = json.loads(rsp.text)
            model = data.get('model', {})
            return model.get('chapterUrl', '')
        except:
            return ''

    def searchContent(self, key, quick, pg="1"):
        """搜索内容"""
        try:
            result = {}
            url = f'https://www.uaa001.com/api/audio/app/audio/search?category=&keyword={urllib.parse.quote(key)}&orderType=1&page={pg}&searchType=1&size=32&tag='
            rsp = self.fetch(url, headers=self.headers)
            content = rsp.text
            data = json.loads(content)
            videos = []
            model_data = data.get('model', {}).get('data', [])
            self.log(f"搜索 '{key}' 页 {pg} 找到 {len(model_data)} 个结果")
            for item in model_data:
                videos.append({
                    "vod_id": item['id'],
                    "vod_name": item['title'],
                    "vod_pic": item['coverUrl'],
                    "vod_remarks": item['categories']
                })
            result['list'] = videos
            return result
        except Exception as e:
            self.log(f"searchContent error: {e}")
            self.log(traceback.format_exc())
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        """播放内容"""
        try:
            return {
                "parse": 0,
                "playUrl": "",
                "url": id,
                "header": self.headers.copy()
            }
        except Exception as e:
            self.log(f"playerContent error: {e}")
            return {"parse": 0, "playUrl": "", "url": "", "header": {}}

    def localProxy(self, param):
        action = {}
        return [200, "video/MP2T", action, ""]
