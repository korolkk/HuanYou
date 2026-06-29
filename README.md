# 🏔️ 欢游 HuanYou — AI旅游助手

基于 Multi-Agent 架构的智能旅游管理系统，为旅行社提供**行程管理、短视频脚本生成、一键导出剪映、客户画像分析**等功能。

## ✨ 功能

### 店长端
| 功能 | 说明 |
|------|------|
| 📋 行程管理 | 创建/导入/编辑旅游线路，支持 Excel 批量导入 |
| 🎬 **短视频脚本** | AI 4阶段流水线生成脚本（生成→润色→评估），支持抖音/快手/视频号/小红书 |
| ✂️ **一键导出剪映** | 脚本导出为 CapCut 草稿 ZIP，解压即可在剪映中编辑 |
| 👥 客户画像 | 基于历史订单和对话的 AI 用户偏好分析 |
| 💬 AI 对话 | 智能助手覆盖行程查询、脚本生成、客户分析 |

### 用户端
| 功能 | 说明 |
|------|------|
| 🔍 智能推荐 | 自然语言描述需求，AI 匹配最佳行程 |
| 🧳 全流程服务 | 报名前/行程中/行程后随时获取信息支持 |
| 📜 历史行程 | 查看订单记录和旅行足迹统计 |

## 🏗 技术架构

```
Vue 3 + Element Plus (前端)
        ↓
FastAPI (API 网关 + JWT 认证)
        ↓
LangGraph Supervisor → 6 个专职 Agent
        ↓
PostgreSQL/pgvector + Redis + MinIO
```

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3.4 + Vite + Element Plus + ECharts + Pinia |
| 后端 | FastAPI + LangChain + LangGraph |
| AI | DeepSeek-V3 / 通义千问 Qwen-Max |
| 数据库 | PostgreSQL + pgvector（生产）/ SQLite（本地开发） |
| 检索引擎 | RAG 混合检索（语义 + 关键词 + RRF 融合 + BGE 重排序） |
| 部署 | Docker Compose（PostgreSQL + Redis + MinIO） |

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone git@github.com:korolkk/HuanYou.git
cd HuanYou
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，填入 DeepSeek API Key（[免费获取](https://platform.deepseek.com)）：

```ini
DEEPSEEK_API_KEY=sk-your-key-here
```

### 3. 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..
```

### 4. 初始化数据库

```bash
cd backend
python -m scripts.seed_data
```

### 5. 启动服务

**Windows PowerShell:**
```powershell
.\start.ps1 backend    # 启动后端 (端口 8000)
.\start.ps1 frontend   # 启动前端 (端口 5173) — 新终端窗口
```

**macOS / Linux / Git Bash:**
```bash
# 终端 1：后端
cd backend && uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend && npm run dev
```

### 6. 访问

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端页面 |
| http://localhost:8000/docs | API 文档 (Swagger) |

**测试账号：**

| 角色 | 手机号 | 密码 |
|------|--------|------|
| 店长 | 13800000001 | admin123 |
| 用户 | 13800000002 | user123 |

## 📁 项目结构

```
HuanYou/
├── backend/
│   ├── app/
│   │   ├── agents/          # 6 个 LangGraph Agent
│   │   │   ├── supervisor.py      # 意图路由主管
│   │   │   ├── trip_manager.py    # 行程管理
│   │   │   ├── script_writer.py   # 短视频脚本生成
│   │   │   ├── recommendation.py  # 智能推荐
│   │   │   ├── trip_support.py    # 全流程服务
│   │   │   ├── customer_profile.py# 客户画像
│   │   │   └── history_agent.py   # 历史查询
│   │   ├── api/             # REST API 路由
│   │   ├── models/          # SQLAlchemy 数据模型 (9张表)
│   │   ├── rag/             # RAG 检索引擎
│   │   ├── services/        # 业务逻辑层
│   │   │   ├── script_service.py  # 脚本4阶段生成
│   │   │   ├── capcut_service.py  # 剪映草稿导出
│   │   │   └── import_service.py  # Excel 导入
│   │   └── schemas/         # Pydantic 验证模型
│   └── scripts/seed_data.py # 测试数据填充
├── frontend/
│   └── src/
│       ├── views/shop/      # 店长端页面
│       │   ├── ScriptStudio.vue   # 脚本工作台（核心）
│       │   ├── TripImport.vue     # 行程导入
│       │   └── ...
│       ├── views/user/      # 用户端页面
│       └── components/      # 可复用组件
├── data/                    # 示例数据文件
├── docker-compose.yml       # Docker 部署
└── start.ps1                # Windows 启动脚本
```

## 🎬 脚本生成 + 剪映导出流程

```
选择行程 → 配置参数(平台/时长/风格)
    → AI 4阶段生成 (研究→创作→润色→评估)
    → 分段编辑 (时间码+配图+BGM)
    → 一键导出剪映 ZIP
    → 解压到 CapCut 草稿目录
    → 打开剪映即可编辑导出
```

## 📝 License

MIT
