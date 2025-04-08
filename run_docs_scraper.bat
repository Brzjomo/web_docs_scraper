@echo off
echo Starting Maya Documentation Scraper...

:: Activate Python environment
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" collectPage

:: Run the scraper
python docs_scraper.py

:: Keep the window open
echo.
echo Press any key to exit...
pause > nul 