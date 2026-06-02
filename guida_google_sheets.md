# Guida: Configurazione Google Sheets & Accessi con Password

Questa guida ti spiega passo-passo come configurare il foglio Google, inserire il codice del server (Apps Script), e abilitare le API Google Cloud per far sì che il tuo computer carichi le classifiche online in modo del tutto gratuito.

---

## 1. Creazione del Foglio Google e Struttura

1. Apri Google Drive e crea un nuovo **Foglio Google**.
2. Rinomina il file in: `RadioCharts_Database` (se usi un altro nome, assicurati di cambiarlo anche in `google_sheets_sync.py` alla riga 7: `SPREADSHEET_NAME = "IlTuoNome"`).
3. All'interno del foglio, crea le seguenti schede (cliccando sul tasto `+` in basso a sinistra):
   * **`Users`**: Gestione utenti e password.
   * **`YearsCache`**: Storico degli anni modificati.
   * **`RadioDatesCache`**: Storico delle radio date modificate.
   * **`Dates_Metadata`**: Gestione interna dei calendari delle date.
   * *Nota: Le schede delle singole radio (`Data_Subasio`, `Data_Divina`, ecc.) verranno create automaticamente dal Python al primo avvio, non devi crearle a mano.*

### Come popolare la scheda `Users`
Apri la scheda `Users` e crea queste colonne nella prima riga:
| A (Username) | B (Password) | C (Role) | D (ExpirationDate) | E (AllowedRadios) |
| :--- | :--- | :--- | :--- | :--- |
| `admin` | `admin123` | `admin` | `2030-12-31` | `all` |
| `utente1` | `pass123` | `user` | `2026-12-31` | `Subasio, Mitology` |

* **Ruolo admin:** Può consultare la classifica e modificare gli anni/date radio dal sito web.
* **Ruolo user:** Può solo consultare la classifica, senza tasti di modifica.
* **ExpirationDate:** Deve essere scritta nel formato `AAAA-MM-GG`. Se la data odierna supera questa data, l'utente riceverà un messaggio di blocco "Utenza scaduta".
* **AllowedRadios (Abilitazione Radio):** Definisce quali radio l'utente può vedere. Puoi scrivere `all` o `*` per abilitarle tutte, oppure un elenco di radio separate da virgole (es. `Subasio, Mitology`).

#### Come configurare il menu a tendina con spunta (multiselezione):
Per rendere semplicissima la scelta delle radio senza scriverle a mano, puoi creare un menu a tendina dinamico:
1. Seleziona le celle della colonna **E** (da E2 in giù).
2. Clicca su **Dati** > **Convalida dei dati** > **Aggiungi regola**.
3. Sotto *Criteri*, seleziona **Menu a tendina**.
4. Aggiungi le seguenti opzioni individuali:
   * `all`
   * `Subasio`
   * `Divina`
   * `Mitology`
   * `Nostalgia`
   * `Toscana`
   * `Italia`
   * `RDS`
   * `RTL1025`
5. Clicca su **Fine**.

**Come funziona il trigger onEdit multiscelta:**
Grazie allo script inserito in Apps Script, quando cliccherai sul menu a tendina in Google Sheets:
* Selezionando una radio (es. `Mitology`), questa verrà aggiunta alla cella.
* Selezionandola di nuovo (es. clicchi ancora su `Mitology`), verrà rimossa dalla cella (come togliere una spunta).
* Se selezioni `all`, la cella si imposterà su `all` sbloccando tutto.

---

## 2. Inserimento del codice Backend (Google Apps Script)

