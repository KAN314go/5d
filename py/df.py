# -*- coding: utf-8 -*-
import re, sys, os, requests, html as htmlmod
from urllib.parse import urlparse, urljoin
import ujson as json, lxml.html, pyquery, jsonpath, cachetools
from bs4 import BeautifulSoup
from base.spider import Spider
class Spider(Spider):
    def init(self, extend=""):
        self.site = 'https://idnflix.com'
        self.tmdb_host = 'https://api.themoviedb.org/3'
        self.tmdb_key = 'd65d1481ed0f57059aa5c99d287d30fb'
        self.phost = 'https://image.tmdb.org/t/p/w500'
        self.site_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'referer': f'{self.site}/', 'origin': self.site,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        self.tmdb_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'accept': 'application/json'
        }
        self.vidsrc_domains = [
            'https://vidsrc.to', 'https://vidsrc.xyz', 'https://vidsrc-embed.ru'
        ]
        self.cache = cachetools.TTLCache(maxsize=100, ttl=3600)
    def getName(self): return "IDNFLIX"
    def isVideoFormat(self, url): return ('.m3u8' in (url or '').lower()) or ('.mp4' in (url or '').lower())
    def manualVideoCheck(self): return True
    def destroy(self): pass
    def homeContent(self, filter):
        return {'class': [
            {'type_name': '电影', 'type_id': 'film'},
            {'type_name': '剧集', 'type_id': 'tv-series'},
            {'type_name': '18+', 'type_id': '18-keatas'},
            {'type_name': '动画', 'type_id': 'donghua'},
        ], 'filters': {}}
    def homeVideoContent(self):
        try:
            html = self.fetch(self.site + '/', headers=self.site_headers, timeout=10).text
            items = self._parse_list_items(html)
            if items: return {'list': items}
        except: pass
        return self.categoryContent('film', 1, False, {})
    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.site}/kategori/{tid}" + (f"?page={pg}" if str(pg) != '1' else "")
        return {
            'list': self._parse_list_items(self.fetch(url, headers=self.site_headers, timeout=10).text),
            'page': pg, 'pagecount': 9999, 'limit': 90, 'total': 999999,
        }
    def detailContent(self, ids):
        path = ids[0]
        full = path if path.startswith('http') else f"{self.site}{path}" if path.startswith('/') else f"{self.site}/{path}"
        cache_key = f"detail_{path}"
        if cache_key in self.cache: return self.cache[cache_key]
        try:
            media_type, tmdb_id, season, episode = self._parse_play_id(path)
            v = self.fetch(f'{self.tmdb_host}/{media_type}/{tmdb_id}', params={'api_key': self.tmdb_key, 'language': 'en-US'}, headers=self.tmdb_headers).json()
            title, pic, year, area, content, remarks = (v.get('title') or v.get('name') or 'IDNFLIX'), '', (v.get('release_date') or v.get('last_air_date') or '')[:4], v.get('original_language') or '', v.get('overview') or '', ''
        except:
            html = self.fetch(full, headers=self.site_headers, timeout=10).text or ''
            title, year_hint, imdb_id = self._parse_idnflix_detail(full)
            det = self._extract_detail_fields(html)
            title, pic, year, area, content, remarks = det.get('title') or title or 'IDNFLIX', det.get('pic') or '', det.get('year') or year_hint or '', det.get('area') or '', det.get('content') or '', det.get('remarks') or ''
            media_type, tmdb_id = self._tmdb_from_imdb(imdb_id) if imdb_id else self._tmdb_from_title(title, year)
            if not tmdb_id: 
                result = {'list': [{'vod_name': title, 'vod_pic': pic, 'vod_year': year, 'vod_area': area, 'vod_remarks': remarks, 'vod_content': content,'vod_play_from': 'IDNFLIX', 'vod_play_url': f'{title}${full}'}]}
                self.cache[cache_key] = result
                return result
        play_str = f"{title}$/{media_type}/{tmdb_id}" if media_type == 'movie' else f"{title}$/{media_type}/{tmdb_id}/1/1"
        result = {'list': [{'vod_name': title, 'vod_pic': pic, 'vod_year': year, 'vod_area': area, 'vod_remarks': remarks, 'vod_content': content,'vod_play_from': 'IDNFLIX', 'vod_play_url': play_str}]}
        self.cache[cache_key] = result
        return result
    def searchContent(self, key, quick, pg="1"):
        url = f"{self.site}/?s={key}" + (f"&page={pg}" if str(pg) != '1' else "")
        r = self.fetch(url, headers=self.site_headers, timeout=10)
        return {'list': self._parse_list_items(r.text), 'page': pg}
    def playerContent(self, flag, id, vipFlags):
        try:
            media_type, tmdb_id, season, episode = self._parse_play_id(id)
            s, e = season or '1', episode or '1'
            imdb_id = self._tmdb_get_imdb_id(media_type, tmdb_id) or ''
            subs = self._get_subtitles(media_type, tmdb_id, s, e)
            for domain in self.vidsrc_domains:
                candidates = []
                if media_type == 'movie':
                    candidates.extend([f"{domain}/embed/movie/{tmdb_id}", f"{domain}/embed/movie?tmdb={tmdb_id}"])
                    if imdb_id: candidates.extend([f"{domain}/embed/movie/{imdb_id}", f"{domain}/embed/movie?imdb={imdb_id}"])
                else:
                    candidates.extend([f"{domain}/embed/tv/{tmdb_id}/{s}-{e}", f"{domain}/embed/tv?tmdb={tmdb_id}&season={s}&episode={e}"])
                    if imdb_id: candidates.extend([f"{domain}/embed/tv/{imdb_id}/{s}-{e}", f"{domain}/embed/tv?imdb={imdb_id}&season={s}&episode={e}"])
                for embed in candidates:
                    m3u8, hdr = self._resolve_vidsrc(embed)
                    if m3u8: return {'parse': 0, 'url': m3u8, 'header': hdr, 'subs': subs}
            return {'parse': 1, 'url': candidates[0] if candidates else id, 'header': self._site_play_headers(), 'subs': subs}
        except:
            url = f"{self.site}{id if id.startswith('/') else '/' + id}"
            return {'parse': 1, 'url': url, 'header': self._site_play_headers()}
    def localProxy(self, param): pass
    def _parse_list_items(self, html):
        if not html: return []
        items = []
        try:
            doc = pyquery.PyQuery(html)
            links = doc('a[href*="/movie/"], a[href*="/tv/"]')
            for link in links:
                elem = pyquery.PyQuery(link)
                href = elem.attr('href')
                name = elem.find('h3').text() or elem.text()
                if not href or not name: continue
                path = href if not href.startswith('http') else urlparse(href).path
                if not path.startswith('/'): path = '/' + path
                img = elem.find('img').attr('src') or elem.closest('.item').find('img').attr('src')
                pic = self._abs_url(img) if img else ''
                items.append({'vod_id': path, 'vod_name': name.strip(), 'vod_pic': pic, 'vod_remarks': ''})
        except Exception as e:
            self.log(f'PyQuery parse error: {e}')
            items = self._parse_list_items_regex(html)
        return items
    def _parse_list_items_regex(self, html):
        items, seen = [], set()
        for pattern in [
            r'<h3[^>]*>\s*<a[^>]+href=["\'](https?://[^"\']+|/[^"\']+)["\'][^>]*>(.*?)</a>\s*</h3>',
            r'<a[^>]+href=["\'](https?://[^"\']+|/[^"\']+)["\'][^>]*>(?:\s*<img[^>]*>|\s*)<h3[^>]*>(.*?)</h3>'
        ]:
            for m in re.finditer(pattern, html, re.I | re.S):
                href, name = m.group(1), self._clean_html_text(m.group(2))
                if not href or ('/movie/' not in href and '/tv/' not in href): continue
                path = href if not href.startswith('http') else urlparse(href).path
                if not path.startswith('/'): path = '/' + path
                if path in seen: continue
                seen.add(path)
                items.append({'vod_id': path, 'vod_name': name, 'vod_pic': self._find_image_for_link(html, href), 'vod_remarks': ''})
        return items
    def _clean_html_text(self, s):
        return htmlmod.unescape(re.sub('<[^>]+>', '', s or '')).strip()
    def _find_image_for_link(self, html, href):
        try:
            idx = html.find(href)
            if idx != -1:
                for window in [html[max(0, idx - 1500): idx + 3000], html[idx: idx + 4000]]:
                    m = re.search(r'<img[^>]+src=["\'](.*?)["\']', window, re.I)
                    if m: return self._abs_url(m.group(1))
        except: pass
        return ''
    def _abs_url(self, src):
        if not src: return ''
        if src.startswith('http'): return src
        if src.startswith('//'): return 'https:' + src
        if src.startswith('/'): return self.site + src
        return self.site + '/' + src
    def _extract_detail_fields(self, html):
        res = {'title': '', 'pic': '', 'year': '', 'area': '', 'remarks': '', 'content': ''}
        if not html: return res
        try:
            tree = lxml.html.fromstring(html)
            title_elem = tree.xpath('//h1[1]')
            if title_elem:
                res['title'] = self._clean_html_text(title_elem[0].text_content())
            else:
                title_elem = tree.xpath('//title')
                if title_elem:
                    res['title'] = self._clean_html_text(title_elem[0].text_content()).split('–')[0].strip()
            og_img = tree.xpath('//meta[@property="og:image" or @name="og:image"]/@content')
            if og_img:
                res['pic'] = self._abs_url(og_img[0])
            else:
                img_elem = tree.xpath('//img[1]/@src')
                if img_elem:
                    res['pic'] = self._abs_url(img_elem[0])
            year_elem = tree.xpath('//*[contains(text(), "Release:")]/following-sibling::a[1]')
            if year_elem and re.match(r'\d{4}', year_elem[0].text_content() or ''):
                res['year'] = year_elem[0].text_content().strip()
            area_elem = tree.xpath('//*[contains(text(), "Country:")]/following-sibling::a[1]')
            if area_elem:
                res['area'] = self._clean_html_text(area_elem[0].text_content())
            badges = tree.xpath('//li[contains(text(), "HD") or contains(text(), "FHD") or contains(text(), "4K") or contains(text(), "18")]/text()')
            rating_elem = tree.xpath('//*[re:match(text(), "^\s*[0-9]\.[0-9]\s*$")]', namespaces={"re": "http://exslt.org/regular-expressions"})
            remarks = []
            if rating_elem: remarks.append(rating_elem[0].text_content().strip())
            if badges: remarks.append('/'.join([b.strip() for b in badges if b.strip()]))
            res['remarks'] = ' | '.join(remarks)
            desc_elem = tree.xpath('//*[contains(text(), "Deskripsi:")]/following-sibling::p[1]')
            if desc_elem:
                res['content'] = self._clean_html_text(desc_elem[0].text_content())
            else:
                first_p = tree.xpath('//p[1]')
                if first_p:
                    res['content'] = self._clean_html_text(first_p[0].text_content())
        except Exception as e:
            self.log(f'lxml parse error: {e}')
            res = self._extract_detail_fields_regex(html)
        return res
    def _extract_detail_fields_regex(self, html):
        res = {'title': '', 'pic': '', 'year': '', 'area': '', 'remarks': '', 'content': ''}
        if not html: return res
        m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
        res['title'] = self._clean_html_text(m.group(1)) if m else self._clean_html_text(re.search(r'<title>(.*?)</title>', html, re.S | re.I).group(1)).split('–')[0].strip()
        og = re.search(r'<meta[^>]+(property|name)=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        res['pic'] = self._abs_url(og.group(2)) if og else self._abs_url(re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I).group(1)) if re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I) else ''
        y = re.search(r'Release:\s*</[^>]*>\s*<a[^>]*>(\d{4})</a>', html, re.I)
        res['year'] = y.group(1) if y else ''
        a = re.search(r'Country:\s*</[^>]*>\s*<a[^>]*>([^<]+)</a>', html, re.I)
        res['area'] = self._clean_html_text(a.group(1)) if a else ''
        badges = re.findall(r'<li[^>]*>\s*(HD|FHD|4K|18)\s*</li>', html, re.I)
        r = re.search(r'>\s*([0-9]\.[0-9])\s*<', html)
        remarks = [r.group(1)] if r else []
        if badges: remarks.append('/'.join(badges))
        res['remarks'] = ' | '.join([x for x in remarks if x])
        d = re.search(r'Deskripsi:\s*</[^>]*>\s*(<p[^>]*>.*?</p>)', html, re.S | re.I)
        res['content'] = self._clean_html_text(d.group(1)) if d else self._clean_html_text(re.search(r'<p[^>]*>(.*?)</p>', re.search(r'Deskripsi:([\s\S]{0,800})', html, re.I).group(1), re.S | re.I).group(1)) if re.search(r'Deskripsi:([\s\S]{0,800})', html, re.I) else ''
        return res
    def _parse_play_id(self, id_str):
        m = re.match(r'^/(movie|tv)/(\d+)(?:/(\d+)/(\d+))?$', id_str or '')
        if not m: raise ValueError('Unrecognized play id (not tmdb)')
        return m.groups()
    def _parse_idnflix_detail(self, url):
        html = self.fetch(url, headers=self.site_headers, timeout=10).text or ''
        try:
            tree = lxml.html.fromstring(html)
            title_elem = tree.xpath('//h1[1]')
            title = title_elem[0].text_content().strip() if title_elem else ''
            year_elem = tree.xpath('//*[contains(text(), "Release:")]/following-sibling::a[1]')
            year = year_elem[0].text_content().strip() if year_elem and re.match(r'\d{4}', year_elem[0].text_content() or '') else ''
            imdb_elem = tree.xpath('//a[contains(@href, "imdb.com/title/tt")]/@href')
            imdb_id = re.search(r'/(tt\d{7,9})', imdb_elem[0] if imdb_elem else '')
            return title, year, imdb_id.group(1) if imdb_id else None
        except:
            m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
            title = re.sub('<.*?>', '', m.group(1).strip()) if m else ''
            y = re.search(r'Release:\s*</[^>]*>\s*<a[^>]*>(\d{4})</a>', html, re.I)
            year = y.group(1) if y else ''
            mm = re.search(r'/(tt\d{7,9})', html)
            return title, year, mm.group(1) if mm else None
    def _tmdb_from_imdb(self, imdb_id):
        try:
            data = self.fetch(f'{self.tmdb_host}/find/{imdb_id}', params={'api_key': self.tmdb_key, 'language': 'zh-CN', 'external_source': 'imdb_id'}, headers=self.tmdb_headers, timeout=10).json()
            movie_id = jsonpath.jsonpath(data, '$.movie_results[0].id')
            tv_id = jsonpath.jsonpath(data, '$.tv_results[0].id')
            if movie_id: return 'movie', movie_id[0]
            if tv_id: return 'tv', tv_id[0]
        except: pass
        return None, None
    def _tmdb_get_imdb_id(self, media_type, tmdb_id):
        try:
            v = self.fetch(f'{self.tmdb_host}/{media_type}/{tmdb_id}', params={'api_key': self.tmdb_key, 'language': 'en-US', 'append_to_response': 'external_ids'}, headers=self.tmdb_headers, timeout=10).json()
            imdb_id = jsonpath.jsonpath(v, '$.external_ids.imdb_id') or jsonpath.jsonpath(v, '$.imdb_id')
            return imdb_id[0] if imdb_id else None
        except: return None
    def _tmdb_from_title(self, title, year=''):
        try:
            data = self.fetch(f'{self.tmdb_host}/search/multi', params={'query': title, 'api_key': self.tmdb_key, 'language': 'zh-CN', 'page': 1, 'include_adult': 'false', 'year': year or ''}, headers=self.tmdb_headers, timeout=10).json()
            results = jsonpath.jsonpath(data, '$.results[?(@.media_type=="movie" || @.media_type=="tv")]')
            if results: return results[0].get('media_type'), results[0].get('id')
        except: pass
        return None, None
    def _site_play_headers(self):
        h = self.site_headers.copy()
        h.pop('authorization', None)
        return h
    def _get_subtitles(self, media_type, tmdb_id, season, episode):
        subs = []
        def _map_lang(label):
            name = (label or '').lower()
            table = {
                'english': 'en', 'arabic': 'ar', 'chinese': 'zh', 'zh': 'zh', '简体': 'zh-CN', '繁體': 'zh-TW',
                'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 'dutch': 'nl', 'finnish': 'fi', 'french': 'fr',
                'german': 'de', 'greek': 'el', 'hungarian': 'hu', 'indonesian': 'id', 'italian': 'it',
                'japanese': 'ja', 'korean': 'ko', 'norwegian': 'no', 'persian': 'fa', 'polish': 'pl',
                'portuguese (br)': 'pt-BR', 'portuguese': 'pt', 'romanian': 'ro', 'russian': 'ru',
                'serbian': 'sr', 'spanish': 'es', 'swedish': 'sv', 'turkish': 'tr', 'thai': 'th', 'vietnamese': 'vi'
            }
            if name in table: return table[name]
            for k, v in table.items():
                if name.startswith(k) or k in name: return v
            return ''
        try:
            if media_type == 'tv':
                sub_api = f"https://s.vdrk.site/subfetch.php?id={tmdb_id}&s={season}&e={episode}"
            else:
                sub_api = f"https://s.vdrk.site/subfetch.php?id={tmdb_id}"
            hdr = self._site_play_headers().copy()
            hdr.update({'referer': 'https://vidrock.net/'})
            resp = self.fetch(sub_api, headers=hdr, timeout=10)
            if resp is not None and resp.status_code == 200:
                try: items = json.loads(resp.text)
                except Exception: items = json.loads(resp.text or '[]')
                if (not items) and media_type == 'tv':
                    try:
                        resp2 = self.fetch(f"https://s.vdrk.site/subfetch.php?id={tmdb_id}", headers=hdr, timeout=10)
                        if resp2 is not None and resp2.status_code == 200:
                            try: items = json.loads(resp2.text)
                            except Exception: items = json.loads(resp2.text or '[]')
                    except Exception: pass
                for it in items or []:
                    u = it.get('file') or it.get('url') or it.get('src')
                    name = it.get('label') or it.get('name') or 'Subtitle'
                    if not u: continue
                    low = u.lower()
                    fmt = 'application/x-subrip' if ('srt' in low) else 'text/vtt'
                    subs.append({'url': u, 'name': name, 'lang': _map_lang(name), 'format': fmt})
        except Exception as e: self.log(f'Get subtitles error: {e}')
        return subs
    def _resolve_vidsrc(self, base_url):
        try:
            def _abs_url(href, base):
                if not href: return ''
                if href.startswith('//'): return 'https:' + href
                if href.startswith('http'): return href
                return urljoin(base, href)
            def _domain(u): return f'{urlparse(u).scheme}://{urlparse(u).netloc}/'
            def _get(url, referer=None):
                h = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36', 'Referer': referer or _domain(url)}
                return self.fetch(url, headers=h, timeout=10)
            current_url, prev_url = base_url, None
            base_html = _get(current_url, referer=_domain(current_url)).text
            base_soup = BeautifulSoup(base_html, 'html.parser')
            tag = base_soup.select_one('#player_iframe')
            rcp_iframe_src = tag.get('src') if tag else None
            if not rcp_iframe_src:
                first_iframe = base_soup.find('iframe')
                if first_iframe and first_iframe.get('src'):
                    current_url = _abs_url(first_iframe['src'], current_url)
                    inter_html = _get(current_url, referer=_domain(prev_url or current_url)).text
                    tag2 = BeautifulSoup(inter_html, 'html.parser').select_one('#player_iframe')
                    rcp_iframe_src = tag2.get('src') if tag2 else None
            if not rcp_iframe_src:
                alt_url = base_url.replace('.to', '.xyz')
                if alt_url != base_url:
                    current_url = alt_url
                    base_html = _get(current_url, referer=_domain(prev_url or current_url)).text
                    tag = BeautifulSoup(base_html, 'html.parser').select_one('#player_iframe')
                    rcp_iframe_src = tag.get('src') if tag else None
            if not rcp_iframe_src: return None, None
            rcp_iframe_src = _abs_url(rcp_iframe_src, current_url)
            rcp_response = _get(rcp_iframe_src, referer=_domain(current_url)).text
            rcp_domain = _domain(rcp_iframe_src)
            rcp_soup = BeautifulSoup(rcp_response, 'html.parser')
            script_tag = rcp_soup.find('script', string=re.compile(r'src\s*:'))
            if script_tag:
                m = re.search(r"src\s*:\s*['\"](.*?)['\"]", script_tag.string)
                next_iframe_path = m.group(1) if m else None
            else:
                iframe_tag = rcp_soup.find('iframe')
                next_iframe_path = iframe_tag.get('src') if iframe_tag else None
            final_iframe = _abs_url(next_iframe_path, rcp_domain) if next_iframe_path else None
            final_response = _get(final_iframe, referer=rcp_domain).text if final_iframe else rcp_response
            final_soup = BeautifulSoup(final_response, 'html.parser')
            script_tags = final_soup.find_all('script')
            for script in script_tags:
                if script.string:
                    for pat in [r"file\s*:\s*['\"](http[^'\"]+)['\"]", r"['\"]file['\"]\s*:\s*['\"](http[^'\"]+)['\"]"]:
                        mm = re.search(pat, script.string, re.S)
                        if mm: return mm.group(1), {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36', 'Referer': rcp_domain}
            source_tag = final_soup.find('source')
            if source_tag and source_tag.get('src'):
                return source_tag['src'], {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36', 'Referer': rcp_domain}
            mu = re.search(r"(https?://[^'\"\s]+\.m3u8[^'\"\s]*)", final_response)
            if mu: return mu.group(1), {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36', 'Referer': rcp_domain}
        except: pass
        return None, None