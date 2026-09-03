import os

base_dir = r"c:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
py_path = os.path.join(base_dir, "genera_html.py")

with open(py_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update css row-3 grid-template-columns
old_css_row3 = "  grid-template-columns: 1.15fr 1fr 1fr 1fr auto !important;"
new_css_row3 = "  grid-template-columns: 1.15fr 1.35fr 1fr auto !important;"
content = content.replace(old_css_row3, new_css_row3)

old_css_row3_tablet = "    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;"
new_css_row3_tablet = "    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;"
content = content.replace(old_css_row3_tablet, new_css_row3_tablet)

# 2. Add css open rules right before </style>
old_style_end = "</style>\n</head>"
new_style_end = """  .date-panel.open {{ display: block !important; }}
  .hour-panel.open {{ display: block !important; }}
</style>
</head>"""
content = content.replace(old_style_end, new_style_end)

# 3. Update HTML markup for Data and Orario dropdowns
old_html_data_orario = """    <!-- Data Section -->
    <div class="filter-section data-section">
      <span class="filter-label">DATA</span>
      <div class="select-wrapper">
        <span class="select-icon" style="color: var(--red);">📅</span>
        <select id="date-select" class="styled-select text-red" onchange="onDateSelectChange(this.value)">
          <option value="30">30 giorni</option>
          <option value="7">7 giorni</option>
          <option value="90">90 giorni</option>
          <option value="all">Tutto</option>
        </select>
      </div>
    </div>

    <!-- Orario Section -->
    <div class="filter-section orario-section">
      <span class="filter-label">ORARIO</span>
      <div class="select-wrapper">
        <span class="select-icon">🕒</span>
        <select id="hour-select" class="styled-select" onchange="selectHourPreset(this.value)">
          <option value="all">Tutto</option>
          <option value="mattina">Mattina</option>
          <option value="pomeriggio">Pomeriggio</option>
          <option value="sera">Sera</option>
          <option value="notte">Notte</option>
        </select>
      </div>
    </div>"""

new_html_data_orario = """    <!-- Data Section -->
    <div class="filter-section data-section">
      <span class="filter-label">DATA</span>
      <div class="date-filter-wrap" style="position: relative; width: 100%;">
        <div class="select-wrapper">
          <span class="select-icon" style="color: var(--red);">📅</span>
          <select id="date-select" class="styled-select text-red" onchange="onDateSelectChange(this.value)">
            <option value="30">30 giorni</option>
            <option value="7">7 giorni</option>
            <option value="90">90 giorni</option>
            <option value="all">Tutto</option>
            <option value="custom">Scegli dal calendario...</option>
          </select>
        </div>
        <div class="date-panel" id="date-panel" style="display:none; position:absolute; top:calc(100% + 6px); left:0; z-index:200; background:#fff; border:1.5px solid var(--rc-border); border-radius:12px; box-shadow:var(--rc-shadow); padding:14px; min-width:260px;">
          <div class="cal-shortcuts" style="display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px;">
            <button class="cal-shortcut-btn" id="preset-all"       onclick="selectPreset('all')" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Tutte</button>
            <button class="cal-shortcut-btn" id="preset-7"         onclick="selectPreset(7)" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">7 gg</button>
            <button class="cal-shortcut-btn" id="preset-30"        onclick="selectPreset(30)" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Mese</button>
          </div>
          <div class="cal-nav" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <button class="cal-nav-btn" onclick="calShiftMonth(-1)" style="background: none; border: none; font-size: 18px; cursor: pointer; font-weight: bold;">&#8249;</button>
            <span class="cal-month-label" id="cal-month-label" style="font-weight: 800; font-size: 14px;"></span>
            <button class="cal-nav-btn" onclick="calShiftMonth(1)" style="background: none; border: none; font-size: 18px; cursor: pointer; font-weight: bold;">&#8250;</button>
          </div>
          <div class="cal-grid" id="cal-grid" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center; font-size: 12px;">
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Lu</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Ma</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Me</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Gi</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Ve</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Sa</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Do</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Orario Section -->
    <div class="filter-section orario-section">
      <span class="filter-label">ORARIO</span>
      <div class="hour-filter-wrap" style="position: relative; width: 100%;">
        <div class="select-wrapper">
          <span class="select-icon">🕒</span>
          <select id="hour-select" class="styled-select" onchange="onHourSelectChange(this.value)">
            <option value="all">Tutto</option>
            <option value="mattina">Mattina</option>
            <option value="pomeriggio">Pomeriggio</option>
            <option value="sera">Sera</option>
            <option value="notte">Notte</option>
            <option value="custom">Scegli ore...</option>
          </select>
        </div>
        <div class="hour-panel" id="hour-panel" style="display:none; position:absolute; top:calc(100% + 6px); left:0; z-index:200; background:#fff; border:1.5px solid var(--rc-border); border-radius:12px; box-shadow:var(--rc-shadow); padding:14px; min-width:320px;">
          <div class="cal-shortcuts" style="display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px;">
            <button class="cal-shortcut-btn" id="hour-preset-all"   onclick="selectHourPreset('all')" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Tutto</button>
            <button class="cal-shortcut-btn" id="hour-preset-none"  onclick="selectHourPreset('none')" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Nessuno</button>
          </div>
          <div class="hour-grid" id="hour-grid" style="display:grid; grid-template-columns:repeat(6,1fr); gap:6px; margin-top:10px;"></div>
        </div>
      </div>
    </div>"""

content = content.replace(old_html_data_orario, new_html_data_orario)

# 4. Update Row 3 HTML: replace top-group & delete positions-group
old_html_row3 = """  <!-- Riga 3: Controlli Avanzati -->
  <div class="filter-row row-3">
    <div class="adv-group toggle-group">
      <span class="filter-label">POSIZIONE ORIGINALE <span class="info-tooltip" title="Mantieni la posizione originale del brano in classifica anche quando filtri per nome">ⓘ</span></span>
      <label class="toggle-wrap">
        <input type="checkbox" id="keep-rank-checkbox" onchange="applyFilters()">
        <span class="toggle-switch"></span>
      </label>
    </div>

    <div class="adv-group top-group">
      <span class="filter-label">MOSTRA PRIME <span class="info-tooltip" title="Limita il numero di posizioni mostrate">🔗</span></span>
      <div style="display: flex; flex-direction: column; gap: 4px; align-items: flex-start;">
        <select id="top-select" class="styled-select compact-select" onchange="applyFilters()">
          <option value="50">50</option>
          <option value="100">100</option>
          <option value="250">250</option>
          <option value="all">Tutte</option>
        </select>
        <button class="cal-shortcut-btn" id="btn-show-all-positions" onclick="showAllPositions()" style="padding: 2px 10px; font-size: 11px; margin-top: 2px; align-self: center;">Tutte</button>
      </div>
    </div>

    <div class="adv-group positions-group">
      <span class="filter-label">POSIZIONI</span>
      <select id="positions-select" class="styled-select compact-select" onchange="applyFilters()">
        <option value="all">Tutte</option>
        <option value="up">In salita</option>
        <option value="down">In discesa</option>
        <option value="new">Nuove</option>
      </select>
    </div>

    <div class="adv-group min-plays-group">
      <span class="filter-label">MIN PASSAGGI</span>
      <input type="number" class="filter-input compact-input" id="min-plays-input" min="1" placeholder="1" oninput="applyFilters()">
    </div>

    <div class="results-count-wrap">
      <span class="results-count" id="results-count"></span>
    </div>
  </div>"""

new_html_row3 = """  <!-- Riga 3: Controlli Avanzati -->
  <div class="filter-row row-3">
    <div class="adv-group toggle-group">
      <span class="filter-label">POSIZIONE ORIGINALE <span class="info-tooltip" title="Mantieni la posizione originale del brano in classifica anche quando filtri per nome">ⓘ</span></span>
      <label class="toggle-wrap">
        <input type="checkbox" id="keep-rank-checkbox" onchange="applyFilters()">
        <span class="toggle-switch"></span>
      </label>
    </div>

    <div class="adv-group top-group" style="flex-direction: row !important; align-items: center !important; gap: 8px !important; justify-content: center !important;">
      <span style="font-size: 13px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: .09em; white-space: nowrap;">PRIME</span>
      <input type="number" id="top-input" min="1" value="50" class="compact-input" style="width: 80px !important; text-align: center !important; height: 38px !important; padding: 0 !important; font-weight: 800 !important;" oninput="applyFilters()">
      <span style="font-size: 13px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: .09em; white-space: nowrap;">POSIZIONI</span>
    </div>

    <div class="adv-group min-plays-group">
      <span class="filter-label">MIN PASSAGGI</span>
      <input type="number" class="filter-input compact-input" id="min-plays-input" min="1" placeholder="1" oninput="applyFilters()">
    </div>

    <div class="results-count-wrap">
      <span class="results-count" id="results-count"></span>
    </div>
  </div>"""

content = content.replace(old_html_row3, new_html_row3)

# 5. globalSelectedRadios with localStorage loading
old_glob_sel = "let globalSelectedRadios = new Set(RADIO_KEYS);"
new_glob_sel = """let globalSelectedRadios = (() => {{
  const saved = localStorage.getItem('radio_charts_global_selected');
  if (saved) {{
    try {{
      const arr = JSON.parse(saved);
      if (Array.isArray(arr) && arr.length > 0) {{
        return new Set(arr.filter(k => RADIO_KEYS.includes(k)));
      }}
    }} catch(e) {{}}
  }}
  return new Set(RADIO_KEYS);
}})();"""
content = content.replace(old_glob_sel, new_glob_sel)

# 6. onDateSelectChange & onHourSelectChange definitions
old_ondateselect = """function onDateSelectChange(val) {{
  if (val === 'all') {{
    selectPreset('all');
  }} else {{
    selectPreset(parseInt(val));
  }}
}}"""

new_ondateselect = """function onDateSelectChange(val) {{
  if (val === 'custom') {{
    buildDatePanel();
    document.getElementById('date-panel')?.classList.add('open');
  }} else {{
    document.getElementById('date-panel')?.classList.remove('open');
    if (val === 'all') {{
      selectPreset('all');
    }} else {{
      selectPreset(parseInt(val));
    }}
  }}
}}

function onHourSelectChange(val) {{
  if (val === 'custom') {{
    buildHourPanel();
    document.getElementById('hour-panel')?.classList.add('open');
  }} else {{
    document.getElementById('hour-panel')?.classList.remove('open');
    selectHourPreset(val);
  }}
}}"""
content = content.replace(old_ondateselect, new_ondateselect)

# 7. update selectHourPreset to update select element + toggleHour, onCalDayClick to set custom value
old_hour_preset = """function selectHourPreset(preset) {{
  if (preset === 'all') {{
    selectedHours = null;
  }} else if (preset === 'mattina') {{
    selectedHours = new Set([6, 7, 8, 9, 10, 11]);
  }} else if (preset === 'pomeriggio') {{
    selectedHours = new Set([12, 13, 14, 15, 16, 17]);
  }} else if (preset === 'sera') {{
    selectedHours = new Set([18, 19, 20, 21, 22, 23]);
  }} else if (preset === 'notte') {{
    selectedHours = new Set([0, 1, 2, 3, 4, 5]);
  }}
  applyFilters();
}}"""

new_hour_preset = """function selectHourPreset(preset) {{
  if (preset === 'all') {{
    selectedHours = null;
  }} else if (preset === 'none') {{
    selectedHours = new Set();
  }} else if (preset === 'mattina') {{
    selectedHours = new Set([6, 7, 8, 9, 10, 11]);
  }} else if (preset === 'pomeriggio') {{
    selectedHours = new Set([12, 13, 14, 15, 16, 17]);
  }} else if (preset === 'sera') {{
    selectedHours = new Set([18, 19, 20, 21, 22, 23]);
  }} else if (preset === 'notte') {{
    selectedHours = new Set([0, 1, 2, 3, 4, 5]);
  }}
  const select = document.getElementById('hour-select');
  if (select) {{
    select.value = preset;
  }}
  applyFilters();
}}"""
content = content.replace(old_hour_preset, new_hour_preset)

old_toggle_hour = """function toggleHour(h) {{
  if (!selectedHours) {{
    selectedHours = new Set();
    for (let i = 0; i < 24; i++) {{
      if (i !== h) selectedHours.add(i);
    }}
  }} else {{
    if (selectedHours.has(h)) {{
      selectedHours.delete(h);
    }} else {{
      selectedHours.add(h);
    }}
    if (selectedHours.size === 24) {{
      selectedHours = null;
    }}
  }}
  updateHourUI();
  applyFilters();
}}"""

new_toggle_hour = """function toggleHour(h) {{
  if (!selectedHours) {{
    selectedHours = new Set();
    for (let i = 0; i < 24; i++) {{
      if (i !== h) selectedHours.add(i);
    }}
  }} else {{
    if (selectedHours.has(h)) {{
      selectedHours.delete(h);
    }} else {{
      selectedHours.add(h);
    }}
    if (selectedHours.size === 24) {{
      selectedHours = null;
    }}
  }}
  const hourSelect = document.getElementById('hour-select');
  if (hourSelect) {{
    hourSelect.value = selectedHours ? 'custom' : 'all';
  }}
  updateHourUI();
  applyFilters();
}}"""
content = content.replace(old_toggle_hour, new_toggle_hour)

old_cal_day_click = """function onCalDayClick(ddmm) {{
  if (!selectedDates) {{
    // Era "tutte" → seleziona solo questo giorno
    selectedDates = new Set([ddmm]);
  }} else {{
    if (selectedDates.has(ddmm)) selectedDates.delete(ddmm);
    else selectedDates.add(ddmm);
    // Se sono di nuovo tutte → torna a null
    const dataKeys = [...allDatesSet];
    if (dataKeys.every(k => selectedDates.has(k))) selectedDates = null;
  }}
  updateDateBadge();
  applyFilters();
  buildCalendar();
}}"""

new_cal_day_click = """function onCalDayClick(ddmm) {{
  if (!selectedDates) {{
    // Era "tutte" → seleziona solo questo giorno
    selectedDates = new Set([ddmm]);
  }} else {{
    if (selectedDates.has(ddmm)) selectedDates.delete(ddmm);
    else selectedDates.add(ddmm);
    // Se sono di nuovo tutte → torna a null
    const dataKeys = [...allDatesSet];
    if (dataKeys.every(k => selectedDates.has(k))) selectedDates = null;
  }}
  const dateSelect = document.getElementById('date-select');
  if (dateSelect) {{
    dateSelect.value = selectedDates ? 'custom' : 'all';
  }}
  updateDateBadge();
  applyFilters();
  buildCalendar();
}}"""
content = content.replace(old_cal_day_click, new_cal_day_click)

# 8. Click outside panel close handler (update selector class checks)
old_click_close = """// Chiudi panel cliccando fuori
document.addEventListener('click', e => {{
  const wrap = document.getElementById('date-filter-btn')?.closest('.date-filter-wrap');
  if(wrap && !wrap.contains(e.target)) {{
    document.getElementById('date-panel')?.classList.remove('open');
  }}
  const wrapHour = document.getElementById('hour-filter-btn')?.closest('.hour-filter-wrap');
  if(wrapHour && !wrapHour.contains(e.target)) {{
    document.getElementById('hour-panel')?.classList.remove('open');
  }}
}});"""

new_click_close = """// Chiudi panel cliccando fuori
document.addEventListener('click', e => {{
  const wrap = e.target.closest('.date-filter-wrap');
  if (!wrap) {{
    document.getElementById('date-panel')?.classList.remove('open');
  }}
  const wrapHour = e.target.closest('.hour-filter-wrap');
  if (!wrapHour) {{
    document.getElementById('hour-panel')?.classList.remove('open');
  }}
}});"""
content = content.replace(old_click_close, new_click_close)

# 9. showAllPositions function
old_show_all = """function showAllPositions() {{
  const select = document.getElementById('top-select');
  if (select) {{
    select.value = 'all';
    applyFilters();
  }}
}}"""

new_show_all = """function showAllPositions() {{
  const input = document.getElementById('top-input');
  if (input) {{
    input.value = '';
    applyFilters();
  }}
}}"""
content = content.replace(old_show_all, new_show_all)

# 10. applyFilters function (change top-select to top-input, remove posFilter checking)
old_apply_filters_start = """function applyFilters() {{
  const q = document.getElementById('search-input').value.toLowerCase().trim();
  
  const topSelect = document.getElementById('top-select');
  const topVal = topSelect ? topSelect.value : '50';
  const currentLimit = topVal === 'all' ? Infinity : parseInt(topVal);
  
  const btnAll = document.getElementById('btn-show-all-positions');
  if (btnAll) {{
    btnAll.classList.toggle('active', topVal === 'all');
  }}
  
  const minPlaysVal = document.getElementById('min-plays-input').value.trim();
  const minPlays = (minPlaysVal && parseInt(minPlaysVal) > 0) ? parseInt(minPlaysVal) : 1;

  const posFilterSelect = document.getElementById('positions-select');
  const posFilter = posFilterSelect ? posFilterSelect.value : 'all';"""

new_apply_filters_start = """function applyFilters() {{
  const q = document.getElementById('search-input').value.toLowerCase().trim();
  
  const topInput = document.getElementById('top-input');
  const topVal = topInput ? topInput.value.trim() : '50';
  const currentLimit = (topVal && parseInt(topVal) > 0) ? parseInt(topVal) : Infinity;
  
  const btnAll = document.getElementById('btn-show-all-positions');
  if (btnAll) {{
    btnAll.classList.toggle('active', !topVal);
  }}
  
  const minPlaysVal = document.getElementById('min-plays-input').value.trim();
  const minPlays = (minPlaysVal && parseInt(minPlaysVal) > 0) ? parseInt(minPlaysVal) : 1;"""

content = content.replace(old_apply_filters_start, new_apply_filters_start)

# Remove posFilter filtering block inside applyFilters
old_filter_block = """    // Posizioni filter: 'up', 'down', 'new'
    if (posFilter === 'up') {{
      if (s.rank <= s._periodRank) return false;
    }} else if (posFilter === 'down') {{
      if (s.rank >= s._periodRank) return false;
    }} else if (posFilter === 'new') {{
      if (!isSongNew(s)) return false;
    }}"""
content = content.replace(old_filter_block, "")

# 11. Global radios select functions
old_toggle_fns = """function toggleGlobalRadio(radioKey) {{
  const wrap = document.getElementById(`cb-${{radioKey}}`);
  const checkbox = wrap.querySelector('input[type="checkbox"]');
  
  if (checkbox.checked) {{
    globalSelectedRadios.add(radioKey);
    wrap.classList.add('checked');
  }} else {{
    globalSelectedRadios.delete(radioKey);
    wrap.classList.remove('checked');
  }}
  
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}

function selectAllGlobal() {{
  const isAllowed = (k) => {{
    if (userAllowedRadios === 'all' || userAllowedRadios === '*') return true;
    if (Array.isArray(userAllowedRadios)) {{
      return userAllowedRadios.map(r => r.toLowerCase().trim()).includes(k.toLowerCase().trim());
    }}
    return false;
  }};

  RADIO_KEYS.forEach(radioKey => {{
    if (!isAllowed(radioKey)) return;
    
    globalSelectedRadios.add(radioKey);
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    if (wrap) {{
      wrap.classList.add('checked');
      wrap.querySelector('input[type="checkbox"]').checked = true;
    }}
  }});
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}

function selectNoneGlobal() {{
  globalSelectedRadios.clear();
  RADIO_KEYS.forEach(radioKey => {{
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    if (wrap) {{
      wrap.classList.remove('checked');
      wrap.querySelector('input[type="checkbox"]').checked = false;
    }}
  }});
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}"""

new_toggle_fns = """function saveGlobalRadiosState() {{
  localStorage.setItem('radio_charts_global_selected', JSON.stringify(Array.from(globalSelectedRadios)));
}}

function applyGlobalCheckboxesState() {{
  RADIO_KEYS.forEach(k => {{
    const wrap = document.getElementById('cb-' + k);
    if (wrap) {{
      const checkbox = wrap.querySelector('input[type="checkbox"]');
      const isChecked = globalSelectedRadios.has(k);
      if (checkbox) checkbox.checked = isChecked;
      if (isChecked) {{
        wrap.classList.add('checked');
      }} else {{
        wrap.classList.remove('checked');
      }}
    }}
  }});
}}

function toggleGlobalRadio(radioKey) {{
  const wrap = document.getElementById(`cb-${{radioKey}}`);
  const checkbox = wrap.querySelector('input[type="checkbox"]');
  
  if (checkbox.checked) {{
    globalSelectedRadios.add(radioKey);
    wrap.classList.add('checked');
  }} else {{
    globalSelectedRadios.delete(radioKey);
    wrap.classList.remove('checked');
  }}
  saveGlobalRadiosState();
  
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}

function selectAllGlobal() {{
  const isAllowed = (k) => {{
    if (userAllowedRadios === 'all' || userAllowedRadios === '*') return true;
    if (Array.isArray(userAllowedRadios)) {{
      return userAllowedRadios.map(r => r.toLowerCase().trim()).includes(k.toLowerCase().trim());
    }}
    return false;
  }};

  RADIO_KEYS.forEach(radioKey => {{
    if (!isAllowed(radioKey)) return;
    
    globalSelectedRadios.add(radioKey);
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    if (wrap) {{
      wrap.classList.add('checked');
      wrap.querySelector('input[type="checkbox"]').checked = true;
    }}
  }});
  saveGlobalRadiosState();
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}

function selectNoneGlobal() {{
  globalSelectedRadios.clear();
  RADIO_KEYS.forEach(radioKey => {{
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    if (wrap) {{
      wrap.classList.remove('checked');
      wrap.querySelector('input[type="checkbox"]').checked = false;
    }}
  }});
  saveGlobalRadiosState();
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}"""
content = content.replace(old_toggle_fns, new_toggle_fns)

# 12. Update initApp and fetchChartsData references
old_fetch_data_init1 = """      if (isInitialLoad) {{
        document.getElementById('top-select').value = '50';
        switchRadio(currentRadio);
        selectPreset(30);
        isInitialLoad = false;
      }} else {{
        switchRadio(currentRadio);
      }}"""

new_fetch_data_init1 = """      if (isInitialLoad) {{
        document.getElementById('top-input').value = '50';
        switchRadio(currentRadio);
        selectPreset(30);
        isInitialLoad = false;
      }} else {{
        switchRadio(currentRadio);
      }}"""
content = content.replace(old_fetch_data_init1, new_fetch_data_init1)

old_fetch_data_init2 = """    if (isInitialLoad) {{
      document.getElementById('top-select').value = '50';
      switchRadio(currentRadio);
      selectPreset(30);
      isInitialLoad = false;
    }} else {{
      switchRadio(currentRadio);
    }}"""

new_fetch_data_init2 = """    if (isInitialLoad) {{
      document.getElementById('top-input').value = '50';
      switchRadio(currentRadio);
      selectPreset(30);
      isInitialLoad = false;
    }} else {{
      switchRadio(currentRadio);
    }}"""
content = content.replace(old_fetch_data_init2, new_fetch_data_init2)

old_init_app_call = """    applyAllowedRadiosVisibility();
    if (user && pass) {{"""
new_init_app_call = """    applyAllowedRadiosVisibility();
    applyGlobalCheckboxesState();
    if (user && pass) {{"""
content = content.replace(old_init_app_call, new_init_app_call)

old_init_app_call2 = """    updateEditPermissions();
    applyAllowedRadiosVisibility();
    if (isInitialLoad) {{"""
new_init_app_call2 = """    updateEditPermissions();
    applyAllowedRadiosVisibility();
    applyGlobalCheckboxesState();
    if (isInitialLoad) {{"""
content = content.replace(old_init_app_call2, new_init_app_call2)


with open(py_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Restyle modifications V3 applied successfully!")