1. Nel tuo foglio Google, clicca nel menu in alto su **Estensioni** > **Apps Script**.
2. Cancella l'eventuale codice vuoto presente nell'editor.
3. Apri il file localizzato nella cartella del progetto: [google_apps_script.js](file:///c:/Users/Jonny/Desktop/REPORT%20CANZONI%20RADIO/google_apps_script.js), seleziona tutto il codice, copialo e incollalo nell'editor di Apps Script.
4. Clicca sull'icona del floppy disk in alto per salvare il progetto.
5. Fai clic sul pulsante blu **Nuovo deployment** (in alto a destra) > seleziona **Applicazione web**.
6. Configura le opzioni come segue:
   * **Descrizione:** *Classifica backend*
   * **Esegui come:** **Tu** (la tua email di Google)
   * **Chi ha accesso:** **Chiunque** *(è sicuro, l'accesso ai dati è blindato e controllato dalle password definite nella scheda Users).*
7. Clicca su **Esegui deployment**.
8. Se richiesto, clicca su **Autorizza accesso** e fornisci le autorizzazioni al tuo account Google (se esce una schermata di avviso, clicca su *Avanzate* > *Apri applicazione (non sicura)*).
9. Una volta completato, copia l'**URL dell'applicazione web** fornito (avrà una forma simile a `https://script.google.com/macros/s/XXXXXX/exec`).

### Collegare il sito all'URL di Apps Script
Apri il file [genera_html.py](file:///c:/Users/Jonny/Desktop/REPORT%20CANZONI%20RADIO/genera_html.py) e sostituisci il valore alla riga 12 con l'URL che hai appena copiato:
```python
# Sostituisci questo valore con il tuo link
APPS_SCRIPT_URL = "https://script.google.com/macros/s/XXXXXX/exec"
```
*Rigenera il sito eseguendo `aggiorna_tutto.py` o `genera_html.py` dal terminale. Da questo momento il sito HTML utilizzerà la login online!*

---

## 3. Abilitare le API Google Cloud (per il caricamento da Python)

Per fare in modo che il computer di casa aggiorni automaticamente il foglio Google ogni giorno con i dati del web scraping, dobbiamo creare le credenziali API:

1. Vai su [Google Cloud Console](https://console.cloud.google.com/) ed esegui l'accesso.
2. Crea un nuovo progetto (es. *Classifiche Radio*).
3. Nel menu di ricerca in alto, cerca **Google Sheets API** e clicca su **Abilita**.
4. Cerca **Google Drive API** e clicca su **Abilita**.
5. Vai nella sezione **API e servizi** > **Credenziali** (nel menu a sinistra).
6. Clicca in alto su **+ Crea credenziali** > seleziona **Account di servizio**.
7. Inserisci un nome (es. *python-uploader*) e clicca su *Crea e continua* e poi *Fine*.
8. Nella tabella degli account di servizio appena creati, clicca sulla matita o sull'indirizzo email dell'account per modificarlo.
9. Vai nella scheda **Chiavi** in alto > clicca su **Aggiungi chiave** > **Crea nuova chiave** > seleziona il formato **JSON**.
10. Verrà scaricato sul tuo computer un file JSON. Rinomina questo file esattamente in **`google_credentials.json`** e spostalo dentro la cartella del tuo progetto: `C:\Users\Jonny\Desktop\REPORT CANZONI RADIO\`.

### Ultimo passaggio fondamentale:
Apri il file `google_credentials.json` appena scaricato con un editor di testo, trova l'indirizzo email all'interno della voce `"client_email"` (avrà una forma tipo `python-uploader@progetto-id.iam.gserviceaccount.com`).
Copia questo indirizzo email, vai sul tuo **Foglio Google online** su Drive, clicca in alto a destra su **Condividi** e aggiungi questo indirizzo email con i permessi di **Editor** (togliendo la spunta a "Invia notifica").

---

## 4. Installazione Librerie Python sul Computer

Per consentire a Python di connettersi a Sheets, apri il terminale sul tuo PC ed esegui:
```cmd
pip install gspread oauth2client
```

Ora tutto è pronto! Quando eseguirai `aggiorna_tutto.py`:
1. Python scaricherà gli override dal foglio Google.
2. Eseguirà lo scraping.
3. Caricherà le classifiche aggiornate su Google Sheets.
4. Rigenererà il file HTML pronto per essere caricato online su GitHub Pages o Vercel.
