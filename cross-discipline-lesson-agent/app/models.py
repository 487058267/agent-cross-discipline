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
    media_type: str                 # 图片或视频 ("image" 或 "video")
    count: int = 3                  # 返回结果数量

# 新增：基于教案章节内容的媒体推荐请求
class SectionMediaRequest(BaseModel):
    section_name: str               # 教案部分名称，如"教学目标"、"跨学科关联"等
    section_content: str            # 该部分的具体内容
    media_type: str                 # "image" 或 "video"
    count: int = 3                  # 推荐数量

# 新增：自动媒体推荐请求（基于会话中的教案章节）
class AutoMediaRequest(BaseModel):
    section_name: str               # 要推荐媒体的教案部分名称
    media_type: str                 # "image" 或 "video"
    count: int = 3                  # 推荐数量

# 新增：章节信息响应模型
class SectionInfo(BaseModel):
    name: str                       # 章节名称
    content: str                    # 章节内容（可能是摘要）
    full_length: int                # 完整内容长度

# 新增：媒体资源信息模型
class MediaItem(BaseModel):
    url: str                        # 资源URL
    title: Optional[str] = None     # 标题（视频用）
    thumbnail: Optional[str] = None # 缩略图
    photographer: Optional[str] = None  # 摄影师（图片用）
    description: Optional[str] = None   # 描述
    link: Optional[str] = None      # 原始链接

# 新增：B站视频信息模型
class BilibiliVideoItem(BaseModel):
    title: str                      # 视频标题
    bvid: str                       # B站视频ID
    url: str                        # 视频链接
    thumbnail: str                  # 缩略图
    description: str                # 视频描述
    author: str                     # UP主
    duration: str                   # 视频时长
    play: int                       # 播放量
    video_review: int               # 弹幕数

# 增强的媒体资源信息模型
class EnhancedMediaItem(BaseModel):
    url: str                        # 资源URL
    title: Optional[str] = None     # 标题（视频用）
    thumbnail: Optional[str] = None # 缩略图
    photographer: Optional[str] = None  # 摄影师（图片用）
    description: Optional[str] = None   # 描述
    link: Optional[str] = None      # 原始链接
    # B站专用字段
    bvid: Optional[str] = None      # B站视频ID
    author: Optional[str] = None    # UP主/作者
    duration: Optional[str] = None  # 时长
    play: Optional[int] = None      # 播放量
    video_review: Optional[int] = None # 弹幕数

# 新增：媒体推荐响应模型
class MediaRecommendationResponse(BaseModel):
    section_name: str               # 章节名称
    keywords_used: str              # 使用的搜索关键词
    media_type: str                 # 媒体类型
    results: List[EnhancedMediaItem] # 推荐结果
    total_found: int                # 找到的总数