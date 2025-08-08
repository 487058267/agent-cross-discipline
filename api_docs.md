# 跨学科教案智能体系统 API 文档

## 📋 项目概述

跨学科教案智能体系统是一个基于AI的教育工具，帮助教师快速生成、修改跨学科教案，并推荐相关的媒体教学资源。系统支持多学科融合教学设计，提供智能化的教案优化建议。

### 核心功能
- 🎯 智能教案生成：基于学科、年级、教学目标生成个性化教案
- ✏️ 教案智能修改：针对特定章节进行精准优化
- 📚 媒体资源推荐：自动推荐相关图片、视频教学资源
- 💾 内容自动保存：所有生成内容自动保存为Markdown文件
- 🔄 会话管理：支持多轮对话式教案优化

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- FastAPI
- uvicorn

### 启动服务
```bash
python run.py
```

### 基础URL
```
http://localhost:8000
```

### API文档访问
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🔧 接口列表

| 序号 | 接口名称 | 方法 | 路径 | 描述 |
|------|----------|------|------|------|
| 1 | 生成教案 | POST | `/generate-lesson` | 生成新的跨学科教案 |
| 2 | 修改教案 | POST | `/modify-lesson/{session_id}` | 修改现有教案特定部分 |
| 3 | 章节媒体推荐 | POST | `/recommend-media-for-section/{session_id}` | 为教案章节推荐媒体资源 |
| 4 | 获取教案章节 | GET | `/lesson-sections/{session_id}` | 获取教案所有章节信息 |
| 5 | 通用媒体推荐 | POST | `/recommend-media/{session_id}` | 基于关键词推荐媒体资源 |
| 6 | 获取保存文件 | GET | `/saved-files/{session_id}` | 获取会话的所有保存文件 |
| 7 | 获取会话信息 | GET | `/session/{session_id}` | 获取完整会话状态 |
| 8 | 健康检查 | GET | `/health` | 检查服务运行状态 |

---

## 📝 接口详情

### 1. 生成教案

**生成一个全新的跨学科教案，系统会自动创建会话ID并保存内容**

#### 基本信息
- **URL**: `/generate-lesson`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|--------|------|------|------|------|
| grade | string | ✅ | 授课年级 | "五年级" |
| main_subject | string | ✅ | 主要学科 | "数学" |
| related_subjects | array[string] | ✅ | 关联学科列表 | ["科学", "美术"] |
| estimated_hours | integer | ✅ | 预估授课时长(小时) | 2 |
| knowledge_goals | array[string] | ✅ | 知识目标列表 | ["理解几何图形", "培养空间想象"] |
| academic_features | string | ✅ | 学术特点和要求 | "注重实践操作，结合生活实例" |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/generate-lesson" \
  -H "Content-Type: application/json" \
  -d '{
    "grade": "五年级",
    "main_subject": "数学",
    "related_subjects": ["科学", "美术"],
    "estimated_hours": 2,
    "knowledge_goals": [
      "理解几何图形的基本性质",
      "培养学生的空间想象能力",
      "学会运用几何知识解决实际问题"
    ],
    "academic_features": "结合实际生活案例，注重动手实践和跨学科思维培养"
  }'
```

#### 响应格式

```json
{
  "session_id": "abc123def456",
  "lesson_plan": "# 五年级数学-科学-美术跨学科教案\n\n## 1. 教学目标\n...",
  "available_sections": [
    "教学目标",
    "跨学科关联", 
    "教学步骤",
    "评估方法",
    "延伸活动"
  ],
  "markdown_file": "saved_lessons/abc123def456_initial_lesson_plan_20241208_143022.md"
}
```

#### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| session_id | string | 会话ID，用于后续操作 |
| lesson_plan | string | 完整的教案内容 |
| available_sections | array[string] | 可操作的教案章节列表 |
| markdown_file | string | 保存的markdown文件路径 |

---

### 2. 修改教案

**对现有教案的特定章节进行智能修改和优化**

#### 基本信息
- **URL**: `/modify-lesson/{session_id}`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | string | ✅ | 会话ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|--------|------|------|------|------|
| modification_instructions | string | ✅ | 具体的修改指令 | "增加更多互动环节，让学生参与度更高" |
| section_to_modify | string | ✅ | 要修改的章节名称 | "教学步骤" |

#### 可修改的章节
- `教学目标`
- `跨学科关联`
- `教学步骤`
- `评估方法`
- `延伸活动`

#### 请求示例

```bash
curl -X POST "http://localhost:8000/modify-lesson/abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "modification_instructions": "在教学步骤中增加小组合作环节，添加学生动手操作的具体步骤，让课堂更加生动有趣",
    "section_to_modify": "教学步骤"
  }'
