# Makefile for StructSim Backend

.PHONY: help install dev lint format check fix-all clean

help:
	@echo "StructSim Backend - 可用命令:"
	@echo "  make install   - 安装依赖"
	@echo "  make dev       - 启动开发服务器"
	@echo "  make lint      - 运行代码检查"
	@echo "  make format    - 格式化代码"
	@echo "  make check     - 运行所有检查"
	@echo "  make fix-all   - 自动修复所有问题"
	@echo "  make clean     - 清理缓存文件"

install:
	pip install -r requirements.txt

dev:
	python run.py --host 127.0.0.1 --port 5000

lint:
	python -m ruff check .
	python -m black --check .
	python -m isort --check-only .

format:
	python -m black .
	python -m isort .

check: lint
	@echo "✅ 所有检查通过"

fix-all:
	python -m black .
	python -m isort .
	python -m ruff check . --fix
	@echo "✅ 自动修复完成"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	@echo "✅ 清理完成"

