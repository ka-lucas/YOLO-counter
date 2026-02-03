(() => {
  const URLS = window.VIDEO_AO_VIVO_URLS || {};
  
  // Estados
  let selectedCamera = null;
  let lineYNorm = 0.5;
  let isPaused = false;
  let statusTimer = null;
  let lastEventId = 0;

  // Elementos DOM
  const cameraSelection = document.getElementById('cameraSelection');
  const lineSetup = document.getElementById('lineSetup');
  const countingActive = document.getElementById('countingActive');
  const cameraSelect = document.getElementById('cameraSelect');
  const btnSelectCamera = document.getElementById('btnSelectCamera');
  const btnStartCount = document.getElementById('btnStartCount');
  const btnPause = document.getElementById('btn-pause');
  const btnStop = document.getElementById('btn-stop');
  const snapshotImage = document.getElementById('snapshotImage');
  const lineOverlay = document.getElementById('lineOverlay');
  const countLine = document.getElementById('countLine');
  const logListEl = document.getElementById('logList');
  const liveStatus = document.getElementById('liveStatus');

  // Helpers
  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : null;
  }

  async function fetchJSON(url, options = {}) {
    const res = await fetch(url, options);
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
    return data;
  }

  function fmtTime(tsSeconds) {
    const d = new Date(tsSeconds * 1000);
    return d.toLocaleTimeString("pt-BR", { hour12: false });
  }

  function addLogItem(ev) {
    if (!logListEl) return;
    const isIn = ev.kind === "IN";
    const item = document.createElement("div");
    item.className = "log-item";
    item.innerHTML = `
      <span class="time">${fmtTime(ev.ts)}</span>
      <span class="text">Animal detectado - ${isIn ? "Entrada" : "Saída"}</span>
      <span class="delta ${isIn ? "plus" : "minus"}">${isIn ? "+1" : "-1"}</span>
    `;
    logListEl.prepend(item);
    while (logListEl.children.length > 30) {
      logListEl.removeChild(logListEl.lastChild);
    }
  }

  // Etapa 1: Seleção de câmera
  cameraSelect.addEventListener('change', (e) => {
    btnSelectCamera.disabled = !e.target.value;
    selectedCamera = e.target.value;
  });

  btnSelectCamera.addEventListener('click', async () => {
    if (!selectedCamera) return;
    
    // Carregar snapshot da câmera selecionada
    snapshotImage.src = `${URLS.snapshot}?camera_id=${selectedCamera}`;
    
    // Mostrar etapa 2
    cameraSelection.style.display = 'none';
    lineSetup.style.display = 'block';
    
    const cameraName = cameraSelect.options[cameraSelect.selectedIndex].text;
    document.getElementById('cameraName').textContent = cameraName;
  });

  // Etapa 2: Configuração da linha
  function setupLineInteraction() {
    if (!lineOverlay) return;

    const updateLine = (clientY) => {
      const rect = lineOverlay.getBoundingClientRect();
      const y = clientY - rect.top;
      lineYNorm = Math.max(0, Math.min(1, y / rect.height));
      countLine.style.top = `${lineYNorm * 100}%`;
    };

    lineOverlay.addEventListener('click', (e) => updateLine(e.clientY));
    
    let dragging = false;
    lineOverlay.addEventListener('mousedown', () => dragging = true);
    window.addEventListener('mouseup', () => dragging = false);
    window.addEventListener('mousemove', (e) => {
      if (dragging) updateLine(e.clientY);
    });
  }

  btnStartCount.addEventListener('click', async () => {
    try {
      // Enviar linha para backend
      await fetchJSON(URLS.line, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ line_y_norm: lineYNorm })
      });

      // Iniciar contagem com camera_id
      await fetchJSON(`${URLS.start}?camera_id=${selectedCamera}`);

      // Mostrar etapa 3
      lineSetup.style.display = 'none';
      countingActive.style.display = 'block';
      liveStatus.style.display = 'inline-block';
      
      const cameraName = cameraSelect.options[cameraSelect.selectedIndex].text;
      document.getElementById('cameraNameActive').textContent = cameraName;

      // Iniciar polling
      startStatusPolling();
    } catch (e) {
      alert('Erro ao iniciar contagem: ' + e.message);
    }
  });

  // Etapa 3: Contagem ativa
  async function refreshStatus() {
    try {
      const data = await fetchJSON(URLS.status);
      document.getElementById('countIn').textContent = data.in ?? 0;
      document.getElementById('countOut').textContent = data.out ?? 0;
      document.getElementById('countBalance').textContent = (data.in ?? 0) - (data.out ?? 0);
      isPaused = !!data.paused;
      btnPause.textContent = isPaused ? '▶ Retomar' : '⏸ Pausar';
    } catch (e) {}
  }

  async function refreshEvents() {
    try {
      const data = await fetchJSON(`${URLS.events}?after=${lastEventId}`);
      for (const ev of (data.events || [])) {
        addLogItem(ev);
        lastEventId = Math.max(lastEventId, ev.id);
      }
    } catch (e) {}
  }

  function startStatusPolling() {
    if (statusTimer) clearInterval(statusTimer);
    statusTimer = setInterval(async () => {
      await refreshStatus();
      await refreshEvents();
    }, 700);
    refreshStatus();
    refreshEvents();
  }

  function stopStatusPolling() {
    if (statusTimer) clearInterval(statusTimer);
    statusTimer = null;
  }

  btnPause.addEventListener('click', async () => {
    try {
      if (isPaused) {
        await fetchJSON(URLS.resume);
      } else {
        await fetchJSON(URLS.pause);
      }
      await refreshStatus();
    } catch (e) {
      alert('Erro: ' + e.message);
    }
  });

  btnStop.addEventListener('click', async () => {
    try {
      await fetchJSON(URLS.stop);
      stopStatusPolling();
      
      // Voltar para seleção
      countingActive.style.display = 'none';
      cameraSelection.style.display = 'block';
      liveStatus.style.display = 'none';
      
      // Limpar
      document.getElementById('countIn').textContent = '0';
      document.getElementById('countOut').textContent = '0';
      document.getElementById('countBalance').textContent = '0';
      logListEl.innerHTML = '';
      lastEventId = 0;
    } catch (e) {
      alert('Erro ao parar: ' + e.message);
    }
  });

  // Init
  setupLineInteraction();
})();
