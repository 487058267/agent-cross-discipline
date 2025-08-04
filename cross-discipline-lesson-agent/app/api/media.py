import requests
from typing import List, Dict
from config.settings import PEXELS_API_KEY, YOUTUBE_API_KEY


class MediaRecommender:
    def get_images(self, query: str, count: int = 3) -> List[Dict]:
        """从Pexels获取相关图片"""
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={query}&per_page={count}"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            return [{
                "url": photo["src"]["original"],
                "photographer": photo["photographer"],
                "link": photo["url"]
            } for photo in photos]
        else:
            raise Exception(f"Pexels API error: {response.text}")

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

        response = requests.get(url, params=params)
        if response.status_code == 200:
            items = response.json().get("items", [])
            return [{
                "title": item["snippet"]["title"],
                "videoId": item["id"]["videoId"],
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
            } for item in items]
        else:
            raise Exception(f"YouTube API error: {response.text}")