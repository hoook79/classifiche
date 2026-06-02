@echo off
chcp 65001 > nul
echo ========================================================
echo   [GITHUB DEPLOY] INVIO CLASSIFICA A GITHUB IN CORSO...
echo ========================================================

:: 1. Copia classifica_radio.html in index.html per la pubblicazione online
if exist classifica_radio.html (
    copy /Y classifica_radio.html index.html > nul
    echo  [OK] Copiato classifica_radio.html in index.html.
) else (
    echo  [ERRORE] File classifica_radio.html non trovato! Esegui prima genera_html.py.
    pause
    exit /b 1
)

:: 2. Inizializza Git se non presente
if not exist .git (
    echo Inizializzazione repository Git locale...
    git init
    git branch -M main
)

:: 3. Controlla se il remote "origin" esiste
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [CONFIGURAZIONE REMOTE GITHUB]
    echo Per caricare il sito online, inserisci l'indirizzo HTTPS del tuo repository GitHub.
    echo Esempio: https://github.com/hoook79/hoook79.github.io.git
    echo.
    set /p repo_url="Incolla l'URL HTTPS del tuo repository e premi INVIO: "
    
    if "%repo_url%"=="" (
        echo  [ERRORE] Nessun URL inserito. Annullato.
        pause
        exit /b 1
    )
    
    git remote add origin %repo_url%
    echo  [OK] Collegato al repository GitHub: %repo_url%
)

:: 4. Aggiungi i file al tracciamento
git add .gitignore index.html *.py *.bat *.vbs

:: 5. Crea il commit
git commit -m "Aggiornamento classifica e codice (%date% %time%)" > nul 2>&1
if %errorlevel% neq 0 (
    :: Se non ci sono modifiche, il commit fallisce ma non è un errore bloccante
    echo  [INFO] Nessuna modifica rilevata nei file rispetto al commit precedente.
) else (
    echo  [OK] Modifiche salvate nel commit locale.
)

:: 6. Pusha su GitHub
echo Invio dei dati su GitHub in corso (potrebbe richiedere l'autenticazione)...
git push -u origin main

if %errorlevel% eq 0 (
    echo.
    echo ========================================================
    echo   [SUCCESSO] SITO WEB CARICATO ONLINE CON SUCCESSO!
    echo ========================================================
) else (
    echo.
    echo  [ERRORE] Il caricamento su GitHub è fallito. 
    echo  Assicurati che:
    echo  1. L'URL del repository sia corretto.
    echo  2. Tu abbia effettuato l'accesso a GitHub su questo computer.
)

echo.
pause
