@echo off
cd /d "C:\Scripts\db_automations\automate"
call "C:\Scripts\db_automations\Env_\Scripts\activate.bat"
python manage.py cpu_viz
pause