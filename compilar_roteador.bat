@echo off
set "ARQUIVO=%~nx1"
set "CAMINHO_COMPLETO=%~1"
set OPENOUT_ANY=a

if not exist "..\publica" mkdir "..\publica"
if not exist "..\restrita" mkdir "..\restrita"

echo %ARQUIVO% | findstr /I "_ALUNO" >nul
if %errorlevel% equ 0 (
    echo [ROTEADOR] Compilando versao ALUNO para ../publica...
    pdflatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=../publica "%CAMINHO_COMPLETO%"
    exit /b 0
)

echo %ARQUIVO% | findstr /I "_PROF" >nul
if %errorlevel% equ 0 (
    echo [ROTEADOR] Compilando versao PROFESSOR para ../restrita...
    pdflatex -synctex=1 -interaction=nonstopmode -file-line-error -output-directory=../restrita "%CAMINHO_COMPLETO%"
    exit /b 0
)

echo [ROTEADOR] Arquivo ignorado (nao e casca _ALUNO nem _PROF).
exit /b 0