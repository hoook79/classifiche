/**
 * Google Apps Script Backend for Radio Charts - V2
 * Incolla questo codice in: Estensioni > Apps Script del tuo foglio Google.
 * Poi clicca su "Nuovo deployment" o "Gestisci deployment" > crea una nuova versione come Applicazione Web.
 */

// Helper per impostare le intestazioni CORS e JSON
function jsonResponse(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

// Gestore delle richieste GET
function doGet(e) {
  try {
    var params = e.parameter;
    var action = params.action;
    var username = params.username;
    var password = params.password;

    if (!action) {
      return jsonResponse({ success: false, error: "Azione mancante." });
    }

    // 1. Verifica Credenziali
    var auth = authenticate(username, password);
    if (!auth.success) {
      return jsonResponse({ success: false, error: auth.error });
    }

    var db = SpreadsheetApp.getActiveSpreadsheet();

    // Azione: login (ritorna solo il successo, ruolo e radio consentite)
    if (action === "login") {
      return jsonResponse({ 
        success: true, 
        username: username, 
        role: auth.role, 
        expiration: auth.expiration,
        allowedRadios: auth.allowedRadios
      });
    }

    // Azione: getData (ritorna tutte le classifiche abilitate e i metadati)
    if (action === "getData") {
      var result = {};
      var sheets = db.getSheets();
      
      // Carica i metadati delle date
      var datesMetadata = {};
      var datesSheet = db.getSheetByName("Dates_Metadata");
      if (datesSheet) {
        var datesData = datesSheet.getDataRange().getValues();
        for (var i = 1; i < datesData.length; i++) {
          var radioKey = datesData[i][0];
          var datesJson = datesData[i][1];
          if (radioKey && datesJson) {
            try {
              datesMetadata[radioKey] = JSON.parse(datesJson);
            } catch (err) {
              datesMetadata[radioKey] = datesJson.split(",");
            }
          }
        }
      }

      // Elenco completo delle radio
      var radioKeys = ["Subasio", "Divina", "Mitology", "Nostalgia", "Toscana", "Italia", "RDS", "RTL1025", "Birikina", "Bruno", "Kisskiss", "M2o", "Propostaaosta"];
      
      for (var k = 0; k < radioKeys.length; k++) {
        var rKey = radioKeys[k];
        
        // Verifica se l'utente è autorizzato a vedere questa radio
        var isAllowed = false;
        if (auth.allowedRadios === "all") {
          isAllowed = true;
        } else {
          for (var j = 0; j < auth.allowedRadios.length; j++) {
            if (auth.allowedRadios[j].toLowerCase().trim() === rKey.toLowerCase()) {
              isAllowed = true;
              break;
            }
          }
        }

        // Se non è autorizzato, non inviare alcun dato per questa radio!
        if (!isAllowed) {
          continue;
        }

        var sheetName = "Data_" + rKey;
        var rSheet = db.getSheetByName(sheetName);
        
        if (!rSheet) {
          result[rKey.toLowerCase()] = { songs: [], dates: datesMetadata[rKey.toLowerCase()] || [] };
          continue;
        }

        var data = rSheet.getDataRange().getValues();
        var songs = [];
        
        // La prima riga contiene le intestazioni: Rank, Artist, Title, Year, RadioDate, Total, Days
        for (var row = 1; row < data.length; row++) {
          var daysObj = {};
          try {
            daysObj = JSON.parse(data[row][6]);
          } catch(err) {
            // Fallback se non è JSON
          }

          songs.push({
            rank: Number(data[row][0]),
            artist: String(data[row][1]),
            title: String(data[row][2]),
            year: String(data[row][3]),
            radioDate: String(data[row][4]),
            total: Number(data[row][5]),
            days: daysObj
          });
        }

        result[rKey.toLowerCase()] = {
          songs: songs,
          dates: datesMetadata[rKey.toLowerCase()] || []
        };
      }

      return jsonResponse({ 
        success: true, 
        data: result, 
        role: auth.role,
        allowedRadios: auth.allowedRadios
      });
    }

    return jsonResponse({ success: false, error: "Azione non riconosciuta." });

  } catch (error) {
    return jsonResponse({ success: false, error: error.toString() });
  }
}

// Gestore delle richieste POST
function doPost(e) {
  try {
    var postData;
    if (e.postData && e.postData.contents) {
      postData = JSON.parse(e.postData.contents);
    } else {
      return jsonResponse({ success: false, error: "Dati POST mancanti." });
    }

    var action = postData.action;
    var username = postData.username;
    var password = postData.password;

    // 1. Verifica Credenziali
    var auth = authenticate(username, password);
    if (!auth.success) {
      return jsonResponse({ success: false, error: auth.error });
    }

    var db = SpreadsheetApp.getActiveSpreadsheet();

    // Azione: saveOverride (richiede ruolo admin)
    if (action === "saveOverride") {
      if (auth.role !== "admin") {
        return jsonResponse({ success: false, error: "Permesso negato. Solo gli amministratori possono modificare i dati." });
      }

      var artist = postData.artist;
      var title = postData.title;
      var year = postData.year || "N/A";
      var radioDate = postData.radioDate || "N/A";

      if (!artist || !title) {
        return jsonResponse({ success: false, error: "Artista e Titolo sono obbligatori." });
      }

      var songKey = artist.trim() + " - " + title.trim();

      // 1. Salva in YearsCache
      var yearsSheet = db.getSheetByName("YearsCache");
      if (!yearsSheet) {
        yearsSheet = db.insertSheet("YearsCache");
        yearsSheet.appendRow(["SongKey", "Year"]);
      }
      updateCacheSheet(yearsSheet, songKey, year);

      // 2. Salva in RadioDatesCache
      var rdSheet = db.getSheetByName("RadioDatesCache");
      if (!rdSheet) {
        rdSheet = db.insertSheet("RadioDatesCache");
        rdSheet.appendRow(["SongKey", "RadioDate"]);
      }
      updateCacheSheet(rdSheet, songKey, radioDate);

      // 3. Aggiorna in tempo reale le schede attive delle radio
      var radioKeys = ["Subasio", "Divina", "Mitology", "Nostalgia", "Toscana", "Italia", "RDS", "RTL1025", "Birikina", "Bruno", "Kisskiss", "M2o", "Propostaaosta"];
      var normalizedTargetKey = normalizeKey(artist, title);

      for (var k = 0; k < radioKeys.length; k++) {
        var sheetName = "Data_" + radioKeys[k];
        var rSheet = db.getSheetByName(sheetName);
        if (!rSheet) continue;

        var dataRange = rSheet.getDataRange();
        var data = dataRange.getValues();

        for (var row = 1; row < data.length; row++) {
          var rowArtist = data[row][1];
          var rowTitle = data[row][2];
          
          if (normalizeKey(rowArtist, rowTitle) === normalizedTargetKey) {
            rSheet.getRange(row + 1, 4).setValue(year);
            rSheet.getRange(row + 1, 5).setValue(radioDate);
          }
        }
      }

      return jsonResponse({ success: true, message: "Modifica salvata con successo e propagata." });
    }

    return jsonResponse({ success: false, error: "Azione POST non riconosciuta." });

  } catch (error) {
    return jsonResponse({ success: false, error: error.toString() });
  }
}

// Funzione di autenticazione interna
function authenticate(username, password) {
  if (!username || !password) {
    return { success: false, error: "Inserisci username e password." };
  }

  var db = SpreadsheetApp.getActiveSpreadsheet();
  var userSheet = db.getSheetByName("Users");
  if (!userSheet) {
    userSheet = db.insertSheet("Users");
    userSheet.appendRow(["Username", "Password", "Role", "ExpirationDate", "AllowedRadios"]);
    userSheet.appendRow(["admin", "admin123", "admin", "2030-12-31", "all"]);
  }

  var data = userSheet.getDataRange().getValues();
  // Colonne: Username, Password, Role, ExpirationDate, AllowedRadios (opzionale)
  for (var i = 1; i < data.length; i++) {
    var u = String(data[i][0]).trim();
    var p = String(data[i][1]).trim();
    var role = String(data[i][2]).trim().toLowerCase();
    var expStr = String(data[i][3]).trim();

    if (u === username.trim() && p === password.trim()) {
      // Verifica scadenza
      var today = new Date();
      today.setHours(0,0,0,0);
      var expDate = new Date(expStr);
      
      if (isNaN(expDate.getTime())) {
        return { success: false, error: "Formato data scadenza non valido sul server." };
      }
      
      if (expDate < today) {
        return { success: false, error: "La tua utenza è scaduta il " + formatDate(expDate) + ". Contatta l'amministratore." };
      }

      // Estrai le radio consentite (5a colonna - indice 4)
      var allowedRadios = "all";
      if (data[i].length > 4 && String(data[i][4]).trim() !== "") {
        var rawAllowed = String(data[i][4]).trim().toLowerCase();
        if (rawAllowed !== "all" && rawAllowed !== "*") {
          allowedRadios = rawAllowed.split(",").map(function(item) {
            return item.trim();
          });
        }
      }

      return { 
        success: true, 
        role: role, 
        expiration: expStr, 
        allowedRadios: allowedRadios 
      };
    }
  }

  return { success: false, error: "Credenziali non valide." };
}

// Funzione di utilità per aggiornare o inserire un record nelle tabelle cache
function updateCacheSheet(sheet, songKey, newValue) {
  var data = sheet.getDataRange().getValues();
  var foundRow = -1;
  
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][0]).trim().toLowerCase() === songKey.toLowerCase()) {
      foundRow = i + 1;
      break;
    }
  }

  if (foundRow !== -1) {
    sheet.getRange(foundRow, 2).setValue(newValue);
  } else {
    sheet.appendRow([songKey, newValue]);
  }
}

// Formatta data GG/MM/AAAA
function formatDate(date) {
  var d = date.getDate();
  var m = date.getMonth() + 1;
  var y = date.getFullYear();
  return (d < 10 ? '0' : '') + d + '/' + (m < 10 ? '0' : '') + m + '/' + y;
}

// Normalizzazione semplificata per confronto stringhe
function normalizeKey(artist, title) {
  var a = String(artist || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  var t = String(title || "").toLowerCase().replace(/[^a-z0-9]/g, "");
  return a + "|" + t;
}

