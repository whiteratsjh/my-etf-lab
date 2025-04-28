#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Run the Streamlit app
echo "Running Streamlit app..."
streamlit run streamlit_app.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false
