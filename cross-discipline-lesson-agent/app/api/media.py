import requests
import re
from typing import List, Dict
from config.settings import PEXELS_API_KEY, YOUTUBE_API_KEY, INNOSPARK_API_KEY, INNOSPARK_API_URL
import json


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

        请直接返回关键词，不要其他解释：
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
                    return keywords
                else:
                    # fallback：简单提取关键词
                    return self._simple_keyword_extraction(section_content)
            else:
                return self._simple_keyword_extraction(section_content)

        except Exception as e:
            print(f"AI keyword extraction failed: {e}")
            return self._simple_keyword_extraction(section_content)

    def _simple_keyword_extraction(self, content: str) -> str:
        """简单的关键词提取作为备选方案"""
        # 移除常见停用词并提取重要词汇
        import jieba
        words = jieba.lcut(content)

        # 简单的停用词列表
        stop_words = {'的', '是', '在', '了', '和', '有', '为', '与', '等', '及', '或', '也', '将', '可以', '能够',
                      '通过', '进行', '学生', '教师', '课堂'}

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
        """从Pexels获取相关图片"""
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={query}&per_page={count}"

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
                raise Exception(f"Pexels API error: {response.text}")
        except Exception as e:
            print(f"Pexels API error: {e}")
            return []

    def get_videos(self, query: str, count: int = 3) -> List[Dict]:
        """从YouTube获取相关视频"""
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": count,
            "key": YOUTUBE_API_KEY
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                items = response.json().get("items", [])
                return [{
                    "title": item["snippet"]["title"],
                    "videoId": item["id"]["videoId"],
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "description": item["snippet"]["description"][:200] + "..." if len(
                        item["snippet"]["description"]) > 200 else item["snippet"]["description"]
                } for item in items]
            else:
                raise Exception(f"YouTube API error: {response.text}")
        except Exception as e:
            print(f"YouTube API error: {e}")
            return []