# -*- coding: utf-8 -*-
import json
import re
import sys
import base64
import requests
import time
import hashlib
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider

class Uvod(Spider):
    siteUrl = "https://api-h5.uvod.tv"
    latest = siteUrl + "/video/latest"
    list_url = siteUrl + "/video/list"
    detail = siteUrl + "/video/info"
    play_url = siteUrl + "/video/source"
    publicKeyPem = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCeBQWotWOpsuPn3PAA+bcmM8YD
fEOzPz7hb/vItV43vBJV2FcM72Hdcv3DccIFuEV9LQ8vcmuetld98eksja9vQ1Ol
8rTnjpTpMbd4HedevSuIhWidJdMAOJKDE3AgGFcQvQePs80uXY2JhTLkRn2ICmDR
/fb32OwWY3QGOvLcuQIDAQAB
-----END PUBLIC KEY-----"""
    privateKeyPem = """-----BEGIN PRIVATE KEY-----
MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBAJ4FBai1Y6my4+fc
8AD5tyYzxgN8Q7M/PuFv+8i1Xje8ElXYVwzvYd1y/cNxwgW4RX0tDy9ya562V33x
6SyNr29DU6XytOeOlOkxt3gd5169K4iFaJ0l0wA4koMTcCAYVxC9B4+zzS5djYmF
MuRGfYgKYNH99vfY7BZjdAY68ty5AgMBAAECgYB1rbvHJj5wVF7Rf4Hk2BMDCi9+
zP4F8SW88Y6KrDbcPt1QvOonIea56jb9ZCxf4hkt3W6foRBwg86oZo2FtoZcpCJ+
rFqUM2/wyV4CuzlL0+rNNSq7bga7d7UVld4hQYOCffSMifyF5rCFNH1py/4Dvswm
pi5qljf+dPLSlxXl2QJBAMzPJ/QPAwcf5K5nngQtbZCD3nqDFpRixXH4aUAIZcDz
S1RNsHrT61mEwZ/thQC2BUJTQNpGOfgh5Ecd1MnURwsCQQDFhAFfmvK7svkygoKX
t55ARNZy9nmme0StMOfdb4Q2UdJjfw8+zQNtKFOM7VhB7ijHcfFuGsE7UeXBe20n
g/XLAkEAv9SoT2hgJaQxxUk4MCF8pgddstJlq8Z3uTA7JMa4x+kZfXTm/6TOo6I8
2VbXZLsYYe8op0lvsoHMFvBSBljV0QJBAKhxyoYRa98dZB5qZRskciaXTlge0WJk
kA4vvh3/o757izRlQMgrKTfng1GVfIZFqKtnBiIDWTXQw2N9cnqXtH8CQAx+CD5t
l1iT0cMdjvlMg2two3SnpOjpo7gALgumIDHAmsUWhocLtcrnJI032VQSUkNnLq9z
EIfmHDz0TPVNHBQ=
-----END PRIVATE KEY-----"""

    def getHeader(self, url):
        try:
            item = url.split("|")
            URL = item[0]
            tid = item[1] if len(item) > 1 else ""
            pg = item[2] if len(item) > 2 else ""
            quality = item[3] if len(item) > 3 else ""
            hm = str(int(time.time() * 1000))
            text = ""
            
            if URL == self.latest:
                text = f"-parent_category_id=101-{hm}"
            elif URL == self.list_url:
                if pg and pg != "":
                    text = f"-page={pg}&pagesize=42&parent_category_id={tid}&sort_type=asc-{hm}"
                else:
                    import urllib.parse
                    text = f"-keyword={urllib.parse.quote(tid).lower()}&need_fragment=1&page=1&pagesize=42&sort_type=asc-{hm}"
            elif URL == self.detail:
                text = f"-id={tid}-{hm}"
            elif URL == self.play_url:
                text = f"-quality={quality}&video_fragment_id={pg}&video_id={tid}-{hm}"
                
            sign = hashlib.md5(text.encode()).hexdigest()
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
                "referer": "https://www.uvod.tv/",
                "origin": "https://www.uvod.tv",
                "content-type": "application/json",
                "accept": "*/*",
                "x-signature": sign,
                "x-timestamp": hm,
                "x-token": ""
            }
            return header
        except Exception as e:
            print(f"Error in getHeader: {str(e)}")
            return {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
                "referer": "www.uvod.tv/",
                "origin": "https://www.uvod.tv"
            }

    def playHeader(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
            "referer": "https://www.uvod.tv/",
            "origin": "https://www.uvod.tv"
        }

    def init(self, extend):
        try:
            if extend and extend != "":
                self.siteUrl = extend
                self.latest = self.siteUrl + "/video/latest"
                self.list_url = self.siteUrl + "/video/list"
                self.detail = self.siteUrl + "/video/info"
                self.play_url = self.siteUrl + "/video/source"
        except Exception as e:
            print(f"Error in init: {str(e)}")

    def encrypt(self, data):
        try:
            if data is None:
                return None
                
            import os
            aesKey = os.urandom(32).hex()
            aesEncryptedData = self.aesEncrypt(data, aesKey, "abcdefghijklmnop")
            rsaEncryptedKey = self.rsaEncrypt(aesKey, self.publicKeyPem)
            return aesEncryptedData + "." + rsaEncryptedKey
        except Exception as e:
            print(f"Error in encrypt: {str(e)}")
            return None

    def decrypt(self, encryptedData):
        try:
            if encryptedData is None:
                return None
                
            encryptedData = re.sub(r'\s', '', encryptedData)
            parts = encryptedData.split('.')
            if len(parts) != 2:
                return None
                
            rsaEncryptedKey = parts[1]
            decryptedKey = self.rsaDecrypt(rsaEncryptedKey, self.privateKeyPem)
            if decryptedKey is None:
                return None
                
            aesEncryptedData = parts[0]
            return self.aesCbcDecrypt(aesEncryptedData, decryptedKey, "abcdefghijklmnop")
        except Exception as e:
            print(f"Error in decrypt: {str(e)}")
            return None

    def aesEncrypt(self, data, key, iv):
        try:
            cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
            data = self.pad(data.encode())
            encrypted = cipher.encrypt(data)
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            print(f"Error in aesEncrypt: {str(e)}")
            return None

    def aesCbcDecrypt(self, encryptedData, key, iv):
        try:
            cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
            encrypted = base64.b64decode(encryptedData)
            decrypted = cipher.decrypt(encrypted)
            return self.unpad(decrypted).decode()
        except Exception as e:
            print(f"Error in aesCbcDecrypt: {str(e)}")
            return None

    def pad(self, s):
        try:
            block_size = AES.block_size
            return s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size).encode()
        except Exception as e:
            print(f"Error in pad: {str(e)}")
            return s

    def unpad(self, s):
        try:
            return s[:-ord(s[len(s)-1:])]
        except Exception as e:
            print(f"Error in unpad: {str(e)}")
            return s

    def rsaEncrypt(self, data, publicKey):
        try:
            key = RSA.importKey(publicKey)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            print(f"Error in rsaEncrypt: {str(e)}")
            return None

    def rsaDecrypt(self, encryptedData, privateKey):
        try:
            key = RSA.importKey(privateKey)
            cipher = PKCS1_v1_5.new(key)
            encrypted = base64.b64decode(encryptedData)
            decrypted = cipher.decrypt(encrypted, None)
            return decrypted.decode()
        except Exception as e:
            print(f"Error in rsaDecrypt: {str(e)}")
            return None

    def homeContent(self, filter):
        try:
            classes = []
            typeIds = ["101", "100", "106", "102", "103", "104", "105"]
            typeNames = ["电视剧", "电影", "粤台专区", "综艺", "动漫", "体育", "纪录片"]
            for i in range(len(typeIds)):
                classes.append({
                    'type_id': typeIds[i],
                    'type_name': typeNames[i]
                })
            
            param = {"parent_category_id": 101}
            encryptData = self.encrypt(json.dumps(param))
            if encryptData is None:
                return json.dumps({'class': classes, 'list': []})
                
            headers = self.getHeader(self.latest)
            response = requests.post(self.latest, data=encryptData, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return json.dumps({'class': classes, 'list': []})
                
            decryptData = self.decrypt(response.text)
            if decryptData is None:
                return json.dumps({'class': classes, 'list': []})
                
            data = json.loads(decryptData)
            
            videos = []
            for item in data.get('data', []):
                videos.append({
                    'vod_id': item.get('id', ''),
                    'vod_name': item.get('title', ''),
                    'vod_pic': item.get('cover', ''),
                    'vod_remarks': item.get('state', '')
                })
            
            return json.dumps({'class': classes, 'list': videos})
        except Exception as e:
            print(f"Error in homeContent: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({'class': [], 'list': []})

    def categoryContent(self, tid, pg, filter, extend):
        try:
            param = {
                "parent_category_id": tid,
                "category_id": None,
                "language": None,
                "year": None,
                "region": None,
                "state": None,
                "keyword": "",
                "paid": None,
                "page": pg,
                "pagesize": 42,
                "sort_field": "",
                "sort_type": "asc"
            }
            encryptData = self.encrypt(json.dumps(param))
            if encryptData is None:
                return json.dumps({'list': [], 'page': pg, 'pagecount': 1, 'limit': 42, 'total': 0})
                
            headers = self.getHeader(f"{self.list_url}|{tid}|{pg}")
            response = requests.post(self.list_url, data=encryptData, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return json.dumps({'list': [], 'page': pg, 'pagecount': 1, 'limit': 42, 'total': 0})
                
            decryptData = self.decrypt(response.text)
            if decryptData is None:
                return json.dumps({'list': [], 'page': pg, 'pagecount': 1, 'limit': 42, 'total': 0})
                
            data = json.loads(decryptData)
            
            videos = []
            for item in data.get('data', []):
                videos.append({
                    'vod_id': item.get('id', ''),
                    'vod_name': item.get('title', ''),
                    'vod_pic': item.get('cover', ''),
                    'vod_remarks': item.get('state', '')
                })
            
            return json.dumps({'list': videos, 'page': pg, 'pagecount': 999, 'limit': 42, 'total': 999})
        except Exception as e:
            print(f"Error in categoryContent: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({'list': [], 'page': pg, 'pagecount': 1, 'limit': 42, 'total': 0})

    def detailContent(self, ids):
        try:
            if not ids or len(ids) == 0:
                return json.dumps({'list': []})
                
            param = {"id": ids[0]}
            encryptData = self.encrypt(json.dumps(param))
            if encryptData is None:
                return json.dumps({'list': []})
                
            headers = self.getHeader(f"{self.detail}|{ids[0]}")
            response = requests.post(self.detail, data=encryptData, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return json.dumps({'list': []})
                
            decryptData = self.decrypt(response.text)
            if decryptData is None:
                return json.dumps({'list': []})
                
            data = json.loads(decryptData)
            
            video = data.get('data', {}).get('video', {})
            videoFragmentList = data.get('data', {}).get('video_fragment_list', [])
            
            vod_play_url = []
            for j, fragment in enumerate(videoFragmentList):
                name = fragment.get('symbol', '')
                nid = fragment.get('id', '')
                qualities = fragment.get('qualities', [])
                nid = f"{ids[0]}|{nid}|{qualities}"
                vod_play_url.append(f"{name}${nid}")
            
            vod = {
                'vod_id': ids[0],
                'vod_year': video.get('year', ''),
                'vod_area': video.get('region', ''),
                'vod_actor': video.get('starring', ''),
                'vod_remarks': video.get('state', ''),
                'vod_content': video.get('description', ''),
                'vod_director': video.get('director', ''),
                'type_name': video.get('language', ''),
                'vod_play_from': 'Qile',
                'vod_play_url': '#'.join(vod_play_url) + '$$$'
            }
            
            return json.dumps({'list': [vod]})
        except Exception as e:
            print(f"Error in detailContent: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({'list': []})

    def searchContent(self, key, quick):
        try:
            param = {
                "parent_category_id": None,
                "category_id": None,
                "language": None,
                "year": None,
                "region": None,
                "state": None,
                "keyword": key,
                "paid": None,
                "page": 1,
                "pagesize": 42,
                "sort_field": "",
                "sort_type": "asc",
                "need_fragment": 1
            }
            encryptData = self.encrypt(json.dumps(param))
            if encryptData is None:
                return json.dumps({'list': []})
                
            headers = self.getHeader(f"{self.list_url}|{key}")
            response = requests.post(self.list_url, data=encryptData, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return json.dumps({'list': []})
                
            decryptData = self.decrypt(response.text)
            if decryptData is None:
                return json.dumps({'list': []})
                
            data = json.loads(decryptData)
            
            videos = []
            for item in data.get('data', []):
                videos.append({
                    'vod_id': item.get('id', ''),
                    'vod_name': item.get('title', ''),
                    'vod_pic': item.get('cover', ''),
                    'vod_remarks': item.get('state', '')
                })
            
            return json.dumps({'list': videos})
        except Exception as e:
            print(f"Error in searchContent: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({'list': []})

    def playerContent(self, flag, id, vipFlags):
        try:
            if not id:
                return json.dumps({'header': self.playHeader(), 'url': ''})
                
            item = id.split("|")
            if len(item) < 3:
                return json.dumps({'header': self.playHeader(), 'url': ''})
                
            tid = item[0]
            nid = item[1]
            quality_str = item[2].replace("[", "").replace("]", "").replace(" ", "")
            qualities = quality_str.split(",")
            
            urls = []
            for s in qualities:
                if s == "4":
                    urls.append("1080p")
                elif s == "3":
                    urls.append("720p")
                elif s == "2":
                    urls.append("480p")
                elif s == "1":
                    urls.append("360p")
                else:
                    urls.append(s.strip())
                
                param = {
                    "video_id": tid,
                    "video_fragment_id": nid,
                    "quality": int(s.strip()),
                    "seek": None
                }
                encryptData = self.encrypt(json.dumps(param))
                if encryptData is None:
                    continue
                    
                headers = self.getHeader(f"{self.play_url}|{tid}|{nid}|{s.strip()}")
                response = requests.post(self.play_url, data=encryptData, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    continue
                    
                decryptData = self.decrypt(response.text)
                if decryptData is None:
                    continue
                    
                data = json.loads(decryptData)
                url = data.get('data', {}).get('video', {}).get('url', '')
                urls.append(url)
            
            return json.dumps({
                'header': self.playHeader(),
                'url': urls
            })
        except Exception as e:
            print(f"Error in playerContent: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({'header': self.playHeader(), 'url': ''})

# 以下为测试代码
if __name__ == '__main__':
    spider = Uvod()
    spider.init("")
    print(spider.homeContent(False))
