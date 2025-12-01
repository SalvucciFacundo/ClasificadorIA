@echo off
echo ========================================
echo Compilando Clasificador IA (Optimizado)
echo ========================================
echo.
echo Este build NO incluye UI ni logica Python en el .exe
echo Los recursos se cargan desde carpetas externas
echo.

REM Limpiar builds anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Compilar con PyInstaller (sin UI ni logic embebidos)
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name ClasificadorIA ^
    --hidden-import=webview ^
    --hidden-import=flask ^
    --hidden-import=engineio.async_drivers.threading ^
    --collect-all torch ^
    --collect-all torchvision ^
    app.py

echo.
echo ========================================
echo Preparando estructura de carpetas
echo ========================================

REM Crear estructura de carpetas junto al .exe
cd dist
mkdir ui 2>nul
mkdir logic 2>nul
mkdir modelo 2>nul
mkdir entrada 2>nul
mkdir clasificaciones 2>nul
mkdir dataset_base 2>nul
mkdir index 2>nul
mkdir logs 2>nul

REM Copiar archivos externos
echo Copiando interfaz...
xcopy /Y /Q ..\ui\*.* ui\

echo Copiando logica Python...
xcopy /Y /Q ..\logic\*.py logic\

echo.
echo ========================================
echo Build completado!
echo ========================================
echo.
echo El ejecutable esta en: dist\ClasificadorIA.exe
echo.
echo Estructura de carpetas creada:
echo   - ui\          (HTML, CSS, JS)
echo   - logic\       (Python modules)
echo   - modelo\      (Modelos entrenados)
echo   - entrada\     (Imagenes a clasificar)
echo   - clasificaciones\ (Imagenes clasificadas)
echo   - dataset_base\    (Dataset de entrenamiento)
echo.
echo IMPORTANTE: Para modificar la interfaz o logica,
echo edita los archivos en ui\ o logic\ y reinicia el programa.
echo NO es necesario recompilar el .exe
echo.
pause
