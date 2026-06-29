.PHONY: help dev backend frontend db seed migrate docker-up docker-down install test clean

# Default target
help:
	@echo "欢游 HuanYou - AI旅游助手"
	@echo ""
	@echo "命令:"
	@echo "  make install    - 安装所有依赖"
	@echo "  make dev        - 启动开发环境 (docker + backend + frontend)"
	@echo "  make backend    - 仅启动后端"
	@echo "  make frontend   - 仅启动前端"
	@echo "  make docker-up  - 启动Docker服务 (PostgreSQL, Redis, MinIO)"
	@echo "  make docker-down- 停止Docker服务"
	@echo "  make db-init    - 初始化数据库 (migrate + seed)"
	@echo "  make migrate    - 运行数据库迁移"
	@echo "  make seed       - 填充测试数据"
	@echo "  make test       - 运行测试"
	@echo "  make clean      - 清理临时文件"

# Install all dependencies
install:
	@echo "安装Python依赖..."
	pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "安装完成!"

# Start full dev environment
dev: docker-up
	@echo "启动后端 (uvicorn)..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "启动前端 (vite)..."
	cd frontend && npm run dev &
	@echo "开发环境已启动:"
	@echo "  API文档: http://localhost:8000/docs"
	@echo "  前端:    http://localhost:5173"
	@wait

# Backend only
backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend only
frontend:
	cd frontend && npm run dev

# Docker services
docker-up:
	docker-compose up -d postgres redis minio
	@echo "等待服务就绪..."
	@sleep 3
	@echo "Docker服务已启动"

docker-down:
	docker-compose down

# Database
migrate:
	cd backend && alembic upgrade head
	@echo "数据库迁移完成"

seed:
	cd backend && python -m scripts.seed_data

db-init: migrate seed
	@echo "数据库初始化完成"

# New migration
migration:
	@read -p "迁移描述: " desc; \
	cd backend && alembic revision --autogenerate -m "$$desc"

# Testing
test:
	cd backend && python -m pytest tests/ -v

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	rm -rf frontend/node_modules/.vite 2>/dev/null || true
	@echo "清理完成"
