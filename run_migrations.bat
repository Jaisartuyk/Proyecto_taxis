@echo off
chcp 65001 >nul
cd /d "C:\Users\H P\OneDrive\Imágenes\virtual\proyecto_completo"
echo Ejecutando makemigrations...
python manage.py makemigrations
echo.
echo Ejecutando migrate...
python manage.py migrate
pause

