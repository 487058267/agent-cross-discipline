import requests
import re
import json
from typing import List, Dict
from config.settings import PEXELS_API_KEY, INNOSPARK_API_KEY, INNOSPARK_API_URL
from bs4 import BeautifulSoup
import urllib.parse
import time  # 用于简单的反爬延时


class MediaRecommender:
    def __init__(self):
        self.innospark_headers = {
            "Authorization": f"Bearer {INNOSPARK_API_KEY}",
            "Content-Type": "application/json"
        }
        # 通用的User-Agent，模拟浏览器行为，降低被封禁的风险
        self.common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'  # 模拟从Google跳转
        }

    def _clean_ai_response_for_keywords(self, content: str) -> str:
        """专门用于清理AI生成的关键词响应，去除无关的格式和解释"""
        # 移除各种可能的思考标签
        content = re.sub(r'<[^>]+>', '', content, flags=re.DOTALL)  # 移除所有XML/HTML标签

        # 移除引导性词语和解释 (使用 re.M 确保多行匹配)
        content = re.sub(r'^\s*好的，关键词是：', '', content, flags=re.M)
        content = re.sub(r'^\s*关键词：', '', content, flags=re.M)
        content = re.sub(r'让我.*?[。，\n]', '', content, flags=re.M)
        content = re.sub(r'我来.*?[。，\n]', '', content, flags=re.M)
        content = re.sub(r'思考.*?[。，\n]', '', content, flags=re.M)

        # 移除Markdown的标题符号、列表符号、粗体斜体等，以及多余的标点
        # 仅保留中文、英文、数字和空格，确保干净的搜索关键词
        content = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', content, flags=re.UNICODE)

        # 清理多余的空行和前后空白
        content = re.sub(r'\s+', ' ', content).strip()
        return content

    def _simple_keyword_extraction(self, content: str) -> str:
        """简单的关键词提取作为备选方案，仅用于AI提取失败时"""
        try:
            import jieba  # pip install jieba
            words = jieba.lcut(content)
        except ImportError:
            words = content.split()

        stop_words = {'的', '是', '在', '了', '和', '有', '为', '与', '等', '及', '或', '也', '将', '可以', '能够',
                      '通过', '进行', '学生', '教师', '课堂', '教学', '学习', '活动', '内容', '目标', '过程', '方法'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words][:5]
        return ' '.join(keywords)

    def _translate_keywords_to_english(self, chinese_keywords: str) -> str:
        """
        使用Innospark模型将中文关键词翻译成英文，用于Pexels搜索。
        """
        if not chinese_keywords:
            return ""

        prompt = f"""
        请将以下中文关键词翻译成最适合用于图片搜索的英文关键词。
        请用英文单词，多个关键词用逗号分隔。不要其他解释和思考过程。
        中文关键词：{chinese_keywords}

        英文关键词：
        """
        data = {
            "model": "InnoSpark",  # 确保这里是您正在使用的Innospark模型名称
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post(
                INNOSPARK_API_URL,
                headers=self.innospark_headers,
                data=json.dumps(data),
                timeout=15  # 翻译通常比生成教案快，超时可以短一点
            )

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    english_keywords = result["choices"][0]["message"]["content"].strip()
                    # 对翻译结果进行简单清理，移除可能的非英文/数字/逗号/空格字符
                    english_keywords = re.sub(r'[^\w\s,]', '', english_keywords)
                    english_keywords = re.sub(r'\s+', ' ', english_keywords).strip()
                    print(f"Translated keywords: '{chinese_keywords}' -> '{english_keywords}'")
                    return english_keywords
                else:
                    print(f"Innospark AI did not return valid translation choices. Response: {result}")
                    return ""
            else:
                print(f"Innospark AI API error during translation: {response.status_code} - {response.text}")
                return ""
        except requests.exceptions.RequestException as e:
            print(f"Innospark AI translation request failed: {e}")
            return ""
        except Exception as e:
            print(f"An unexpected error occurred during AI translation: {e}")
            return ""

    def extract_keywords_from_section(self, section_content: str, section_name: str) -> str:
        """使用AI从教案部分提取关键词用于媒体搜索"""
        prompt = f"""
        请从以下教案的"{section_name}"部分中提取最适合用于搜索相关图片和视频的中文关键词。
        关键词之间用空格分隔，不要超过10个字。
        关键词应直接反映内容核心，**不要包含任何Markdown符号、序号或多余解释**。

        教案内容：
        {section_content}

        纯关键词：
        """

        data = {
            "model": "InnoSpark",  # 确保这里是您正在使用的Innospark模型名称
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
                    keywords = self._clean_ai_response_for_keywords(keywords)
                    print(f"Keywords extracted by AI and cleaned for section '{section_name}': '{keywords}'")
                    if not keywords or len(keywords.split()) < 1:
                        return self._simple_keyword_extraction(section_content)
                    return keywords
                else:
                    print(f"Innospark AI did not return valid choices for keyword extraction. Response: {result}")
                    return self._simple_keyword_extraction(section_content)
            else:
                print(f"Innospark AI API error during keyword extraction: {response.status_code} - {response.text}")
                return self._simple_keyword_extraction(section_content)

        except requests.exceptions.RequestException as e:
            print(f"Innospark AI keyword extraction request failed: {e}")
            return self._simple_keyword_extraction(section_content)
        except Exception as e:
            print(f"An unexpected error occurred during AI keyword extraction: {e}")
            return self._simple_keyword_extraction(section_content)

    def get_images_for_section(self, section_content: str, section_name: str, count: int = 3) -> List[Dict]:
        """根据教案部分内容获取相关图片"""
        keywords = self.extract_keywords_from_section(section_content, section_name)
        return self.get_images(keywords, count)

    def get_videos_for_section(self, section_content: str, section_name: str, count: int = 3) -> List[Dict]:
        """根据教案部分内容获取相关视频"""
        keywords = self.extract_keywords_from_section(section_content, section_name)
        return self.get_videos(keywords, count)

    def get_images(self, query: str, count: int = 3) -> List[Dict]:
        """从Pexels API 获取相关图片，并优化中文查询（通过翻译）。"""
        if not PEXELS_API_KEY:
            print("PEXELS_API_KEY is not set. Cannot fetch images from Pexels.")
            return []

        # 关键修改：将中文查询翻译成英文
        english_query = self._translate_keywords_to_english(query)
        if not english_query:
            print(f"Failed to translate keywords '{query}', cannot search Pexels effectively.")
            return []

        # Pexels 对英文搜索效果最好，直接使用翻译后的英文关键词
        # 可以选择最核心的几个词，Pexels API 默认会按空格分隔
        pexel_search_query = " ".join(english_query.split(',')[:3]).strip()  # 取前3个翻译后的词
        print(f"Searching Pexels Images with ENGLISH query: '{pexel_search_query}' (Original CH: '{query}')")

        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(pexel_search_query)}&per_page={count}&locale=en-US"  # 搜索时使用英文，结果元数据可以尝试用en-US

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            photos = response.json().get("photos", [])
            results = []
            for photo in photos:
                results.append({
                    "url": photo["src"]["original"],
                    "thumbnail": photo["src"]["medium"],
                    "photographer": photo["photographer"],
                    "link": photo["url"],
                    "description": photo.get("alt", "")
                })
            return results
        except requests.exceptions.RequestException as e:
            print(f"Pexels API request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Pexels API response JSON decode error: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Pexels API call: {e}")
            return []

    def get_videos(self, query: str, count: int = 3) -> List[Dict]:
        """
        从B站搜索相关视频 (通过网页抓取实现)，主要目标是获取链接。
        注意：B站网页结构可能会随时变化，导致抓取失败。
        """
        print(f"Searching Bilibili (web scraping) for: '{query}')")
        try:
            search_url = f"https://search.bilibili.com/all?keyword={urllib.parse.quote(query)}&from_source=web_search&order=totalrank&duration=0&tids_1=-1&__refresh__=true&page=1"

            headers = self.common_headers.copy()
            headers['Referer'] = 'https://www.bilibili.com/'

            response = requests.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找视频卡片，优先匹配新版结构 'bili-video-card'
            video_items = soup.find_all('div', class_=re.compile(r'bili-video-card'))
            if not video_items:
                video_items = soup.find_all('li', class_='video-item')  # 兼容旧版
            if not video_items:
                video_items = soup.find_all('li', class_='video matrix')  # 更旧的结构

            videos = []

            for item in video_items[:count]:
                title = 'N/A'
                url = ''
                author = 'N/A'

                # --- 提取标题和URL (核心逻辑) ---
                title_link_tag = item.find('h3', class_=re.compile(r'bili-video-card__info--tit'))
                if title_link_tag:  # 如果找到了H3标题容器
                    title_link_tag_a = title_link_tag.find('a')  # 尝试查找H3下的A标签
                    if title_link_tag_a:
                        title = title_link_tag_a.get('title', 'N/A').strip()
                        raw_url = title_link_tag_a.get('href', '')
                        url = 'https:' + raw_url if raw_url.startswith('//') else raw_url
                        if url and not url.startswith('http'):
                            url = urllib.parse.urljoin('https://www.bilibili.com/', url)

                # 如果新版H3下的A标签没有找到，尝试旧版直接的A标签
                if not url:  # 如果URL还为空，尝试旧版选择器
                    title_link_tag_old = item.find('a', class_='title')
                    if title_link_tag_old:
                        title = title_link_tag_old.get('title', 'N/A').strip()
                        raw_url = title_link_tag_old.get('href', '')
                        url = 'https:' + raw_url if raw_url.startswith('//') else raw_url
                        if url and not url.startswith('http'):
                            url = urllib.parse.urljoin('https://www.bilibili.com/', url)

                # --- 提取UP主名称 (次要，能取到就取) ---
                author_tag = item.find('a', class_='up-name') or item.find('span',
                                                                           class_='bili-video-card__info--author') or item.find(
                    'span', class_='bili-video-card__info--owner')
                if author_tag:
                    author = author_tag.text.strip()

                # *** 核心判断：只要有有效的URL就返回 ***
                if url and "bilibili.com/video/BV" in url:  # 确保URL是一个B站视频链接
                    video_info = {
                        "title": self._clean_html(title),
                        "url": url,
                        "author": author,
                        "bvid": re.search(r'(BV[a-zA-Z0-9]+)', url).group(1) if re.search(r'(BV[a-zA-Z0-9]+)',
                                                                                          url) else "N/A",  # 尝试提取BVID
                        "thumbnail": "",  # 简化处理，不需要提取
                        "description": "",  # 简化处理，不需要提取
                        "duration": "N/A",  # 简化处理，不需要提取
                        "play": 0,  # 简化处理，不需要提取
                        "video_review": 0  # 简化处理，不需要提取
                    }
                    videos.append(video_info)
                    time.sleep(0.1)  # 增加少量延时

            if not videos:
                print(f"No valid Bilibili video URLs found for query '{query}'.")
            return videos
        except requests.exceptions.RequestException as e:
            print(f"Bilibili web scraping request failed: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Bilibili web scraping: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;',
                                                                                                        '"').replace(
            '&apos;', "'")
        return clean_text.strip()

    def _format_duration(self, duration) -> str:
        """格式化视频时长 (在此简化版本中可能不再直接使用，但为完整性保留)。"""
        if not duration:
            return "未知"
        if isinstance(duration, str) and re.match(r'^(?:(\d{1,2}:)?\d{1,2}:)?(\d{2})$', duration):
            return duration
        try:
            total_seconds = int(duration)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            if minutes >= 60:
                hours = minutes // 60
                minutes = minutes % 60
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return f"{minutes:02d}:{seconds:02d}"
        except (ValueError, TypeError):
            return str(duration)