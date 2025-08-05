from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.api.innospark import InnosparkClient
from app.api.media import MediaRecommender
from app.models import LessonRequest, LessonModification, MediaRequest, SectionMediaRequest, AutoMediaRequest
import json
import hashlib
import re

app = FastAPI(title="跨学科教案智能体")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化客户端
innospark = InnosparkClient()
media_recommender = MediaRecommender()

# 存储用户会话状态
user_sessions: Dict[str, Dict[str, Any]] = {}


def parse_lesson_sections(lesson_plan: str) -> Dict[str, str]:
    """解析教案，提取各个部分的内容"""
    sections = {}

    # 改进的章节模式，支持多种格式
    section_patterns = [
        # Markdown格式: #### **1. 教学目标** 或 ### 1. 教学目标
        r'#{1,6}\s*\*?\*?\s*(\d+\.\s*[^*\n]+|\d+\s*[^*\n]+|[^*\n]+)\*?\*?',
        # 纯数字格式: 1. 教学目标
        r'^\d+\.\s*(.+)$',
        # 直接章节名: 教学目标
        r'^(教学目标|跨学科关联|教学步骤|评估方法|延伸活动)$',
        # 带星号的: **教学目标**
        r'^\*\*([^*]+)\*\*$'
    ]

    lines = lesson_plan.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 跳过明显的非章节内容（如思考过程）
        if any(keyword in line for keyword in ['用户要求', '让我', '需要', '考虑', '可能', '应该']):
            continue

        # 检查是否是新的章节标题
        is_section_header = False
        for pattern in section_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # 保存之前的章节
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)

                # 提取和清理章节名称
                section_name = match.group(1) if match.groups() else line
                # 清理章节名称中的标记符号和数字
                section_name = re.sub(r'[#*\d\.\s]*', '', section_name).strip()

                # 标准化章节名称
                if '教学目标' in section_name:
                    section_name = '教学目标'
                elif '跨学科' in section_name:
                    section_name = '跨学科关联'
                elif '教学步骤' in section_name:
                    section_name = '教学步骤'
                elif '评估' in section_name:
                    section_name = '评估方法'
                elif '延伸' in section_name:
                    section_name = '延伸活动'

                if section_name:  # 确保章节名不为空
                    current_section = section_name
                    current_content = []
                    is_section_header = True
                break

        if not is_section_header and current_section:
            current_content.append(line)

    # 保存最后一个章节
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content)

    # 调试输出
    print("Parsed sections:", list(sections.keys()))

    return sections

@app.post("/generate-lesson")
async def generate_lesson(lesson_request: LessonRequest):
    """生成初始教案"""
    try:
        lesson_plan = innospark.generate_lesson_plan(lesson_request.dict())

        # 生成会话ID
        data_str = json.dumps(lesson_request.dict(), sort_keys=True, ensure_ascii=False)
        session_id = hashlib.md5(data_str.encode('utf-8')).hexdigest()[:12]

        # 解析教案章节
        sections = parse_lesson_sections(lesson_plan)

        # 存储到会话
        user_sessions[session_id] = {
            "current_lesson_plan": lesson_plan,
            "sections": sections,
            "history": [{"action": "initial_generation", "content": lesson_plan}]
        }

        return {
            "session_id": session_id,
            "lesson_plan": lesson_plan,
            "available_sections": list(sections.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/modify-lesson/{session_id}")
async def modify_lesson(session_id: str, modification: LessonModification):
    """修改现有教案"""
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        current_plan = user_sessions[session_id]["current_lesson_plan"]
        modified_plan = innospark.modify_lesson_plan(
            current_plan,
            modification.dict()
        )

        # 重新解析章节
        sections = parse_lesson_sections(modified_plan)

        # 更新会话
        user_sessions[session_id]["current_lesson_plan"] = modified_plan
        user_sessions[session_id]["sections"] = sections
        user_sessions[session_id]["history"].append({
            "action": "modification",
            "instructions": modification.modification_instructions,
            "modified_section": modification.section_to_modify,
            "result": modified_plan
        })

        return {
            "lesson_plan": modified_plan,
            "available_sections": list(sections.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend-media-for-section/{session_id}")
async def recommend_media_for_section(session_id: str, request: AutoMediaRequest):
    """为教案的特定部分推荐媒体资源"""
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        sections = user_sessions[session_id]["sections"]

        if request.section_name not in sections:
            available_sections = list(sections.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Section '{request.section_name}' not found. Available sections: {available_sections}"
            )

        section_content = sections[request.section_name]

        if request.media_type == "image":
            results = media_recommender.get_images_for_section(
                section_content,
                request.section_name,
                request.count
            )
        elif request.media_type == "video":
            results = media_recommender.get_videos_for_section(
                section_content,
                request.section_name,
                request.count
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid media type. Use 'image' or 'video'")

        # 提取用于搜索的关键词供参考
        keywords = media_recommender.extract_keywords_from_section(section_content, request.section_name)

        return {
            "section_name": request.section_name,
            "keywords_used": keywords,
            "media_type": request.media_type,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lesson-sections/{session_id}")
async def get_lesson_sections(session_id: str):
    """获取教案的所有章节信息"""
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    sections = user_sessions[session_id]["sections"]

    return {
        "session_id": session_id,
        "sections": [
            {
                "name": name,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "full_length": len(content)
            }
            for name, content in sections.items()
        ]
    }


@app.post("/recommend-media/{session_id}")
async def recommend_media(session_id: str, media_request: MediaRequest):
    """推荐媒体资源（保持原有接口兼容性）"""
    try:
        if media_request.media_type == "image":
            results = media_recommender.get_images(media_request.query, media_request.count)
        elif media_request.media_type == "video":
            results = media_recommender.get_videos(media_request.query, media_request.count)
        else:
            raise HTTPException(status_code=400, detail="Invalid media type")

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return user_sessions[session_id]