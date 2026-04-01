#!/bin/bash
echo "========================================================="
echo "  Indian Tax Analysis System - 1-Click Setup (Mac/Linux)"
echo "========================================================="

if ! [ -x "$(command -v docker)" ]; then
  echo "[ERROR] Docker is not installed!"
  echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
  exit 1
fi

if [ ! -f .env ]; then
  echo "[WARNING] .env file not found! Please create it using ENV_SETUP_GUIDE.md"
fi

echo "[1/3] Stopping any old instances..."
docker-compose down --remove-orphans > /dev/null 2>&1

echo "[2/3] Building and starting (first run takes a few minutes)..."
docker-compose up -d --build

echo "[3/3] Opening the application..."
sleep 5
open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || echo "Open http://localhost:3000 in your browser."

echo ""
echo "========================================================="
echo "  DONE! Open http://localhost:3000 in your browser"
echo "  To stop: run 'docker-compose down'"
echo "========================================================="
