from dataclasses import dataclass, field
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
# 优先加载项目根目录的 .env 文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # 如果没有 .env 文件，尝试从环境变量加载
    load_dotenv()


@dataclass
class Settings:
    # LLM 配置（默认使用本地部署的 Qwen3，OpenAI 兼容接口）
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", "not-needed"))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "qwen3-30b"))

    # 下游服务地址
    plantcad2_base_url: str = field(default_factory=lambda: os.getenv("PLANTCAD2_BASE_URL", "http://localhost:8005"))
    evo2_base_url: str = field(default_factory=lambda: os.getenv("EVO2_BASE_URL", "http://36.137.205.153:8666"))
    alphafold3_base_url: str = field(default_factory=lambda: os.getenv("ALPHAFOLD3_BASE_URL", "http://localhost:8015"))

    # 服务配置
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8010")))

    # 超时配置
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "120.0"))
    api_timeout: float = 60.0
    alphafold3_timeout: float = 600.0  # AlphaFold3 结构预测耗时较长（2-10分钟）
    max_retries: int = 3

settings = Settings()
