import json
import requests
import re
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

    def _clean_ai_response(self, content: str) -> str:
        """增强的AI响应清理，移除思考标签和多余内容"""
        # 移除各种思考标签
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
        content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL)

        # 移除其他可能的XML标签
        content = re.sub(r'<[^>]+>', '', content)

        # 移除思考过程的表述
        content = re.sub(r'让我.*?[。，\n]', '', content)
        content = re.sub(r'我来.*?[。，\n]', '', content)
        content = re.sub(r'思考.*?[。，\n]', '', content)
        content = re.sub(r'首先.*?分析', '分析', content)
        content = re.sub(r'接下来.*?设计', '设计', content)

        # 移除用户要求的重复
        content = re.sub(r'用户要求.*?\n', '', content)
        content = re.sub(r'根据要求.*?\n', '', content)

        # 清理多余的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        # 去除开头和结尾的空白
        content = content.strip()

        return content

    def generate_lesson_plan(self, lesson_request: Dict[str, Any]) -> str:
        """生成跨学科教案 - 分阶段生成更详细内容"""

        # 第一阶段：生成教案主体结构
        main_prompt = self._build_comprehensive_lesson_prompt(lesson_request)
        main_plan = self._call_ai_api(main_prompt)

        # 第二阶段：增强跨学科关联
        enhanced_prompt = self._build_cross_disciplinary_enhancement_prompt(main_plan, lesson_request)
        enhanced_plan = self._call_ai_api(enhanced_prompt)

        return enhanced_plan

    def modify_lesson_plan(self, current_plan: str, modification: Dict[str, Any]) -> str:
        """修改现有教案"""
        prompt = self._build_modification_prompt(current_plan, modification)
        return self._call_ai_api(prompt)

    def _call_ai_api(self, prompt: str) -> str:
        """调用AI API的统一方法"""
        data = {
            "model": "InnoSpark",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(data),
                timeout=120  # 增加超时时间，因为教案更详细
            )

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    raw_content = result["choices"][0]["message"]["content"]
                    cleaned_content = self._clean_ai_response(raw_content)
                    return cleaned_content
                else:
                    raise Exception("Invalid response format from Innospark API")
            else:
                print(f"API Error - Status: {response.status_code}, Response: {response.text}")
                raise Exception(f"Innospark API error: {response.status_code} - {response.text}")

        except requests.RequestException as e:
            print(f"Request Error: {e}")
            raise Exception(f"Failed to connect to Innospark API: {str(e)}")

    def _build_comprehensive_lesson_prompt(self, lesson_request: Dict[str, Any]) -> str:
        """构建综合的教案生成提示词"""
        return f"""
你是一名国际知名的跨学科教育专家，专门设计创新的项目式学习教案。请为{lesson_request['grade']}学生设计一份高质量的跨学科教案。

## 核心信息
- **主学科**: {lesson_request['main_subject']}
- **关联学科**: {', '.join(lesson_request['related_subjects'])}
- **预估课时**: {lesson_request['estimated_hours']}小时
- **知识目标**: {', '.join(lesson_request['knowledge_goals'])}
- **学生特点**: {lesson_request['academic_features']}

## 教案要求
请严格按照以下结构生成详细的跨学科教案，确保每个部分内容充实、具体可操作：

### 1. 教学目标（必须包含以下四个维度）

#### 1.1 学科核心素养目标
- **{lesson_request['main_subject']}核心素养**: [具体描述3-4个核心素养目标]
- **跨学科能力**: [描述如何培养跨学科思维和解决问题能力]

#### 1.2 知识与技能目标
- **核心知识点**: [详细列出每个学科的核心知识点]
- **技能发展**: [描述学生将掌握的实践技能]

#### 1.3 过程与方法目标
- **科学探究**: [描述科学探究的具体过程]
- **工程设计**: [描述工程设计思维的培养]

#### 1.4 情感态度价值观目标
- **科学精神**: [培养科学态度和创新精神]
- **社会责任**: [培养解决实际问题的社会责任感]

### 2. 跨学科关联分析

#### 2.1 学科融合点
[详细分析各学科之间的融合点和关联性，至少300字]

#### 2.2 真实情境应用
[设计与现实生活紧密相关的问题情境，体现跨学科价值]

#### 2.3 核心驱动问题
[设计一个引人深思的核心问题，驱动整个学习过程]

### 3. 详细教学步骤

#### 第1课时: [课时主题]
**学习目标**: [本课时具体目标]

**导入环节(10分钟)**:
- [具体的导入活动设计]
- [学生参与方式]

**探究活动(25分钟)**:
- [详细的活动流程]
- [学生分组方式]
- [教师指导要点]

**总结提升(10分钟)**:
- [本课时总结方式]
- [作业布置]

#### 第2课时: [课时主题]
[按相同格式详细设计]

#### 第{lesson_request['estimated_hours']}课时: [课时主题]
[按相同格式详细设计]

### 4. 评估方法

#### 4.1 形成性评估
- **过程性评价**: [评价学生学习过程的具体方法]
- **实时反馈**: [课堂即时评价方式]

#### 4.2 总结性评估
- **作品评价**: [学生作品的评价标准]
- **能力测评**: [跨学科能力的测评方法]

#### 4.3 评价工具
- **评价量表**: [设计具体的评价量表]
- **自我评价**: [学生自我评价的方式]

### 5. 延伸活动

#### 5.1 课后探究项目
[设计2-3个深入的探究项目]

#### 5.2 社会实践活动
[连接社会实际的实践活动]

#### 5.3 跨学科拓展
[进一步的跨学科学习机会]

## 特殊要求
1. 确保每个部分内容详实，具有可操作性
2. 体现项目式学习的特点，以问题解决为导向
3. 充分融合各学科知识，避免简单拼接
4. 考虑学生的认知水平和兴趣特点
5. 使用markdown格式，结构清晰
6. 不要包含任何思考过程，直接输出完整教案

现在请生成完整的教案内容：
"""

    def _build_cross_disciplinary_enhancement_prompt(self, main_plan: str, lesson_request: Dict[str, Any]) -> str:
        """构建跨学科增强提示词"""
        return f"""
请对以下教案进行跨学科深度优化，重点加强各学科之间的有机融合：

原教案：
{main_plan}

## 优化要求：

### 1. 深化跨学科融合
- 分析{lesson_request['main_subject']}与{', '.join(lesson_request['related_subjects'])}的深层连接点
- 设计更多跨学科的实践活动
- 确保知识点之间的有机关联，而非简单并列

### 2. 增强项目式学习特色
- 强化核心驱动问题的引领作用
- 设计更多基于真实情境的学习任务
- 增加学生主动建构知识的机会

### 3. 丰富教学活动设计
- 每个课时增加更多具体的活动细节
- 设计更多小组合作和探究实验
- 加入更多现代教育技术的应用

### 4. 完善评价体系
- 设计更详细的过程性评价方案
- 增加跨学科能力的评价指标
- 提供具体的评价工具和量表

请在保持原有结构的基础上，输出优化后的完整教案，确保内容更加充实和具有跨学科特色。
不要包含任何思考过程，直接输出优化后的教案：
"""

    def _build_modification_prompt(self, current_plan: str, modification: Dict[str, Any]) -> str:
        """构建教案修改提示词"""
        return f"""
请根据以下要求修改教案，确保修改后的内容质量更高、更具可操作性：

## 当前教案
{current_plan}

## 修改要求
- **修改部分**: {modification['section_to_modify']}
- **修改指令**: {modification['modification_instructions']}

## 修改标准
1. 保持教案的整体结构和逻辑性
2. 确保修改部分与其他部分的协调一致
3. 增强内容的实用性和可操作性
4. 保持跨学科教育的特色
5. 使用清晰的markdown格式

请输出完整的修改后教案，不要包含任何思考过程：
"""