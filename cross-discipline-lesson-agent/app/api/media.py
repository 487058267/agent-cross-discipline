import requests
import re
import json
from typing import List, Dict
from config.settings import PEXELS_API_KEY, INNOSPARK_API_KEY, INNOSPARK_API_URL
from bs4 import BeautifulSoup
import urllib.parse


class MediaRecommender:
    def __init__(self):
        self.innospark_headers = {
            "Authorization": f"Bearer {INNOSPARK_API_KEY}",
            "Content-Type": "application/json"
        }

    def extract_keywords_from_section(self, section_content: str, section_name: str) -> str:
        """使用AI从教案部分提取关键词用于媒体搜索"""
        prompt = f"""
        请从以下教案的"{section_name}"部分中提取最适合用于搜索相关图片和视频的关键词。
        请用简洁的中文关键词，多个关键词用空格分隔，不超过10个字。

        教案内容：
        {section_content}

        请直接返回关键词，不要其他解释和思考过程：
        """

        data = {
            "model": "InnoSpark-R",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post(
                INNOSPARK_API_URL,
                headers=self.innospark_headers,
                data=json.dumps(data),
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    keywords = result["choices"][0]["message"]["content"].strip()
                    # 清理可能的think标签和多余内容
                    keywords = self._clean_ai_response(keywords)
                    return keywords
                else:
                    return self._simple_keyword_extraction(section_content)
            else:
                return self._simple_keyword_extraction(section_content)

        except Exception as e:
            print(f"AI keyword extraction failed: {e}")
            return self._simple_keyword_extraction(section_content)

    def _clean_ai_response(self, content: str) -> str:
        """清理AI响应，移除思考标签和多余内容"""
        # 移除各种可能的思考标签
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
        content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL)

        # 移除其他可能的XML标签
        content = re.sub(r'<[^>]+>', '', content)

        # 移除"让我想想"、"思考一下"等表述
        content = re.sub(r'让我.*?[。，]', '', content)
        content = re.sub(r'我来.*?[。，]', '', content)
        content = re.sub(r'思考.*?[。，]', '', content)

        # 清理多余的空行和空白
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()

        return content

    def _simple_keyword_extraction(self, content: str) -> str:
        """简单的关键词提取作为备选方案"""
        try:
            import jieba
            words = jieba.lcut(content)
        except ImportError:
            # 如果没有jieba，使用简单的分词
            words = content.split()

        # 简单的停用词列表
        stop_words = {'的', '是', '在', '了', '和', '有', '为', '与', '等', '及', '或', '也', '将', '可以', '能够',
                      '通过', '进行', '学生', '教师', '课堂', '教学', '学习', '活动', '内容'}

        # 过滤停用词并选择前几个词
        keywords = [word for word in words if len(word) > 1 and word not in stop_words][:5]
        return ' '.join(keywords)

    def get_images_for_section(self, section_content: str, section_name: str, count: int = 3) -> List[Dict]:
        """根据教案部分内容获取相关图片"""
        keywords = self.extract_keywords_from_section(section_content, section_name)
        return self.get_images(keywords, count)

    def get_videos_for_section(self, section_content: str, section_name: str, count: int = 3) -> List[Dict]:
        """根据教案部分内容获取相关视频"""
        keywords = self.extract_keywords_from_section(section_content, section_name)
        return self.get_videos(keywords, count)


    def get_images(self, query: str, count: int = 3) -> List[Dict]:
        """从Pexels获取相关图片，并优化中文查询。"""
        headers = {"Authorization": PEXELS_API_KEY}

        # --- 新增的优化逻辑 ---
        # 只取前两个关键词进行搜索，以提高Pexels的匹配精度
        simple_query = " ".join(query.split()[:2])
        print(f"Original query: '{query}', Simplified query for Pexels: '{simple_query}'")
        # ----------------------

        # 使用简化的查询，并添加中文语言环境提示
        url = f"https://api.pexels.com/v1/search?query={simple_query}&per_page={count}&locale=zh-CN"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                photos = response.json().get("photos", [])
                return [{
                    "url": photo["src"]["original"],
                    "thumbnail": photo["src"]["medium"],
                    "photographer": photo["photographer"],
                    "link": photo["url"],
                    "description": photo.get("alt", "")
                } for photo in photos]
            else:
                print(f"Pexels API error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Pexels API error: {e}")
            return []

    def get_videos(self, query: str, count: int = 3) -> List[Dict]:
        """从B站搜索相关视频"""
        try:
            # B站搜索API
            search_url = "https://api.bilibili.com/x/web-interface/search/type"
            params = {
                "search_type": "video",
                "keyword": query,
                "page": 1,
                "page_size": count
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.bilibili.com'
            }

            response = requests.get(search_url, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                videos = []

                if data.get("code") == 0 and "data" in data and "result" in data["data"]:
                    for item in data["data"]["result"][:count]:
                        video_info = {
                            "title": self._clean_html(item.get("title", "")),
                            "bvid": item.get("bvid", ""),
                            "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                            "thumbnail": item.get("pic", "").replace("http:", "https:"),
                            "description": self._clean_html(item.get("description", ""))[:200] + "..." if len(
                                item.get("description", "")) > 200 else self._clean_html(item.get("description", "")),
                            "author": item.get("author", ""),
                            "duration": self._format_duration(item.get("duration", "")),
                            "play": item.get("play", 0),
                            "video_review": item.get("video_review", 0)
                        }
                        videos.append(video_info)

                return videos
            else:
                # 如果API失败，尝试备用方法
                return self._search_bilibili_backup(query, count)

        except Exception as e:
            print(f"B站视频搜索失败: {e}")
            # 返回备用搜索结果或空列表
            return self._search_bilibili_backup(query, count)


    def _search_bilibili_backup(self, query: str, count: int = 3) -> List[Dict]:
        """
        B站备用搜索方法 - 通过网页抓取实现，更可靠。
        """
        print(f"Bilibili API failed, using web scraping backup for query: '{query}'")
        try:
            search_url = f"https://search.bilibili.com/all?keyword={urllib.parse.quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7'
            }

            response = requests.get(search_url, headers=headers, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                video_items = soup.find_all('div', class_='video-item')
                videos = []

                for item in video_items[:count]:
                    title_tag = item.find('a', class_='title')
                    if not title_tag:
                        continue

                    title = title_tag.get('title', 'N/A')
                    url = 'https:' + title_tag.get('href', '')
                    bvid = url.split('/video/')[1].split('?')[0] if '/video/' in url else 'N/A'

                    thumbnail_tag = item.find('img')
                    thumbnail = 'https:' + thumbnail_tag.get('src', '') if thumbnail_tag else ''

                    desc_tag = item.find('div', class_='des')
                    description = desc_tag.text.strip() if desc_tag else ''

                    author_tag = item.find('a', class_='up-name')
                    author = author_tag.text.strip() if author_tag else 'N/A'

                    duration_tag = item.find('span', class_='duration')
                    duration = duration_tag.text.strip() if duration_tag else 'N/A'

                    video_info = {
                        "title": title,
                        "bvid": bvid,
                        "url": url,
                        "thumbnail": thumbnail,
                        "description": description,
                        "author": author,
                        "duration": duration,
                        "play": 0,  # Web scraping doesn't easily get play count
                        "video_review": 0
                    }
                    videos.append(video_info)
                return videos
            else:
                return []
        except Exception as e:
            print(f"Bilibili web scraping backup failed: {e}")
            return []

    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 解码HTML实体
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return clean_text.strip()

    def _format_duration(self, duration) -> str:
        """格式化视频时长"""
        if not duration:
            return "未知"

        if isinstance(duration, str):
            return duration

        # 如果是秒数，转换为分:秒格式
        try:
            total_seconds = int(duration)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        except (ValueError, TypeError):
            return str(duration)