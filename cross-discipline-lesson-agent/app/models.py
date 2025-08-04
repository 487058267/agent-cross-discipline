from typing import List, Optional
from pydantic import BaseModel

class LessonRequest(BaseModel):
    grade: str                   # 授课年级
    main_subject: str            # 主学科
    related_subjects: List[str]  # 关联学科
    estimated_hours: int         # 预估课时
    knowledge_goals: List[str]   # 知识目标
    academic_features: str       # 学术特点

class LessonModification(BaseModel):
    modification_instructions: str  # 修改指令
    section_to_modify: str          # 要修改的部分

class MediaRequest(BaseModel):
    query: str                      # 搜索查询
    media_type: str                 # 图片或视频
    count: int = 3                  # 返回结果数量