```

#### 响应格式

```json
{
  "lesson_plan": "修改后的完整教案内容...",
  "available_sections": [
    "教学目标",
    "跨学科关联", 
    "教学步骤",
    "评估方法",
    "延伸活动"
  ],
  "markdown_file": "saved_lessons/abc123def456_modified_lesson_plan_20241208_143422.md"
}
```

---

### 3. 章节媒体推荐

**基于教案特定章节内容，智能推荐相关的图片或视频资源**

#### 基本信息
- **URL**: `/recommend-media-for-section/{session_id}`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | string | ✅ | 会话ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 | 示例 | 可选值 |
|--------|------|------|------|------|-------|
| section_name | string | ✅ | 教案章节名称 | "教学步骤" | 见可用章节列表 |
| media_type | string | ✅ | 媒体资源类型 | "image" | "image", "video" |
| count | integer | ❌ | 推荐资源数量 | 5 | 1-10，默认3 |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/recommend-media-for-section/abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "section_name": "教学步骤",
    "media_type": "image",
    "count": 5
  }'
```

#### 响应格式

```json
{
  "section_name": "教学步骤",
  "keywords_used": "几何图形 教学实践 小学数学",
  "media_type": "image",
  "results": [
    {
      "url": "https://images.pexels.com/photos/123456/pexels-photo-123456.jpeg",
      "thumbnail": "https://images.pexels.com/photos/123456/pexels-photo-123456.jpeg?w=350",
      "photographer": "John Doe",
      "link": "https://www.pexels.com/photo/123456/",
      "description": "几何图形教学示例图"
    }
  ],
  "total_found": 5,
  "markdown_file": "saved_lessons/abc123def456_media_recommendation_image_20241208_143622.md"
}
```

#### 媒体资源字段说明

**图片资源 (media_type: "image")**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| url | string | 高清图片URL |
| thumbnail | string | 缩略图URL |
| photographer | string | 摄影师名称 |
| link | string | 原始图片页面链接 |
| description | string | 图片描述 |

**视频资源 (media_type: "video")**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| title | string | 视频标题 |
| videoId | string | YouTube视频ID |
| url | string | YouTube视频链接 |
| thumbnail | string | 视频缩略图URL |
| description | string | 视频描述 |

---

### 4. 获取教案章节

**获取教案的所有章节信息和内容摘要**

#### 基本信息
- **URL**: `/lesson-sections/{session_id}`
- **Method**: `GET`

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | string | ✅ | 会话ID |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/lesson-sections/abc123def456"
```

#### 响应格式

```json
{
  "session_id": "abc123def456",
  "sections": [
    {
      "name": "教学目标",
      "content": "通过本课学习，学生将能够：1. 理解几何图形的基本性质 2. 培养空间想象能力...",
      "full_length": 245
    },
    {
      "name": "跨学科关联",
      "content": "本课程将数学几何知识与科学实验、美术创作相结合...",
      "full_length": 198
    }
  ]
}
```

---

### 5. 通用媒体推荐

**基于自定义关键词搜索和推荐媒体资源**

#### 基本信息
- **URL**: `/recommend-media/{session_id}`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | string | ✅ | 会话ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|--------|------|------|------|------|
| query | string | ✅ | 搜索关键词 | "小学数学 几何图形" |
| media_type | string | ✅ | 媒体类型 | "video" |
| count | integer | ❌ | 返回数量 | 3 |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/recommend-media/abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "小学数学几何图形教学",
    "media_type": "video",
    "count": 3
  }'
```

#### 响应格式

```json
{
  "results": [
    {
      "title": "小学数学几何图形趣味教学",
      "videoId": "dQw4w9WgXcQ",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
      "description": "通过生动有趣的动画，帮助小学生理解几何图形的基本概念..."
    }
  ]
}
```

---

### 6. 获取保存文件

**获取指定会话的所有已保存Markdown文件列表**

#### 基本信息
- **URL**: `/saved-files/{session_id}`
- **Method**: `GET`

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | string | ✅ | 会话ID |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/saved-files/abc123def456"
```

#### 响应格式

```json
{
  "session_id": "abc123def456",
  "total_files": 3,
  "files": [
    {
      "filename": "abc123def456_modified_lesson_plan_20241208_143422.md",
      "filepath": "saved_lessons/abc123def456_modified_lesson_plan_20241208_143422.md",
      "size": 2048,
      "created_time": "2024-12-08T14:34:22.123456",
      "modified_time": "2024-12-08T14:34:22.123456"
    },
    {
      "filename": "abc123def456_media_recommendation_image_20241208_143622.md",
      "filepath": "saved_lessons/abc123def456_media_recommendation_image_20241208_143622.md",
      "size": 1536,
      "created_time": "2024-12-08T14:36:22.789012",
      "modified_time": "2024-12-08T14:36:22.789012"
    }
  ]
}
```

---

### 7. 获取会话信息

**获取完整的会话状态和历史记录**

#### 基本信息
- **URL**: `/session/{session_id}`
- **Method**: `GET`

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| session_id | string | ✅ | 会话ID |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/session/abc123def456"
```

