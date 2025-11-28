# coding=utf-8
#!/usr/bin/python
import sys
sys.path.append('..')
from base.spider import Spider
import urllib.parse
import re
from lxml import etree

class Spider(Spider):
    def getName(self):
        return "58动漫"
    
    def init(self, extend):
        pass
        
    def homeContent(self, filter):
        cateManual = {
            "国产动漫": "26",
            "日本动漫": "27", 
            "欧美动漫": "28",
            "海外动漫": "29",
            "动漫电影": "30"
        }
        classes = [{'type_name': k, 'type_id': v} for k, v in cateManual.items()]
        return {'class': classes}

    def homeVideoContent(self):
        try:
            rsp = self.fetch('https://www.djjch.com/')
            root = etree.HTML(rsp.text)
            videos = root.xpath('//ul[@class="fed-list-info fed-part-rows"]/li[contains(@class,"fed-list-item")]')[:12]
            
            videoList = []
            for video in videos:
                name = self.getText(video, './/a[@class="fed-list-title"]/@title')
                img = self.getText(video, './/a[@class="fed-list-pics"]/@data-original')
                remarks = self.getText(video, './/span[@class="fed-list-remarks"]/text()')
                href = self.getText(video, './/a[@class="fed-list-pics"]/@href')
                
                if name and href:
                    videoList.append({
                        "vod_id": href,
                        "vod_name": name,
                        "vod_pic": self.fixUrl(img),
                        "vod_remarks": remarks
                    })
            
            return {'list': videoList}
        except:
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            rsp = self.fetch(f'https://www.djjch.com/wuba/{tid}-{pg}.html')
            root = etree.HTML(rsp.text)
            videos = root.xpath('//ul[contains(@class,"fed-list-info")]/li[contains(@class,"fed-list-item")]')
            
            videoList = []
            for video in videos:
                name = self.getText(video, './/a[contains(@class,"fed-list-title")]/@title')
                img = self.getText(video, './/a[contains(@class,"fed-list-pics")]/@data-original')
                remarks = self.getText(video, './/span[contains(@class,"fed-list-remarks")]/text()')
                href = self.getText(video, './/a[contains(@class,"fed-list-pics")]/@href')
                
                if href:
                    videoList.append({
                        "vod_id": href,
                        "vod_name": name,
                        "vod_pic": self.fixUrl(img),
                        "vod_remarks": remarks
                    })
            
            return {
                'list': videoList,
                'page': pg,
                'pagecount': 999,
                'limit': len(videoList),
                'total': 999999
            }
        except:
            return {'list': [], 'page': 1, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, array):
        try:
            tid = array[0]
            url = self.fixUrl(tid, True)
            rsp = self.fetch(url)
            root = etree.HTML(rsp.text)
            
            title = self.getText(root, '//h1/text()') or self.getText(root, '//title/text()')
            img = self.fixUrl(self.getText(root, '//img[@data-original]/@data-original'))
            
            # 获取描述信息
            info_text = ' '.join([x.strip() for x in root.xpath('//div[contains(@class,"fed-part-layout")]//text()') if x.strip()])
            detail_text = ' '.join([x.strip() for x in root.xpath('//div[contains(@class,"fed-deta-info")]//text()') if x.strip()])
            desc = ' '.join([info_text, detail_text]).strip() or '暂无简介'
            
            # 解析播放源 - 重点保留中文名称
            playFrom, playList = self.parsePlaySources(root)
            
            vod = {
                "vod_id": tid,
                "vod_name": title,
                "vod_pic": img,
                "vod_content": desc,
                "vod_play_from": '$$$'.join(playFrom) if playFrom else '',
                "vod_play_url": '$$$'.join(playList) if playList else ''
            }
            
            return {'list': [vod]}
        except Exception as e:
            print(f"detailContent error: {e}")
            return {'list': []}

    def searchContent(self, key, quick, page='1'):
        try:
            rsp = self.fetch(f'https://www.djjch.com/search.php?searchword={urllib.parse.quote(key)}')
            root = etree.HTML(rsp.text)
            
            videoList = []
            for video in root.xpath('//li[contains(@class,"fed-list-item")]')[:20]:
                name = self.getText(video, './/a/@title') or self.getText(video, './/text()')
                img = self.getText(video, './/img/@data-original')
                href = self.getText(video, './/a/@href')
                
                if name and href and '/dongmandaquan/' in href:
                    videoList.append({
                        "vod_id": href,
                        "vod_name": name.strip(),
                        "vod_pic": self.fixUrl(img),
                        "vod_remarks": ""
                    })
            
            return {'list': videoList}
        except:
            return {'list': []}

    def playerContent(self, flag, id, vipFlags):
        try:
            url = self.fixUrl(id, True)
            rsp = self.fetch(url)
            
            # 尝试多种方式提取视频地址
            patterns = [
                r'var now\s*=\s*["\'](.*?)["\']',
                r'player\.url\s*=\s*["\'](.*?)["\']',
                r'src\s*:\s*["\'](.*?)["\']',
                r'file\s*:\s*["\'](.*?)["\']'
            ]
            
            play_url = None
            for pattern in patterns:
                match = re.search(pattern, rsp.text)
                if match:
                    play_url = match.group(1)
                    break
            
            if not play_url:
                iframe_match = re.search(r'<iframe[^>]*src=["\'](.*?)["\']', rsp.text)
                if iframe_match:
                    play_url = iframe_match.group(1)
            
            if play_url:
                play_url = self.fixUrl(play_url)
            
            return {
                "parse": 0,
                "playUrl": "",
                "url": play_url or url,
                "header": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.djjch.com/"
                }
            }
        except:
            return {"parse": 0, "playUrl": "", "url": id, "header": {}}

    def isVideoFormat(self, url):
        formats = ['.m3u8', '.mp4', '.avi', '.mkv', '.flv', '.ts']
        return any(fmt in url for fmt in formats)

    def manualVideoCheck(self):
        pass

    def localProxy(self, param):
        return [200, "video/MP2T", "", ""]

    # 辅助方法
    def getText(self, element, xpath):
        result = element.xpath(xpath)
        return result[0] if result else ''

    def fixUrl(self, url, is_content_url=False):
        if not url:
            return ''
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if is_content_url:
            return 'https://www.djjch.com' + url
        return 'https://www.djjch.com' + url

    def parsePlaySources(self, root):
        playFrom, playList = [], []
        
        # 从选项卡获取播放源 - 重点保留中文名称
        tab_elements = root.xpath('//ul[contains(@class,"nav-tabs")]/li/a')
        play_containers = root.xpath('//div[contains(@class,"tab-pane")]')
        
        for i, tab in enumerate(tab_elements):
            if i >= len(play_containers):
                break
                
            # 获取完整文本内容，包括图标后的中文名称
            name_parts = tab.xpath('.//text()')
            name = ''.join(name_parts).strip()
            
            # 过滤无效名称
            if not name or '排序' in name or '↑↓' in name:
                continue
                
            # 清理名称中的特殊字符和多余空格
            name = re.sub(r'\s+', ' ', name)
            name = name.replace('&nbsp;', ' ').strip()
            
            # 提取剧集列表
            episodes = play_containers[i].xpath('.//a[contains(@class,"btn")]')
            episode_list = []
            
            for ep in episodes:
                ep_name = ''.join(ep.xpath('.//text()')).strip()
                ep_url = self.getText(ep, './@href')
                if ep_name and ep_url:
                    episode_list.append(f"{ep_name}${self.fixUrl(ep_url, True)}")
            
            if episode_list:
                playFrom.append(name)
                playList.append('#'.join(episode_list))
        
        # 如果上面没找到，尝试从播放器提示信息中获取中文名称
        if not playFrom:
            player_tips = root.xpath('//div[contains(@class,"player_infotip")]//text()')
            for i, container in enumerate(root.xpath('//div[contains(@id,"playlist")]')):
                # 从提示信息中提取中文名称
                source_name = f"线路{i+1}"
                if i < len(player_tips):
                    tip_text = player_tips[i]
                    if '腾讯' in tip_text:
                        source_name = '腾讯视频'
                    elif '优酷' in tip_text:
                        source_name = '优酷视频'
                    elif '奇艺' in tip_text or '爱奇艺' in tip_text:
                        source_name = '爱奇艺视频'
                
                episodes = container.xpath('.//a[contains(@href,"/play/")]')
                episode_list = []
                
                for ep in episodes:
                    ep_name = ''.join(ep.xpath('.//text()')).strip()
                    ep_url = self.getText(ep, './@href')
                    if ep_name and ep_url:
                        episode_list.append(f"{ep_name}${self.fixUrl(ep_url, True)}")
                
                if episode_list:
                    playFrom.append(source_name)
                    playList.append('#'.join(episode_list))
        
        return playFrom, playList