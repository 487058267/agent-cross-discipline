import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Innospark API 配置
INNOSPARK_API_KEY = os.getenv("INNOSPARK_API_KEY", "7V1rpBFgK0DOHPh95pMP8Sxe1DXK_7c0UGJ5Fxpi_ejZiDvklCz38ev2_iLs7VxdaDslykF-DRJQhZDwOD7ZNA==")
INNOSPARK_API_URL = "http://120.55.167.27:9001/v1/chat/completions"

# 媒体API配置 (示例)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "flNU12jcrAIw4suVytmjFMk5qHfEznVdTyOEXgolR2RxO6kOcsDO0hkx")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyBxTSLDIHJjXIJliqXpcXjQxr4T_13_byQ")

# 应用配置
MAX_HISTORY_LENGTH = 10  # 最大历史记录数