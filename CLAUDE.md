# CLAUDE.md — 欢游 HuanYou AI旅游助手

## 项目概述

欢游是一个基于 Multi-Agent 架构的旅行社智能管理系统。

- **前端**: Vue 3.4 + Vite + Element Plus + ECharts + Pinia + TypeScript
- **后端**: FastAPI + LangChain + LangGraph + SQLAlchemy 2.0
- **AI**: DeepSeek-V3 (主) / 通义千问 Qwen-Max (备)
- **数据库**: 生产 PostgreSQL + pgvector / 本地开发 SQLite
- **部署**: Docker Compose

## 常用命令

```bash
# 后端
cd backend
python -m scripts.seed_data                          # 初始化SQLite数据库+测试数据
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000  # 启动后端
alembic upgrade head                                  # 数据库迁移(PostgreSQL)

# 前端
cd frontend && npm install && npm run dev             # 启动前端 (端口5173)

# 测试
curl http://localhost:8000/api/health                 # 健康检查
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"phone":"13800000001","password":"admin123"}'  # 登录
```

## 项目结构

```
backend/app/
├── agents/          # 6个LangGraph Agent (supervisor路由+worker执行)
├── api/             # FastAPI路由 (auth/shop/user/agent_chat)
├── models/          # SQLAlchemy模型 (9张表: Customer/Trip/Order/VideoScript/...)
├── schemas/         # Pydantic请求/响应验证
├── services/        # 业务逻辑层 (script/capcut/import/trip/order/customer)
├── rag/             # RAG检索引擎 (parser/chunker/embedder/indexer/retriever/reranker)
└── utils/           # JWT认证等工具

frontend/src/
├── views/shop/      # 店长端页面 (Dashboard/TripList/TripDetail/ScriptStudio/TripImport/...)
├── views/user/      # 用户端页面 (Home/Recommend/MyOrders/History/TripChat)
├── components/shop/ # 可复用组件 (TripSearchSelect/ScriptSegmentEditor/QualityRadar/ExportDialog/...)
├── stores/          # Pinia状态管理 (auth)
├── api/             # Axios API封装 (authApi/tripApi/scriptApi/importApi/...)
└── types/           # TypeScript类型定义
```

## 核心数据流

### 脚本生成+剪映导出
```
店长选择行程 → ScriptStudio.vue → POST /api/shop/scripts/generate
→ ScriptGenerationService (4阶段: 研究→生成→润色→评估)
→ 保存到 video_scripts 表 (script_json 存储 ScriptSegment[])
→ 点击导出 → POST /api/shop/scripts/{id}/export/capcut
→ CapCutExportService 生成 draft_content.json → ZIP下载
→ 用户解压到 CapCut 草稿目录 → 打开剪映即可编辑
```

### Agent对话
```
POST /api/agent/chat → agent_chat.py → _quick_route(关键词匹配)
→ 分发给各handler (_handle_script_writer/_handle_recommendation/...)
→ 各handler调用对应Service → 返回结果并保存到conversations表
```

## 关键约定

- **所有API响应**使用中文
- **数据库兼容**: SQLite本地开发（`DB_TYPE=sqlite`），自动使用JSON替代PostgreSQL ARRAY/JSONB
- **密码哈希**: PBKDF2-SHA256（非bcrypt，兼容Windows Python 3.14）
- **UUID主键**: String(36) 通用格式
- **剪映时间码**: 秒→微秒(`*1_000_000`)，草稿JSON格式参考 `capcut_service.py`
- **测试账号**: `13800000001/admin123`(店长) / `13800000002/user123`(用户)
- **配置文件**: `.env` (不提交Git)，模板见 `.env.example`

## 当前状态

- ✅ 后端API全覆盖 (CRUD + Agent + RAG + 剪映导出)
- ✅ 前端店长端核心页面完成 (Dashboard/TripList/TripDetail/ScriptStudio/TripImport)
- 🔜 CustomerList/CustomerProfile 为占位桩
- 🔜 需要配置 `DEEPSEEK_API_KEY` 才能启用AI功能（生成/润色/评估）
- 🔜 Mem0记忆层待集成
