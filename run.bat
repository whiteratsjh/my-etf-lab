@echo off
:: Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate the virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

:: Install dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

:: Run the Streamlit app
echo Running Streamlit app...
streamlit run streamlit_app.py