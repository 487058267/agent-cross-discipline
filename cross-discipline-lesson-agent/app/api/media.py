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
        # 移除了所有非字母数字和非中文字符，除了空格
        content = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', content, flags=re.UNICODE)

        # 清理多余的空行和前后空白
        content = re.sub(r'\s+', ' ', content).strip()
        return content

    def _simple_keyword_extraction(self, content: str) -> str:
        """简单的关键词提取作为备选方案，仅用于AI提取失败时"""
        try:
            # 确保安装了 jieba: pip install jieba
            import jieba
            words = jieba.lcut(content)
        except ImportError:
            # 如果没有jieba，使用简单的分词
            words = content.split()

        # 简单的停用词列表，这里可以扩展
        stop_words = {'的', '是', '在', '了', '和', '有', '为', '与', '等', '及', '或', '也', '将', '可以', '能够',
                      '通过', '进行', '学生', '教师', '课堂', '教学', '学习', '活动', '内容', '目标', '过程',
                      '方法'}  # 增加了教学相关的停用词

        # 过滤停用词并选择前几个有意义的词
        keywords = [word for word in words if len(word) > 1 and word not in stop_words][:5]
        return ' '.join(keywords)

    def extract_keywords_from_section(self, section_content: str, section_name: str) -> str:
        """使用AI从教案部分提取关键词用于媒体搜索"""
        # 优化后的提示词
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
                    # 调用新的清理函数来处理AI的原始输出
                    keywords = self._clean_ai_response_for_keywords(keywords)
                    # 打印清理后的关键词，方便调试
                    print(f"Keywords extracted by AI and cleaned for section '{section_name}': '{keywords}'")
                    if not keywords or len(keywords.split()) < 1:  # 如果清理后关键词为空或太少，使用备选
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
        """
        从 Pexels API 获取相关图片，并优化中文查询。
        """
        headers = {"Authorization": PEXELS_API_KEY}

        # 只取前几个关键词进行搜索，以提高Pexels的匹配精度
        # Pexels 对中文支持较好，可以直接使用。
        # 如果关键词是多个词语，Pexels会按空格分隔进行搜索。
        simple_query = " ".join(query.split()[:3])  # 限制到前3个词，避免过长查询
        print(f"Searching Pexels Images for: '{simple_query}' (Original: '{query}')")

        # 使用简化的查询，并添加中文语言环境提示
        url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(simple_query)}&per_page={count}&locale=zh-CN"

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            photos = response.json().get("photos", [])
            results = []
            for photo in photos:
                # Pexels API返回的图片URL通常有多种尺寸，选择 'original' 或 'large'
                results.append({
                    "url": photo["src"]["original"],  # 原始大图
                    "thumbnail": photo["src"]["medium"],  # 中等大小图作为缩略图
                    "photographer": photo["photographer"],
                    "link": photo["url"],  # Pexels 页面链接
                    "description": photo.get("alt", "")  # 图片描述
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
        从B站搜索相关视频 (通过网页抓取实现)。
        注意：B站网页结构可能会随时变化，导致抓取失败。
        """
        print(f"Searching Bilibili (web scraping) for: '{query}'")
        try:
            # B站搜索URL，确保编码
            search_url = f"https://search.bilibili.com/all?keyword={urllib.parse.quote(query)}&from_source=web_search&order=totalrank&duration=0&tids_1=-1&__refresh__=true&page=1"

            headers = self.common_headers.copy()
            headers['Referer'] = 'https://www.bilibili.com/'

            response = requests.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找视频列表项。优先匹配新版结构 'bili-video-card'
            video_items = soup.find_all('div', class_=re.compile(r'bili-video-card'))
            # 如果新版找不到，尝试旧版 'video-item'
            if not video_items:
                video_items = soup.find_all('li', class_='video-item')

            videos = []

            for item in video_items[:count]:
                title = 'N/A'
                url = ''
                bvid = 'N/A'
                thumbnail = ''
                description = ''
                author = 'N/A'
                duration = 'N/A'
                play = 0
                video_review = 0

                # --- 提取标题和URL ---
                # 新版结构：标题通常在 h3.bili-video-card__info--tit 下的 a 标签
                title_h3 = item.find('h3', class_='bili-video-card__info--tit')
                if title_h3:
                    title_a_tag = title_h3.find('a')
                    if title_a_tag:
                        title = title_a_tag.get('title', 'N/A').strip()
                        raw_url = title_a_tag.get('href', '')
                        url = 'https:' + raw_url if raw_url.startswith('//') else raw_url

                # 旧版结构：标题直接是 class='title' 的 a 标签
                if not url:  # 如果新版没找到，尝试旧版
                    title_a_tag_old = item.find('a', class_='title')
                    if title_a_tag_old:
                        title = title_a_tag_old.get('title', 'N/A').strip()
                        raw_url = title_a_tag_old.get('href', '')
                        url = 'https:' + raw_url if raw_url.startswith('//') else raw_url

                # 如果URL仍然不完整，检查是否是相对路径，并拼接完整
                if url and not url.startswith('http'):
                    url = urllib.parse.urljoin('https://www.bilibili.com/', url)

                # --- 提取bvid ---
                if url != '':
                    bvid_match = re.search(r'/video/(BV[a-zA-Z0-9]+)', url)
                    if bvid_match:
                        bvid = bvid_match.group(1)

                # --- 提取缩略图 ---
                thumbnail_tag = item.find('img')
                if thumbnail_tag:
                    # 尝试 data-src (懒加载图片) 或 src
                    thumb_src = thumbnail_tag.get('data-src') or thumbnail_tag.get('src')
                    if thumb_src:
                        # 确保是完整的 https URL
                        thumbnail = 'https:' + thumb_src.replace('//', '') if thumb_src.startswith('//') else thumb_src
                        # 移除B站图片的一些裁剪参数，获取更通用的URL
                        if '@' in thumbnail:
                            thumbnail = thumbnail.split('@')[0]

                # --- 提取描述 ---
                description_tag = item.find('p', class_='des') or item.find('div', class_='bili-video-card__info--desc')
                if description_tag:
                    description = description_tag.text.strip()

                # --- 提取UP主名称 ---
                author_tag = item.find('a', class_='up-name') or item.find('span',
                                                                           class_='bili-video-card__info--author')
                if author_tag:
                    author = author_tag.text.strip()

                # --- 提取视频时长 ---
                duration_tag = item.find('span', class_='duration') or item.find('div',
                                                                                 class_='bili-video-card__stats--duration')
                if duration_tag:
                    duration = duration_tag.text.strip()

                # --- 提取播放量和弹幕数 ---
                # 播放量
                play_tag = item.find('span', class_='play-count') or item.find('span',
                                                                               class_='bili-video-card__stats--item icon-play')
                if play_tag:
                    play_text = play_tag.text.strip()
                    numeric_play = re.sub(r'\D', '', play_text)  # 移除非数字字符
                    if numeric_play:
                        play = int(numeric_play)

                # 弹幕数
                video_review_tag = item.find('span', class_='danmu-count') or item.find('span',
                                                                                        class_='bili-video-card__stats--item icon-danmu')
                if video_review_tag:
                    video_review_text = video_review_tag.text.strip()
                    numeric_review = re.sub(r'\D', '', video_review_text)  # 移除非数字字符
                    if numeric_review:
                        video_review = int(numeric_review)

                video_info = {
                    "title": self._clean_html(title),
                    "bvid": bvid,
                    "url": url,
                    "thumbnail": thumbnail,
                    "description": self._clean_html(description)[:200] + "..." if len(
                        self._clean_html(description)) > 200 else self._clean_html(description),
                    "author": author,
                    "duration": self._format_duration(duration),
                    "play": play,
                    "video_review": video_review
                }
                videos.append(video_info)
                time.sleep(0.1)  # 增加少量延时

            if not videos:
                print(f"No videos found for query '{query}' or scraping failed in detail extraction.")
            return videos
        except requests.exceptions.RequestException as e:
            print(f"Bilibili web scraping request failed: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Bilibili web scraping: {e}")
            import traceback
            traceback.print_exc()  # 打印完整堆栈信息，帮助调试
            return []


    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 解码HTML实体 (例如 &lt; -> <)
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;',
                                                                                                        '"').replace(
            '&apos;', "'")
        return clean_text.strip()

    def _format_duration(self, duration) -> str:
        """格式化视频时长"""
        if not duration:
            return "未知"

        # B站网页抓取通常直接返回 "MM:SS" 或 "HH:MM:SS" 格式，可以直接使用
        if isinstance(duration, str) and re.match(r'(\d{1,2}:)?\d{2}:\d{2}', duration):
            return duration

        # 如果是秒数，转换为分:秒格式 (以防万一)
        try:
            total_seconds = int(duration)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            # 考虑时长超过一小时的情况
            if minutes >= 60:
                hours = minutes // 60
                minutes = minutes % 60
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return f"{minutes:02d}:{seconds:02d}"
        except (ValueError, TypeError):
            return str(duration)