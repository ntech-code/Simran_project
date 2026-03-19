#!/bin/bash

# ============================================================================
# Indian Tax Analysis System - Automated Setup Script (Linux/Mac)
# ============================================================================

echo ""
echo "============================================================================"
echo "   Indian Tax Analysis System - Automated Setup"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}[ERROR] Git is not installed. Please install Git first.${NC}"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

echo -e "${GREEN}[INFO] All prerequisites found!${NC}"
echo ""

# Clone or pull repository
if [ -d ".git" ]; then
    echo -e "${BLUE}[STEP 1/5] Pulling latest changes from GitHub...${NC}"
    git pull origin main
else
    echo -e "${BLUE}[STEP 1/5] Cloning repository from GitHub...${NC}"
    cd ..
    git clone https://github.com/Pratham-Solanki911/TaxAnalyst.git
    cd TaxAnalyst
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to clone/pull repository${NC}"
    exit 1
fi

echo -e "${GREEN}[SUCCESS] Repository updated!${NC}"
echo ""

# Setup environment files
echo -e "${BLUE}[STEP 2/5] Setting up environment files...${NC}"

# Backend .env
if [ ! -f ".env" ]; then
    echo -e "${GREEN}[INFO] Creating backend .env file...${NC}"
    cat > .env << 'EOF'
# Gemini API Configuration
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key-here
EOF
    echo -e "${YELLOW}[WARN] Please update .env with your actual GEMINI_API_KEY${NC}"
else
    echo -e "${GREEN}[INFO] Backend .env already exists${NC}"
fi

# Frontend .env
if [ ! -f "frontend/.env" ]; then
    echo -e "${GREEN}[INFO] Creating frontend .env file...${NC}"
    cat > frontend/.env << 'EOF'
# API Configuration
VITE_API_URL=http://localhost:8000

# Google OAuth Configuration
# Get your Client ID from: https://console.cloud.google.com/apis/credentials
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
EOF
    echo -e "${YELLOW}[WARN] Please update frontend/.env with your VITE_GOOGLE_CLIENT_ID${NC}"
    echo -e "${GREEN}[INFO] Or use Development Mode to bypass Google OAuth${NC}"
else
    echo -e "${GREEN}[INFO] Frontend .env already exists${NC}"
fi

echo -e "${GREEN}[SUCCESS] Environment files ready!${NC}"
echo ""

# Install backend dependencies
echo -e "${BLUE}[STEP 3/5] Installing Python dependencies...${NC}"
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install Python dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}[SUCCESS] Python dependencies installed!${NC}"
echo ""

# Install frontend dependencies
echo -e "${BLUE}[STEP 4/5] Installing Node.js dependencies...${NC}"
cd frontend
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install Node.js dependencies${NC}"
    cd ..
    exit 1
fi

cd ..
echo -e "${GREEN}[SUCCESS] Node.js dependencies installed!${NC}"
echo ""

# Create start scripts
echo -e "${BLUE}[STEP 5/5] Creating start scripts...${NC}"

# Create start-backend.sh
cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "Starting Backend Server..."
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
EOF
chmod +x start-backend.sh

# Create start-frontend.sh
cat > start-frontend.sh << 'EOF'
#!/bin/bash
echo "Starting Frontend Server..."
cd frontend
npm run dev
EOF
chmod +x start-frontend.sh

# Create start-all.sh
cat > start-all.sh << 'EOF'
#!/bin/bash
echo "Starting Tax Analysis System..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Start backend
echo "Starting Backend..."
./start-backend.sh &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting Frontend..."
./start-frontend.sh &
FRONTEND_PID=$!

echo ""
echo "============================================================================"
echo "   Tax Analysis System is running!"
echo "============================================================================"
echo ""
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3000"
echo "API Docs:    http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
EOF
chmod +x start-all.sh

echo -e "${GREEN}[SUCCESS] Start scripts created!${NC}"
echo ""

echo "============================================================================"
echo "   Setup Complete!"
echo "============================================================================"
echo ""
echo "IMPORTANT: Configure your environment variables:"
echo ""
echo "1. Edit .env and add your GEMINI_API_KEY"
echo "   Get it from: https://makersuite.google.com/app/apikey"
echo ""
echo "2. Edit frontend/.env and add your VITE_GOOGLE_CLIENT_ID"
echo "   Get it from: https://console.cloud.google.com/apis/credentials"
echo "   OR use 'Continue as Developer' button to bypass Google OAuth"
echo ""
echo "To start the application:"
echo "   ./start-all.sh        (starts both backend and frontend)"
echo "   ./start-backend.sh    (backend only)"
echo "   ./start-frontend.sh   (frontend only)"
echo ""
echo "Access the application at: http://localhost:3000"
echo ""
echo "============================================================================"
