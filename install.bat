@echo off
echo Setting up AI Personal Assistant...
echo.

REM Activate or create virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Virtual environment created and activated.
)

echo.
echo Updating pip...
python -m pip install --upgrade pip

echo.
echo Installing lightweight dependencies...
echo ======================================

REM Install packages one by one
python -m pip install google-generativeai==0.3.0
python -m pip install streamlit==1.28.0
python -m pip install streamlit-chat==0.1.0
python -m pip install requests==2.31.0
python -m pip install beautifulsoup4==4.12.2
python -m pip install python-dateutil==2.8.2
python -m pip install python-dotenv==1.0.0
python -m pip install wolframalpha==5.0.0

echo.
echo Checking .env file...
if not exist .env (
    echo Creating .env file...
    echo # Gemini API Key (free from https://aistudio.google.com/app/apikey) > .env
    echo GEMINI_API_KEY=your_gemini_api_key_here >> .env
    echo. >> .env
    echo # NewsAPI Key (free tier from https://newsapi.org) >> .env
    echo NEWS_API_KEY=your_news_api_key_here >> .env
    echo. >> .env
    echo # Weather API (free from https://openweathermap.org/api) >> .env
    echo WEATHER_API_KEY=your_weather_api_key_here >> .env
    echo. >> .env
    echo # Optional: WolframAlpha (from https://wolframalpha.com) >> .env
    echo WOLFRAM_APP_ID=your_wolfram_app_id >> .env
    echo .env file created. Please update with your API keys.
) else (
    echo .env file already exists.
)

echo.
echo Creating directory structure...
if not exist assistant mkdir assistant
if not exist config mkdir config
if not exist utils mkdir utils

echo. > assistant\__init__.py
echo. > config\__init__.py
echo. > utils\__init__.py

echo.
echo Running quick test...
python quick_test.py

echo.
echo ======================================
echo Setup complete!
echo.
echo To run the assistant:
echo 1. Edit .env file with your Gemini API key
echo 2. Run: python app.py
echo 3. Or for web interface: streamlit run web_app.py
echo ======================================
pause