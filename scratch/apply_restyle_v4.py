import os

base_dir = r"c:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
py_path = os.path.join(base_dir, "genera_html.py")

with open(py_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update .radio-tab CSS to prevent shrinking on desktop horizontal scroll
old_radio_tab_css = """.radio-tab {{
  position: relative;
  padding: 18px 24px 19px !important;
  color: rgba(255,255,255,.56) !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  letter-spacing: .045em !important;
  border-bottom: none !important;
  transition: color .18s ease, background .18s ease !important;
}}"""

new_radio_tab_css = """.radio-tab {{
  position: relative;
  padding: 18px 24px 19px !important;
  color: rgba(255,255,255,.56) !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  letter-spacing: .045em !important;
  border-bottom: none !important;
  transition: color .18s ease, background .18s ease !important;
  flex-shrink: 0 !important;
}}"""
content = content.replace(old_radio_tab_css, new_radio_tab_css)

# 2. Update desktop row-1 grid CSS to allow three columns
old_row1_css = """.row-1 {{
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 210px !important;
  align-items: stretch !important;
  gap: 18px !important;
}}"""

new_row1_css = """.row-1 {{
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 180px 160px !important;
  align-items: stretch !important;
  gap: 18px !important;
}}"""
content = content.replace(old_row1_css, new_row1_css)

# 3. Update mobile CSS: increase grid-template-columns for pos badge, and clear pos-cell width
old_mobile_tbody_tr = """  tbody tr {{
    display: grid !important;
    grid-template-columns: 58px minmax(0, 1fr) auto !important;
    grid-template-areas:
      "pos song plays"
      "pos date date" !important;
    gap: 8px 12px !important;
    padding: 14px !important;
    border: 1px solid rgba(226,232,240,.94) !important;
    border-radius: 19px !important;
    background: #fff !important;
    box-shadow: 0 8px 22px rgba(15,23,42,.065) !important;
  }}"""

new_mobile_tbody_tr = """  tbody tr {{
    display: grid !important;
    grid-template-columns: 68px minmax(0, 1fr) auto !important;
    grid-template-areas:
      "pos song plays"
      "pos date date" !important;
    gap: 8px 12px !important;
    padding: 14px !important;
    border: 1px solid rgba(226,232,240,.94) !important;
    border-radius: 19px !important;
    background: #fff !important;
    box-shadow: 0 8px 22px rgba(15,23,42,.065) !important;
  }}"""
content = content.replace(old_mobile_tbody_tr, new_mobile_tbody_tr)

old_mobile_pos_cell = """  .pos-cell {{
    grid-area: pos !important;
    display: flex !important;
    align-items: flex-start !important;
    justify-content: center !important;
  }}"""

new_mobile_pos_cell = """  .pos-cell {{
    grid-area: pos !important;
    display: flex !important;
    align-items: flex-start !important;
    justify-content: center !important;
    width: auto !important;
    padding: 0 !important;
  }}"""
content = content.replace(old_mobile_pos_cell, new_mobile_pos_cell)

# 4. Replace Row 1 HTML in genera_html.py to add the new Confronto button
old_row1_html = """  <!-- Riga 1: Cerca + Esporta -->
  <div class="filter-row row-1">
    <div class="search-box">
      <input type="text" id="search-input" placeholder="Cerca artista o titolo…" oninput="applyFilters()">
      <span class="icon">🔍</span>
    </div>
    <button class="export-btn" id="export-btn" onclick="exportToCSV()" title="Esporta classifica filtrata in CSV" style="display: inline-flex; align-items: center; gap: 6px; background: #0d9488; color: #fff; border: none; border-radius: 8px; padding: 10px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);">
      <svg class="export-icon" viewBox="0 0 24 24" style="width: 16px; height: 16px; fill: currentColor;"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/></svg>
      Esporta CSV
    </button>
  </div>"""

new_row1_html = """  <!-- Riga 1: Cerca + Esporta + Confronto -->
  <div class="filter-row row-1">
    <div class="search-box">
      <input type="text" id="search-input" placeholder="Cerca artista o titolo…" oninput="applyFilters()">
      <span class="icon">🔍</span>
    </div>
    <button class="compare-btn" id="compare-btn" onclick="openCompareModal()" title="Confronta ed evidenzia brani mancanti" style="display: inline-flex; align-items: center; justify-content: center; gap: 6px; background: #4f46e5; color: #fff; border: none; border-radius: 8px; padding: 10px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);">
      📊 Confronto Playlist
    </button>
    <button class="export-btn" id="export-btn" onclick="exportToCSV()" title="Esporta classifica filtrata in CSV" style="display: inline-flex; align-items: center; justify-content: center; gap: 6px; background: #0d9488; color: #fff; border: none; border-radius: 8px; padding: 10px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);">
      <svg class="export-icon" viewBox="0 0 24 24" style="width: 16px; height: 16px; fill: currentColor;"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/></svg>
      Esporta CSV
    </button>
  </div>"""
content = content.replace(old_row1_html, new_row1_html)

# 5. Append comparison modal layout
old_modal_end = """        <div class="edit-modal-actions">
          <button class="edit-btn edit-btn-cancel" id="edit-btn-cancel" onclick="closeEditYearModalDirect()">Annulla</button>
          <button class="edit-btn edit-btn-save" id="edit-year-save-btn" onclick="saveYearOverride()">
            <span class="btn-text">Salva</span>
            <span class="btn-spinner" style="display:none">Salvataggio... ⏳</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>"""

new_modal_end = """        <div class="edit-modal-actions">
          <button class="edit-btn edit-btn-cancel" id="edit-btn-cancel" onclick="closeEditYearModalDirect()">Annulla</button>
          <button class="edit-btn edit-btn-save" id="edit-year-save-btn" onclick="saveYearOverride()">
            <span class="btn-text">Salva</span>
            <span class="btn-spinner" style="display:none">Salvataggio... ⏳</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- COMPARISON MODAL -->
<div class="modal-overlay" id="compare-modal-overlay" onclick="closeCompareModal(event)">
  <div class="modal edit-modal" id="compare-modal-box" style="max-width: 600px !important;">
    <div class="modal-header">
      <div class="modal-title">
        <div class="edit-modal-title-text">Confronto Playlist</div>
        <div class="edit-modal-subtitle">Trova canzoni non presenti in una determinata radio</div>
      </div>
      <button class="modal-close" onclick="closeCompareModalDirect()">✕</button>
    </div>
    <div class="modal-body edit-modal-body" style="display:flex; flex-direction:column; gap:16px;">
      
      <div>
        <label for="compare-my-radio" class="edit-input-label">La mia radio (Destinazione)</label>
        <div class="select-wrapper">
          <span class="select-icon" style="color: var(--rc-teal);">📻</span>
          <select id="compare-my-radio" class="styled-select" style="padding-left: 44px !important;">
            <option value="subasio">Radio Subasio</option>
            <option value="divina">Radio Divina</option>
            <option value="mitology">Radio Mitology</option>
            <option value="nostalgia">Nostalgia Toscana</option>
            <option value="toscana">Radio Toscana</option>
            <option value="italia">Radio Italia</option>
            <option value="rds">RDS</option>
            <option value="rtl1025">RTL 102.5</option>
            <option value="birikina">Radio Birikina</option>
            <option value="bruno">Radio Bruno</option>
            <option value="kisskiss">Radio Kiss Kiss</option>
            <option value="m2o">Radio m2o</option>
            <option value="propostaaosta">Proposta Aosta</option>
            <option value="capital">Radio Capital</option>
          </select>
        </div>
      </div>

      <div>
        <label class="edit-input-label">Mando l'export (Seleziona un'altra radio o incolla/carica elenco)</label>
        <div style="display:flex; flex-direction:column; gap:10px;">
          <!-- Opzione 1: Altra radio -->
          <div class="select-wrapper">
            <span class="select-icon" style="color: var(--rc-red);">📻</span>
            <select id="compare-source-radio" class="styled-select" style="padding-left: 44px !important;" onchange="document.getElementById('compare-source-text').value = ''; document.getElementById('compare-source-file').value = '';">
              <option value="">-- Seleziona un'altra radio del database --</option>
              <option value="subasio">Radio Subasio</option>
              <option value="divina">Radio Divina</option>
              <option value="mitology">Radio Mitology</option>
              <option value="nostalgia">Nostalgia Toscana</option>
              <option value="toscana">Radio Toscana</option>
              <option value="italia">Radio Italia</option>
              <option value="rds">RDS</option>
              <option value="rtl1025">RTL 102.5</option>
              <option value="birikina">Radio Birikina</option>
              <option value="bruno">Radio Bruno</option>
              <option value="kisskiss">Radio Kiss Kiss</option>
              <option value="m2o">Radio m2o</option>
              <option value="propostaaosta">Proposta Aosta</option>
              <option value="capital">Radio Capital</option>
            </select>
          </div>

          <div style="text-align: center; font-weight: 700; color: var(--rc-muted); font-size: 12px; margin: 4px 0;">OPPURE INCOLLA/CARICA</div>

          <!-- Opzione 2: Carica File o Incolla testo -->
          <textarea id="compare-source-text" placeholder="Incolla qui l'elenco dei brani (es. Artista - Titolo, uno per riga, o CSV)..." class="edit-year-input-field" style="height:120px; font-family:monospace; font-size:12px; padding:10px; resize:vertical;" oninput="document.getElementById('compare-source-radio').value = '';"></textarea>
          
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:12px; font-weight:700; color:var(--rc-muted);">Carica file CSV:</span>
            <input type="file" id="compare-source-file" accept=".csv,.txt" style="font-size:12px;" onchange="document.getElementById('compare-source-radio').value = '';">
          </div>
        </div>
      </div>

      <div class="edit-modal-actions" style="margin-top: 10px;">
        <button class="edit-btn edit-btn-cancel" onclick="closeCompareModalDirect()">Chiudi</button>
        <button class="edit-btn edit-btn-save" onclick="runPlaylistComparison()" style="background: linear-gradient(145deg, var(--rc-teal), var(--rc-teal-dark)) !important;">
          <span class="btn-text">Esegui Confronto</span>
        </button>
      </div>

      <!-- Risultati del confronto -->
      <div id="compare-results-area" style="display:none; border-top:1px solid var(--rc-border); padding-top:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div style="font-weight:900; color:var(--rc-text); font-size:14px;" id="compare-results-title"></div>
          <button class="cal-shortcut-btn" id="compare-export-csv" onclick="exportCompareResultsToCSV()" style="padding:6px 12px; font-size:11px; background:#0d9488; color:#fff; font-weight:700; border-radius:6px; cursor:pointer; display:inline-block;">Esporta Risultati</button>
        </div>
        <div id="compare-results-table-wrap" style="max-height: 250px; overflow-y: auto; border: 1px solid var(--rc-border); border-radius: 8px; background: #fafafa;">
          <table style="width:100%; border-collapse:collapse; font-size:12px; box-shadow:none; border:none; border-radius:0;">
            <thead style="position:sticky; top:0; background: #071124; z-index:10;">
              <tr>
                <th style="padding:8px 10px; color:#fff; text-align:left; font-size:11px; height:auto; border-right:none;">Artista</th>
                <th style="padding:8px 10px; color:#fff; text-align:left; font-size:11px; height:auto; border-right:none;">Titolo</th>
              </tr>
            </thead>
            <tbody id="compare-results-tbody">
              <!-- Righe generate js -->
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</div>"""
content = content.replace(old_modal_end, new_modal_end)

# 6. Append Javascript logic for the comparison feature at the end of script
old_script_end = """</script>
</body>
</html>"""

new_script_end = """let lastCompareMissingSongs = [];

function openCompareModal() {{
  document.getElementById('compare-modal-overlay').classList.add('open');
}}

function closeCompareModal(e) {{
  if (e.target.id === 'compare-modal-overlay') {{
    closeCompareModalDirect();
  }}
}}

function closeCompareModalDirect() {{
  document.getElementById('compare-modal-overlay').classList.remove('open');
}}

async function runPlaylistComparison() {{
  const myRadioKey = document.getElementById('compare-my-radio').value;
  const sourceRadioKey = document.getElementById('compare-source-radio').value;
  const sourceText = document.getElementById('compare-source-text').value.trim();
  const fileInput = document.getElementById('compare-source-file');
  
  let sourceSongs = [];
  
  if (sourceRadioKey) {{
    // Confronta con un'altra radio del database
    sourceSongs = RAW[sourceRadioKey].songs;
  }} else if (fileInput.files.length > 0) {{
    // Carica da file
    const file = fileInput.files[0];
    const text = await new Promise((resolve) => {{
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.readAsText(file);
    }});
    sourceSongs = parseExportSongs(text);
  }} else if (sourceText) {{
    // Carica da testo incollato
    sourceSongs = parseExportSongs(sourceText);
  }} else {{
    alert("Seleziona una radio di confronto, carica un file CSV o incolla l'elenco dei brani!");
    return;
  }}

  if (sourceSongs.length === 0) {{
    alert("Nessun brano trovato nella sorgente di confronto.");
    return;
  }}

  // Costruisci il Set delle canzoni presenti in "La mia radio" (usando chiave normalizzata)
  const myRadioSongs = RAW[myRadioKey].songs;
  const myRadioSet = new Set(myRadioSongs.map(s => getNormKey(s.artist, s.title)));

  // Trova le canzoni mancanti
  const missingSongs = [];
  const addedKeys = new Set(); // per evitare duplicati nei risultati

  sourceSongs.forEach(s => {{
    const key = getNormKey(s.artist, s.title);
    if (!myRadioSet.has(key) && !addedKeys.has(key)) {{
      addedKeys.add(key);
      missingSongs.push({{ artist: s.artist, title: s.title }});
    }}
  }});

  // Salva i risultati per l'esportazione
  lastCompareMissingSongs = missingSongs;

  // Ordina alfabeticamente per artista
  missingSongs.sort((a,b) => a.artist.localeCompare(b.artist));

  // Renderizza la tabella dei risultati
  const tbody = document.getElementById('compare-results-tbody');
  tbody.innerHTML = '';
  
  if (missingSongs.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="2" style="text-align:center; padding:20px; font-weight:600; color:var(--rc-muted);">Tutte le canzoni dell\\'export sono già presenti nella tua radio! 🎉</td></tr>';
    document.getElementById('compare-export-csv').style.display = 'none';
  }} else {{
    missingSongs.forEach(s => {{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td style="padding:8px 10px; border-bottom:1px solid var(--rc-border); font-weight:700;">${{s.artist}}</td><td style="padding:8px 10px; border-bottom:1px solid var(--rc-border);">${{s.title}}</td>`;
      tbody.appendChild(tr);
    }});
    document.getElementById('compare-export-csv').style.display = 'inline-block';
  }}

  document.getElementById('compare-results-title').textContent = `${{missingSongs.length}} brani mancanti`;
  document.getElementById('compare-results-area').style.display = 'block';
}}

function parseExportSongs(text) {{
  const songs = [];
  const lines = text.split('\\n');
  lines.forEach(line => {{
    line = line.trim();
    if (!line) return;
    
    // Prova a splittare per csv / tab / semicolon
    let artist = '', title = '';
    if (line.includes(';')) {{
      const parts = line.split(';');
      if (parts.length >= 2) {{
        artist = parts[0].trim();
        title = parts[1].trim();
      }}
    }} else if (line.includes(',')) {{
      const parts = line.split(',');
      if (parts.length >= 2) {{
        artist = parts[0].trim();
        title = parts[1].trim();
      }}
    }} else if (line.includes(' - ')) {{
      const parts = line.split(' - ');
      artist = parts[0].trim();
      title = parts[1].trim();
    }} else if (line.includes(' – ')) {{
      const parts = line.split(' – ');
      artist = parts[0].trim();
      title = parts[1].trim();
    }} else {{
      // Riga singola, considerala come titolo
      title = line;
    }}
    
    // Rimuovi virgolette se presenti
    artist = artist.replace(/^["']|["']$/g, '').trim();
    title = title.replace(/^["']|["']$/g, '').trim();
    
    if (title) {{
      songs.push({{ artist: artist || 'Sconosciuto', title: title }});
    }}
  }});
  return songs;
}}

function exportCompareResultsToCSV() {{
  if (lastCompareMissingSongs.length === 0) return;
  const headers = ["Artista", "Titolo"];
  const rows = lastCompareMissingSongs.map(s => `"${{s.artist.replace(/"/g, '""')}}","${{s.title.replace(/"/g, '""')}}"`).join('\\n');
  const csvContent = "\\ufeff" + [headers.join(','), rows].join('\\n');
  const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  
  const myRadioKey = document.getElementById('compare-my-radio').value;
  const filename = `Brani_Mancanti_${{myRadioKey.toUpperCase()}}_${{new Date().toISOString().slice(0,10)}}.csv`;
  
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}}
</script>
</body>
</html>"""
content = content.replace(old_script_end, new_script_end)

with open(py_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Restyle modifications V4 (horizontal scroll, mobile overlaps, and playlist comparison modal) applied successfully!")
