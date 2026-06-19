# Root Makefile for macOS FaceUnlock Platform Control

.PHONY: all bootstrap check test clean install uninstall

all: check

bootstrap:
	@echo "Bootstrapping development environment..."
	@bash scripts/bootstrap.sh

check:
	@echo "Running system environment diagnostic checks..."
	@bash scripts/check_env.sh

test:
	@echo "Executing automated test suite..."
	@./venv/bin/python -m unittest discover -s tests -p "test_*.py"

clean:
	@echo "Cleaning transient files, logs, and compiled assets..."
	@rm -rf __pycache__ vision_daemon/core/__pycache__ shared/__pycache__ ipc/__pycache__ tests/__pycache__
	@rm -f *.pyc vision_daemon/core/*.pyc shared/*.pyc ipc/*.pyc tests/*.pyc
	@rm -rf .pytest_cache
	@cd pam && make clean
	@echo "Cleanup completed."

install:
	@echo "Installing PAM module and registering LaunchAgent daemon..."
	@sudo bash scripts/install.sh

uninstall:
	@echo "Uninstalling PAM module and daemon services..."
	@sudo bash scripts/uninstall.sh
