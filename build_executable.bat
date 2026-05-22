@echo off
REM -------------------------------------------------
REM  Build do executável – versão robusta (PowerShell ok)
REM -------------------------------------------------

REM ----- 1. Garante que estamos na pasta do script -----
pushd "%~dp0"

REM ----- 2. Cria/ativa ambiente virtual -----
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate

REM ----- 3. Atualiza pip e instala dependências -----
pip install --upgrade pip
if not exist requirements.txt (
    echo ==== ERRO: requirements.txt não encontrado ==== && popd && exit /b 1
)
pip install -r requirements.txt

REM ----- 4. Ícone do executável -----
set "ICON_ARG=--icon c:/projetos/gad/assets/gad.ico"

REM ----- 5. Remove artefatos de builds anteriores -----
if exist dist ( rmdir /s /q dist )
if exist build ( rmdir /s /q build )
if exist gad.spec ( del /f /q gad.spec )

REM ----- 6. Build com coleta completa e debug -----
pyinstaller --clean --debug=all ^
    --name gad ^
    --onefile ^
    --add-data ".env;." ^
    --add-data "venv\Lib\site-packages\PySide6\Qt\plugins;Qt\plugins" ^
    %ICON_ARG% ^
    --paths venv\Lib\site-packages ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --hidden-import=idna ^
    --hidden-import=charset_normalizer ^
    --hidden-import=certifi ^
    --hidden-import=tabulate ^
    --hidden-import=dotenv ^
    --collect-all=requests ^
    --collect-all=urllib3 ^
    --collect-all=idna ^
    --collect-all=charset_normalizer ^
    --collect-all=certifi ^
    --collect-all=tabulate ^
    --collect-all=dotenv ^
    main.py

popd
pause
