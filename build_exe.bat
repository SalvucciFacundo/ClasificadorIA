@echo off
echo Instalando dependencias...
pip install -r requirements.txt

echo Construyendo ejecutable desde .spec...
pyinstaller --noconfirm --clean ClasificadorIA.spec

echo Build completado. El ejecutable esta en la carpeta dist.
pause
