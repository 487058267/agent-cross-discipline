import requests
import re
import json
from typing import List, Dict, Optional
from config.settings import PEXELS_API_KEY, INNOSPARK_API_KEY, INNOSPARK_API_URL
from bs4 import BeautifulSoup
import urllib.parse
import time
import hashlib

# 假设的 COOKIES，请替换为你自己从浏览器获取的有效 COOKIES
# 注意：生产环境不建议硬编码敏感信息，且COOKIE可能需要定期更新或通过登录流程获取
# 为了测试目的，你可以从浏览器登录B站后，F12 -> Network -> 刷新页面 -> 找到任意请求 -> Headers -> Request Headers -> Cookie 复制
# 至少包含 SESSDATA, bili_jct, DedeUserID, buvid3 等关键cookie
MOCK_BILIBILI_COOKIES = "header_theme_version=CLOSE; enable_web_push=DISABLE; buvid_fp=f17cb46480b83ab69fcbf35968aa5cba; rpdid=|(J~k))m~JuR0J'u~kmuYuJlm; buvid3=5C2B99C2-B188-4C73-4529-C60783E0661301409infoc; b_nut=1754904001; _uuid=4B1455BD-FDB8-57B10-94DA-4296226D8110A02933infoc; CURRENT_QUALITY=0; buvid4=BC025B76-6D35-2C6C-44AF-DD358083DD2E26448-023112810-; b_lsid=F383ED87_198BB81D290; bsource=search_google; home_feed_column=4; browser_resolution=885-812; CURRENT_FNVAL=2000; sid=mzyg09dq; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTU3NTE4NzgsImlhdCI6MTc1NTQ5MjYxOCwicGx0IjotMX0.SiRr8XBdnDBpyEr_iz92BLDK9KiEBI0wZ12vxOTABEE; bili_ticket_expires=1755751818"

class MediaRecommender:
    def __init__(self):
        self.innospark_headers = {
            "Authorization": f"Bearer {INNOSPARK_API_KEY}",
            "Content-Type": "application/json"
        }
        self.common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'application/json, text/plain, */*', # 修改为接受JSON，因为是API请求
            'Connection': 'keep-alive',
            'Referer': 'https://search.bilibili.com/', # 模拟从B站搜索页跳转
        }
        # 将cookies字符串转换为字典
        self.bilibili_cookies_dict = self._parse_cookies_string(MOCK_BILIBILI_COOKIES)

    def _parse_cookies_string(self, cookies_str: str) -> Dict[str, str]:
        """将cookies字符串转换为字典"""
        cookies_dict = {}
        for item in cookies_str.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookies_dict[key] = value
        return cookies_dict

    def _clean_ai_response_for_keywords(self, content: str) -> str:
        # ... (与之前相同)
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
        # ... (与之前相同)
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
        # ... (与之前相同)
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
        # ... (与之前相同)
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
        # ... (与之前相同)
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
        从B站搜索相关视频 (通过API实现，借鉴1.py思路)。
        注意：B站API可能需要WBI签名或特定且有效的Cookies。
        """
        print(f"Searching Bilibili API for: '{query}'")

        search_url = "https://api.bilibili.com/x/web-interface/wbi/search/all/v2"
        params = {
            'keyword': query,
            'page': 1,
            'page_size': 42, # 增大page_size以获取更多结果进行筛选
            'platform': 'pc',
            'highlight': 1,
            'single_column': 0
        }

        # 为了兼容WBI签名（如果需要），这里可以添加w_rid和wts，但暂时不实现WBI算法
        # 如果遇到-412错误，表示WBI签名缺失或错误，需要进一步实现签名逻辑
        # params.update(self._get_wbi_sign_params(params)) # 假设有这个方法

        try:
            response = requests.get(
                search_url,
                params=params,
                headers=self.common_headers, # 使用通用header，包含User-Agent等
                cookies=self.bilibili_cookies_dict, # 使用解析后的cookies字典
                timeout=15
            )

            data = response.json()

            if data.get('code') == -412:
                print("Bilibili search API was blocked, might need WBI signature. Refer to https://nemo2011.github.io/bilibili-api/#/get-credential")
                return []
            if data.get('code') != 0:
                print(f"Bilibili API returned an error: {data.get('message', 'Unknown error')}")
                return []

            # 提取视频结果，根据1.py的结构，视频数据在result的第11个元素
            results_sections = data.get('data', {}).get('result', [])
            video_data_list = []
            if len(results_sections) > 11 and 'data' in results_sections[11]:
                video_data_list = results_sections[11]['data']
            else:
                print("Could not find video data in the expected structure (results[11]['data']).")


            videos = []
            for item in video_data_list:
                if item.get('media_type') == 'video' or item.get('type') == 'video': # 确保是视频类型
                    title = self._clean_html(item.get('title', '无标题')) # 标题可能包含HTML标签
                    arcurl = item.get('arcurl', '') # 视频链接
                    bvid = item.get('bvid', '') # B站视频ID
                    author = item.get('author', item.get('upic', '未知UP主')) # 提取UP主
                    duration = item.get('duration', '00:00') # 视频时长
                    play = item.get('play', 0) # 播放量
                    video_review = item.get('video_review', 0) # 弹幕数
                    description = self._clean_html(item.get('description', '')) # 描述

                    thumbnail = item.get('pic', '')
                    if thumbnail and not thumbnail.startswith('http'):
                        thumbnail = 'https:' + thumbnail # 补全缩略图链接

                    video_info = {
                        "title": title,
                        "url": arcurl,
                        "bvid": bvid,
                        "thumbnail": thumbnail,
                        "description": description,
                        "author": author,
                        "duration": duration,
                        "play": play,
                        "video_review": video_review,
                        "link": arcurl # 原始链接同arcurl
                    }
                    videos.append(video_info)
                    if len(videos) >= count: # 达到所需数量
                        break

            print(f"Found {len(videos)} Bilibili videos for query '{query}'.")
            return videos
        except requests.exceptions.RequestException as e:
            print(f"Bilibili API request failed: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Bilibili API response JSON decode error: {e}. Response text: {response.text[:500]}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Bilibili API call: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _clean_html(self, text: str) -> str:
        # ... (与之前相同)
        """清理HTML标签"""
        if not text:
            return ""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;',
                                                                                                        '"').replace(
            '&apos;', "'")
        return clean_text.strip()

    def _format_duration(self, duration) -> str:
        # ... (与之前相同)
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