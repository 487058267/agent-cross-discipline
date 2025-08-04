from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.api.innospark import InnosparkClient
from app.api.media import MediaRecommender
from app.models import LessonRequest, LessonModification, MediaRequest

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
user_sessions = {}


class SessionData(BaseModel):
    current_lesson_plan: Optional[str] = None
    history: list = []


@app.post("/generate-lesson")
async def generate_lesson(lesson_request: LessonRequest):
    try:
        lesson_plan = innospark.generate_lesson_plan(lesson_request.dict())

        # 修复：将列表转换为元组后再哈希
        request_data = lesson_request.dict()
        request_data["related_subjects"] = tuple(request_data["related_subjects"])
        request_data["knowledge_goals"] = tuple(request_data["knowledge_goals"])

        session_id = str(hash(frozenset(request_data.items())))

        user_sessions[session_id] = SessionData(...)
        return {"session_id": session_id, "lesson_plan": lesson_plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/modify-lesson/{session_id}")
async def modify_lesson(session_id: str, modification: LessonModification):
    """修改现有教案"""
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        current_plan = user_sessions[session_id].current_lesson_plan
        modified_plan = innospark.modify_lesson_plan(
            current_plan,
            modification.dict()
        )

        # 更新会话
        user_sessions[session_id].current_lesson_plan = modified_plan
        user_sessions[session_id].history.append({
            "action": "modification",
            "instructions": modification.modification_instructions,
            "modified_section": modification.section_to_modify,
            "result": modified_plan
        })

        return {"lesson_plan": modified_plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend-media/{session_id}")
async def recommend_media(session_id: str, media_request: MediaRequest):
    """推荐媒体资源"""
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