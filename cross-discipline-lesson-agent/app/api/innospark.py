import json
import requests
from typing import Dict, Any
from config.settings import INNOSPARK_API_KEY, INNOSPARK_API_URL


class InnosparkClient:
    def __init__(self):
        self.api_key = INNOSPARK_API_KEY
        self.base_url = INNOSPARK_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_lesson_plan(self, lesson_request: Dict[str, Any]) -> str:
        """生成跨学科教案"""
        prompt = self._build_lesson_prompt(lesson_request)

        data = {
            "model": "InnoSpark-R",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(data),
                timeout=30  # 添加超时设置
            )

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception("Invalid response format from Innospark API")
            else:
                print(f"API Error - Status: {response.status_code}, Response: {response.text}")
                raise Exception(f"Innospark API error: {response.status_code} - {response.text}")

        except requests.RequestException as e:
            print(f"Request Error: {e}")
            raise Exception(f"Failed to connect to Innospark API: {str(e)}")

    def modify_lesson_plan(self, current_plan: str, modification: Dict[str, Any]) -> str:
        """修改现有教案"""
        prompt = (
            f"以下是当前的教案:\n{current_plan}\n\n"
            f"根据以下要求修改教案:\n{modification['modification_instructions']}\n\n"
            f"只修改'{modification['section_to_modify']}'部分，其他部分保持不变。"
            "直接返回修改后的完整教案。"
        )

        data = {
            "model": "InnoSpark-R",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(data),
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception("Invalid response format from Innospark API")
            else:
                print(f"API Error - Status: {response.status_code}, Response: {response.text}")
                raise Exception(f"Innospark API error: {response.status_code} - {response.text}")

        except requests.RequestException as e:
            print(f"Request Error: {e}")
            raise Exception(f"Failed to connect to Innospark API: {str(e)}")

    def _build_lesson_prompt(self, lesson_request: Dict[str, Any]) -> str:
        """构建教案生成提示词"""
        return (
            f"你是一位经验丰富的跨学科教育专家，需要为{lesson_request['grade']}年级的学生"
            f"设计一个以{lesson_request['main_subject']}为主，融合{', '.join(lesson_request['related_subjects'])}的教案。\n\n"
            f"具体要求:\n"
            f"- 预估课时: {lesson_request['estimated_hours']}小时\n"
            f"- 知识目标: {', '.join(lesson_request['knowledge_goals'])}\n"
            f"- 学术特点: {lesson_request['academic_features']}\n\n"
            "请按照以下结构生成教案:\n"
            "1. 教学目标\n2. 跨学科关联\n3. 教学步骤\n4. 评估方法\n5. 延伸活动\n"
            "确保内容具有创新性和实践性。"
        )