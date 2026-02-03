# Makefile for Oink Platform
# Auto-detects architecture (x86_64 or arm64/aarch64) to select the correct docker-compose file.

ARCH := $(shell uname -m)

# Select docker-compose file based on architecture
ifeq ($(ARCH),x86_64)
    COMPOSE_FILE := docker-compose.x86.yml
    PLATFORM_MSG := "Running on x86_64 (CPU Only)"
else
    COMPOSE_FILE := docker-compose.yml
    PLATFORM_MSG := "Running on ARM/Jetson (GPU Enabled)"
endif

.PHONY: help build run stop logs clean info

help:
	@echo "Oink Platform Makefile"
	@echo "Detected Architecture: $(ARCH)"
	@echo "Using: $(COMPOSE_FILE)"
	@echo ""
	@echo "Targets:"
	@echo "  make build    - Build containers"
	@echo "  make run      - Start services (daemon mode)"
	@echo "  make stop     - Stop services"
	@echo "  make logs     - Follow logs"
	@echo "  make clean    - Stop and remove containers, networks, and images"
	@echo "  make info     - Show environment info"

info:
	@echo "========================================"
	@echo $(PLATFORM_MSG)
	@echo "Architecture: $(ARCH)"
	@echo "Compose File: $(COMPOSE_FILE)"
	@echo "========================================"

build:
	@echo "Building for $(ARCH)..."
	docker-compose -f $(COMPOSE_FILE) build

run:
	@echo "Starting services for $(ARCH)..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "Running migrations..."
	docker-compose -f $(COMPOSE_FILE) exec -T app python manage.py migrate
	@echo "Creating superuser (gaspar)..."
	docker-compose -f $(COMPOSE_FILE) exec -T app python scripts/create_superuser.py

stop:
	@echo "Stopping services..."
	docker-compose -f $(COMPOSE_FILE) down

logs:
	@echo "Following logs..."
	docker-compose -f $(COMPOSE_FILE) logs -f

clean:
	@echo "Cleaning up..."
	docker-compose -f $(COMPOSE_FILE) down -v --rmi all
