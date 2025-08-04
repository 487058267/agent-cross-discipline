from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
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


# 会话数据模型
class SessionData(BaseModel):
    current_lesson_plan: Optional[str] = None
    history: List[Dict[str, Any]] = []


# 存储用户会话状态 - 使用普通字典
user_sessions: Dict[str, Dict[str, Any]] = {}


@app.post("/generate-lesson")
async def generate_lesson(lesson_request: LessonRequest):
    """生成初始教案"""
    try:
        lesson_plan = innospark.generate_lesson_plan(lesson_request.dict())

        # 生成会话ID
        session_id = str(hash(frozenset(lesson_request.dict().items())))

        # 存储到会话 - 修复：使用字典而不是 Pydantic 模型实例
        user_sessions[session_id] = {
            "current_lesson_plan": lesson_plan,
            "history": [{"action": "initial_generation", "content": lesson_plan}]
        }

        return {
            "session_id": session_id,
            "lesson_plan": lesson_plan
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

        # 更新会话
        user_sessions[session_id]["current_lesson_plan"] = modified_plan
        user_sessions[session_id]["history"].append({
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