#### 响应格式

```json
{
  "current_lesson_plan": "当前完整的教案内容...",
  "sections": {
    "教学目标": "通过本课学习，学生将能够...",
    "跨学科关联": "本课程将数学几何知识与科学实验...",
    "教学步骤": "第一步：导入环节..."
  },
  "history": [
    {
      "action": "initial_generation",
      "content": "初始生成的教案内容...",
      "markdown_file": "saved_lessons/abc123def456_initial_lesson_plan_20241208_143022.md"
    },
    {
      "action": "modification",
      "instructions": "增加更多互动环节",
      "modified_section": "教学步骤",
      "result": "修改后的教案内容...",
      "markdown_file": "saved_lessons/abc123def456_modified_lesson_plan_20241208_143422.md"
    }
  ],
  "request_info": {
    "grade": "五年级",
    "main_subject": "数学",
    "related_subjects": ["科学", "美术"],
    "estimated_hours": 2
  }
}
```

---

### 8. 健康检查

**检查API服务运行状态**

#### 基本信息
- **URL**: `/health`
- **Method**: `GET`

#### 请求示例

```bash
curl -X GET "http://localhost:8000/health"
```

#### 响应格式

```json
{
  "status": "healthy"
}
```

---

## 🚨 错误处理

### HTTP状态码说明

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | 请求参数错误或格式不正确 |
| 404 | Not Found | 请求的资源不存在（如session_id不存在） |
| 500 | Internal Server Error | 服务器内部错误 |

### 错误响应格式

所有错误响应都遵循以下格式：

```json
{
  "detail": "具体的错误描述信息"
}
```

### 常见错误示例

#### 1. 会话不存在 (404)
```json
{
  "detail": "Session not found"
}
```

#### 2. 章节不存在 (400)
```json
{
  "detail": "Section '无效章节' not found. Available sections: ['教学目标', '跨学科关联', '教学步骤', '评估方法', '延伸活动']"
}
```

#### 3. 媒体类型错误 (400)
```json
{
  "detail": "Invalid media type. Use 'image' or 'video'"
}
```

#### 4. API调用失败 (500)
```json
{
  "detail": "Failed to connect to Innospark API: Connection timeout"
}
```

---

## 🎯 使用场景

### 场景1: 完整教案生成流程

```bash
# 1. 生成初始教案
curl -X POST "http://localhost:8000/generate-lesson" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 响应获得 session_id: "abc123def456"

# 2. 查看生成的章节
curl -X GET "http://localhost:8000/lesson-sections/abc123def456"

# 3. 修改特定章节
curl -X POST "http://localhost:8000/modify-lesson/abc123def456" \
  -H "Content-Type: application/json" \
  -d '{"modification_instructions":"增加互动环节","section_to_modify":"教学步骤"}'

# 4. 为章节推荐媒体资源
curl -X POST "http://localhost:8000/recommend-media-for-section/abc123def456" \
  -H "Content-Type: application/json" \
  -d '{"section_name":"教学步骤","media_type":"image","count":3}'

# 5. 查看所有保存的文件
curl -X GET "http://localhost:8000/saved-files/abc123def456"
```

### 场景2: 快速媒体资源搜索

```bash
# 直接根据关键词搜索相关教学资源
curl -X POST "http://localhost:8000/recommend-media/session123" \
  -H "Content-Type: application/json" \
  -d '{"query":"小学科学实验","media_type":"video","count":5}'
```

---

## 📁 文件管理

### 自动保存功能

系统会自动将以下内容保存为Markdown文件：

1. **初始教案** - `{session_id}_initial_lesson_plan_{timestamp}.md`
2. **修改后教案** - `{session_id}_modified_lesson_plan_{timestamp}.md`
3. **媒体推荐结果** - `{session_id}_media_recommendation_{media_type}_{timestamp}.md`

### 文件存储位置

所有文件保存在项目根目录的 `saved_lessons/` 文件夹中。

### 文件命名规则

```
{session_id}_{content_type}_{timestamp}.md

示例:
abc123def456_initial_lesson_plan_20241208_143022.md
abc123def456_modified_lesson_plan_20241208_143422.md
abc123def456_media_recommendation_image_20241208_143622.md
```

---

## 🔧 配置说明

### 环境变量配置

系统需要配置以下API密钥（在 `config/settings.py` 中）：

```python
# AI服务配置
INNOSPARK_API_KEY = "your_innospark_api_key"
INNOSPARK_API_URL = "https://api.innospark.com/v1/chat/completions"

# 媒体服务配置
PEXELS_API_KEY = "your_pexels_api_key"
YOUTUBE_API_KEY = "your_youtube_api_key"
```

### 服务启动配置

在 `run.py` 中可以调整服务启动参数：

```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",    # 监听地址
    port=8000,         # 端口号
    reload=True,       # 开发模式热重载
    access_log=True    # 访问日志
)
```