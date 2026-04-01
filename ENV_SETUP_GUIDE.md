# 🔒 Environment Setup Guide

## Prerequisites
- Install **Docker Desktop** from https://www.docker.com/products/docker-desktop

## Step 1: Create `.env` file
Create a file named `.env` in the main project folder and paste:

```env
GEMINI_API_KEY="your_gemini_api_key_here"
GOOGLE_CLOUD_PROJECT="your_project_id"
GOOGLE_CLOUD_LOCATION="us-central1"
GOOGLE_APPLICATION_CREDENTIALS="vertex_ai_key.json"
```

## Step 2: Add Vertex AI Key
Place your Google Cloud Service Account JSON file in the main folder, named `vertex_ai_key.json`.

## Step 3: Run the App

**Windows:** Double-click `start_windows.bat`
**Mac:** Open Terminal here → `chmod +x start_mac.sh` → `./start_mac.sh`

The app opens at **http://localhost:3000** automatically!

⚠️ **Never share your `.env` or `vertex_ai_key.json` files publicly!**
