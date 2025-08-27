#!/bin/bash

# Local Development Startup Script
echo "🚀 Starting LHSFFL Platform in Local Development Mode..."

echo ""
echo "📋 Setup Options:"
echo "1. Local SQLite Database (no database connection needed)"
echo "2. Remote MySQL Database (requires SSH tunnel)"
echo ""

read -p "Choose option (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "🗄️  Using Local SQLite Database..."
    echo "✅ No additional setup required!"
    echo ""
    echo "🎯 Starting services..."
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:5000"
    echo ""
    
    # Start both services
    npm run start-local
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "🔒 Using Remote MySQL Database via SSH Tunnel..."
    echo "📡 First, start the SSH tunnel in another terminal:"
    echo ""
    echo "   cd lhsffl-servers"
    echo "   ssh -i ~/.ssh/dynasty-key.pem -L 3307:dynasty-rw.chqkmuq4yu49.us-west-2.rds.amazonaws.com:3306 ec2-user@34.219.242.88"
    echo ""
    read -p "Press Enter when tunnel is ready..."
    
    echo ""
    echo "🎯 Starting services with database connection..."
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend API: http://localhost:5000"
    echo "   - Database: Remote MySQL via tunnel"
    echo ""

    # Start both services
    npm run start-local
    
else
    echo "❌ Invalid choice. Please run the script again and choose 1 or 2."
    exit 1
fi
