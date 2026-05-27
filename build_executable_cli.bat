@echo off
REM =========================================================
REM  Build do executável em modo **console** (para CLI e ajuda)
REM =========================================================

pushd "%~dp0"

REM ----- 1. Garante que o virtual‑env exista -----
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate

REM ----- 2. Atualiza pip e instala dependências -----
pip install --upgrade pip
if not exist requirements.txt (
    echo ==== ERRO: requirements.txt não encontrado ==== && popd && exit /b 1
)
pip install -r requirements.txt

REM ----- 3. Remove artefatos de builds anteriores -----
if exist dist\gad_cli.exe ( del /f /q dist\gad_cli.exe )
if exist build\gad_cli ( rmdir /s /q build\gad_cli )
if exist gad_cli.spec ( del /f /q gad_cli.spec )

REM ----- 4. Build **console** (sem a flag --windowed) -----
pyinstaller ^
    --clean ^
    --name gad_cli ^
    --onefile ^
    --add-data ".env;." ^
    --add-data "assets;assets" ^
    --paths venv\Lib\site-packages ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --hidden-import=idna ^
    --hidden-import=charset_normalizer ^
    --hidden-import=certifi ^
    --hidden-import=tabulate ^
    --hidden-import=dotenv ^
    --hidden-import=pyzipper ^
    --collect-all=requests ^
    --collect-all=urllib3 ^
    --collect-all=idna ^
    --collect-all=charset_normalizer ^
    --collect-all=certifi ^
    --collect-all=tabulate ^
    --collect-all=dotenv ^
    --collect-all=pyzipper ^
    main.py

popd
pause
