@echo off
echo ========================================
echo Actualizando recursos (UI y Logic)
echo ========================================
echo.

if not exist dist\ClasificadorIA.exe (
    echo ERROR: No se encontro el ejecutable en dist\
    echo Por favor ejecuta primero build_optimized.bat
    pause
    exit /b
)

echo Copiando interfaz...
xcopy /Y /Q /S ui\*.* dist\ui\

echo Copiando logica Python...
xcopy /Y /Q /S logic\*.py dist\logic\

echo.
echo Recursos actualizados correctamente.
echo Puedes ejecutar dist\ClasificadorIA.exe
echo.
pause
