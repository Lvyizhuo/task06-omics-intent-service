# 组学智能体意图识别服务 - 部署指南

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [Docker 部署](#docker-部署)
- [手动部署](#手动部署)
- [配置说明](#配置说明)
- [运维管理](#运维管理)
- [故障排查](#故障排查)

## 环境要求

### Docker 部署（推荐）
- Docker >= 20.10
- Docker Compose >= 2.0（可选）

### 手动部署
- Python >= 3.11
- pip 或 poetry

## 快速开始

### 1. 准备配置文件

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件，填入实际值
vim .env
```

必须配置的项：
- `LLM_API_KEY`：阿里云百炼 API Key

### 2. Docker 部署（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 手动部署

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

## Docker 部署

### 构建镜像

```bash
# 使用 docker-compose（推荐）
docker-compose build

# 或使用 docker 命令
docker build -t omics-intent-service .
```

### 启动容器

```bash
# 使用 docker-compose（推荐）
docker-compose up -d

# 或使用 docker 命令
docker run -d \
  --name omics-intent-service \
  -p 8010:8010 \
  --env-file .env \
  --restart unless-stopped \
  omics-intent-service
```

### 查看日志

```bash
# docker-compose 方式
docker-compose logs -f

# docker 命令方式
docker logs -f omics-intent-service
```

### 停止服务

```bash
# docker-compose 方式
docker-compose down

# docker 命令方式
docker stop omics-intent-service
docker rm omics-intent-service
```

## 手动部署

### 1. 环境准备

```bash
# 创建项目目录
mkdir -p /opt/omics-intent-service
cd /opt/omics-intent-service

# 克隆代码
git clone <repository-url> .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
vim .env
```

### 3. 启动服务

```bash
# 前台启动（调试用）
uvicorn app.main:app --host 0.0.0.0 --port 8010

# 后台启动
nohup uvicorn app.main:app --host 0.0.0.0 --port 8010 > app.log 2>&1 &
```

### 4. Systemd 服务（生产环境推荐）

创建服务文件 `/etc/systemd/system/omics-intent.service`：

```ini
[Unit]
Description=Omics Intent Recognition Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/omics-intent-service
Environment="PATH=/opt/omics-intent-service/venv/bin"
EnvironmentFile=/opt/omics-intent-service/.env
ExecStart=/opt/omics-intent-service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8010
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable omics-intent
sudo systemctl start omics-intent
sudo systemctl status omics-intent
```

## 配置说明

### 环境变量列表

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `LLM_API_KEY` | ✅ | - | 阿里云百炼 API Key |
| `LLM_BASE_URL` | ❌ | `https://dashscope.aliyuncs.com/compatible-mode/v1` | LLM 服务地址 |
| `LLM_MODEL` | ❌ | `qwen-plus-latest` | LLM 模型名称 |
| `PLANTCAD2_BASE_URL` | ❌ | `http://localhost:8005` | PlantCAD2 服务地址 |
| `EVO2_BASE_URL` | ❌ | `http://36.137.205.153:8666` | EVO2 服务地址 |
| `HOST` | ❌ | `0.0.0.0` | 服务监听地址 |
| `PORT` | ❌ | `8010` | 服务监听端口 |
| `LLM_TIMEOUT` | ❌ | `30` | LLM 调用超时（秒）|
| `API_TIMEOUT` | ❌ | `60` | 下游 API 调用超时（秒）|
| `MAX_RETRIES` | ❌ | `3` | 最大重试次数 |

### 配置优先级

1. 环境变量（最高优先级）
2. `.env` 文件
3. 默认值

## 运维管理

### 健康检查

```bash
# HTTP 健康检查
curl http://localhost:8010/health

# 预期响应
{
  "status": "healthy",
  "service": "omics-intent",
  "version": "1.0.0"
}
```

### 日志管理

**Docker 日志：**
```bash
# 查看实时日志
docker-compose logs -f

# 查看最近 100 行
docker-compose logs --tail 100

# 查看特定时间后的日志
docker-compose logs --since 2024-01-01T00:00:00
```

**手动部署日志：**
```bash
# 查看日志文件
tail -f app.log

# 使用 journalctl（systemd）
journalctl -u omics-intent -f
```

### 性能监控

```bash
# Docker 容器资源使用
docker stats omics-intent-service

# 查看容器详情
docker inspect omics-intent-service
```

### 备份与恢复

**备份配置：**
```bash
# 备份 .env 文件
cp .env .env.backup.$(date +%Y%m%d)
```

**恢复配置：**
```bash
# 恢复配置
cp .env.backup.20240101 .env
docker-compose restart
```

## 故障排查

### 常见问题

#### 1. 服务无法启动

**检查配置：**
```bash
# 验证 .env 文件
cat .env

# 检查必需配置
grep LLM_API_KEY .env
```

**检查端口占用：**
```bash
# macOS/Linux
lsof -i :8010

# 或使用 ss
ss -tlnp | grep 8010
```

**查看启动日志：**
```bash
docker-compose logs omics-intent
```

#### 2. LLM 调用失败

**检查 API Key：**
```bash
# 测试 API 连通性
curl -H "Authorization: Bearer $LLM_API_KEY" \
  "$LLM_BASE_URL/models"
```

**查看错误日志：**
```bash
docker-compose logs | grep -i error
```

#### 3. 下游服务不可达

**检查网络连通性：**
```bash
# 测试 PlantCAD2
curl http://localhost:8005/health

# 测试 EVO2
curl http://36.137.205.153:8666/health
```

**Docker 网络问题：**
```bash
# 检查容器网络
docker network ls
docker network inspect task06-omics-intent-service_omics-network
```

#### 4. 性能问题

**查看资源使用：**
```bash
# Docker 资源监控
docker stats

# 系统资源
top
htop
```

**调整超时配置：**
```env
# 增加超时时间
LLM_TIMEOUT=60
API_TIMEOUT=120
```

### 日志级别调整

临时调整日志级别（需重启服务）：

```python
# 在 app/main.py 中修改
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 回滚操作

**Docker 回滚：**
```bash
# 使用之前的镜像版本
docker-compose down
docker-compose up -d --build
```

**手动部署回滚：**
```bash
# 切换到之前的版本
git checkout <previous-commit>
pip install -r requirements.txt
sudo systemctl restart omics-intent
```

## 更新升级

### Docker 方式

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose down
docker-compose up -d --build
```

### 手动方式

```bash
# 拉取最新代码
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl restart omics-intent
```

## 安全建议

1. **API Key 安全**
   - 不要将 `.env` 文件提交到版本控制
   - 定期轮换 API Key
   - 使用密钥管理服务（如 AWS Secrets Manager）

2. **网络安全**
   - 仅暴露必要的端口
   - 使用防火墙限制访问
   - 考虑使用反向代理（Nginx）

3. **容器安全**
   - 使用非 root 用户运行（已配置）
   - 定期更新基础镜像
   - 扫描镜像漏洞

## 生产环境建议

1. **使用反向代理**

   Nginx 配置示例：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8010;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

2. **HTTPS 配置**
   - 使用 Let's Encrypt 获取证书
   - 配置自动续期

3. **监控告警**
   - 配置 Prometheus + Grafana 监控
   - 设置健康检查告警
   - 监控 LLM API 调用配额

4. **日志收集**
   - 使用 ELK 或 Loki 收集日志
   - 配置日志轮转

---

如有问题，请查看 [README.md](README.md) 或联系开发团队。
