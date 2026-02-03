/* static/video_ao_vivo/js/index.js
 *
 * Responsabilidades:
 * 1) Iniciar/pausar/retomar/parar o processamento (APIs Django)
 * 2) Exibir stream MJPEG no <img id="liveStream"> (ou suportar <video> se existir)
 * 3) Poll do status para atualizar IN/OUT
 * 4) Overlay para linha de contagem:
 *    - Clique/arraste para posicionar linha
 *    - Converte coordenada do clique para y normalizado (0..1) respeitando object-fit: contain
 *    - Envia para o backend em /api/line/
 */

(() => {
  const URLS = window.VIDEO_AO_VIVO_URLS || {};

  // ===== DOM =====
  const imgStream = document.getElementById("liveStream"); // MJPEG
  const videoEl = document.getElementById("liveVideo"); // opcional (se você usar <video>)
  const btnPlay = document.getElementById("btn-play");
  const btnReload = document.getElementById("btn-reload");
  const countInEl = document.getElementById("countIn");
  const countOutEl = document.getElementById("countOut");
  const logListEl = document.getElementById("logList") || document.querySelector(".log-list");
  let lastEventId = 0;


  // Overlay (passo 6). Se não existir no HTML, criamos por JS.
  let canvasEl = document.getElementById("videoCanvas") || document.querySelector(".video-canvas");
  let overlayEl = document.getElementById("lineOverlay");
  let lineEl = document.getElementById("countLine");

  // ===== STATE =====
  let isPaused = false;
  let statusTimer = null;
  let isDragging = false;

  // meta do vídeo (frame real)
  let videoMeta = { width: 0, height: 0, fps: 0 };
  let lastYNorm = 0.5;

  // rate limit envio de linha
  let lastSendTs = 0;
  let pendingSend = null;

  // ===== Helpers =====
  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  function cacheBust(url) {
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}t=${Date.now()}`;
  }
  function fmtTime(tsSeconds) {
  const d = new Date(tsSeconds * 1000);
  return d.toLocaleTimeString("pt-BR", { hour12: false });
}
  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : null;
  }

  async function fetchJSON(url, options = {}) {
    const res = await fetch(url, options);
    const ct = res.headers.get("content-type") || "";
    const data = ct.includes("application/json") ? await res.json() : null;
    if (!res.ok) {
      const msg = data?.error || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return data;
  }

  function ensureOverlay() {
    if (!canvasEl) return;

    // Se o container não tem position relative, garante por JS (não substitui seu CSS, só ajuda)
    const style = window.getComputedStyle(canvasEl);
    if (style.position === "static") {
      canvasEl.style.position = "relative";
    }

    if (!overlayEl) {
      overlayEl = document.createElement("div");
      overlayEl.id = "lineOverlay";
      overlayEl.className = "line-overlay";
      // overlay ocupa tudo
      overlayEl.style.position = "absolute";
      overlayEl.style.inset = "0";
      overlayEl.style.cursor = "crosshair";
      // deixa clicar/arrastar
      overlayEl.style.userSelect = "none";
      overlayEl.style.touchAction = "none";
      canvasEl.appendChild(overlayEl);
    }

    if (!lineEl) {
      lineEl = document.createElement("div");
      lineEl.id = "countLine";
      lineEl.className = "count-line";
      lineEl.style.position = "absolute";
      lineEl.style.left = "0";
      lineEl.style.right = "0";
      lineEl.style.height = "3px";
      lineEl.style.top = "50%";
      lineEl.style.background = "rgba(0,255,0,.85)";
      lineEl.style.boxShadow = "0 0 0 2px rgba(0,0,0,.35)";
      overlayEl.appendChild(lineEl);
    }
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

  // ===== Stream =====
  function setStreamSrc() {
    if (!imgStream) return;
    const streamUrl = imgStream.getAttribute("data-stream-url") || URLS.stream;
    if (!streamUrl) return;
    imgStream.src = cacheBust(streamUrl);
  }

  function clearStreamSrc() {
    if (!imgStream) return;
    imgStream.removeAttribute("src");
  }

  // ===== Video meta =====
  async function loadVideoMeta() {
    // 1) tenta API do backend
    const metaUrl = URLS.meta || "/video-ao-vivo/api/meta/";
    try {
      const data = await fetchJSON(metaUrl);
      if (data?.ok && data.width && data.height) {
        videoMeta = { width: data.width, height: data.height, fps: data.fps || 0 };
        return;
      }
    } catch (e) {
      // segue fallback
    }

    // 2) se tiver <video>, tenta ler do elemento (quando carregar metadata)
    if (videoEl) {
      await new Promise((resolve) => {
        if (videoEl.videoWidth && videoEl.videoHeight) return resolve();
        videoEl.addEventListener("loadedmetadata", resolve, { once: true });
      });
      if (videoEl.videoWidth && videoEl.videoHeight) {
        videoMeta = { width: videoEl.videoWidth, height: videoEl.videoHeight, fps: 0 };
        return;
      }
    }

    // 3) fallback seguro
    videoMeta = { width: 1920, height: 1080, fps: 0 };
  }

  // ===== Contain math (mapear clique → frame) =====
  function getContainRect() {
    if (!canvasEl) return { x: 0, y: 0, w: 0, h: 0, scale: 1 };

    const rect = canvasEl.getBoundingClientRect();
    const cw = rect.width;
    const ch = rect.height;

    const vw = videoMeta.width || 1920;
    const vh = videoMeta.height || 1080;

    const scale = Math.min(cw / vw, ch / vh);
    const drawnW = vw * scale;
    const drawnH = vh * scale;
    const offsetX = (cw - drawnW) / 2;
    const offsetY = (ch - drawnH) / 2;

    return { x: offsetX, y: offsetY, w: drawnW, h: drawnH, scale, cw, ch };
  }

  function clientYToNorm(clientY) {
    if (!canvasEl) return 0.5;

    const rect = canvasEl.getBoundingClientRect();
    const localY = clientY - rect.top;

    const contain = getContainRect();
    const yInDrawn = localY - contain.y;
    const yClamped = Math.max(0, Math.min(contain.h, yInDrawn));
    const yInFrame = yClamped / contain.scale;
    const yNorm = yInFrame / (videoMeta.height || 1080);

    return Math.max(0, Math.min(1, yNorm));
  }

  function setLineVisual(yNorm) {
    if (!lineEl || !canvasEl) return;

    lastYNorm = yNorm;

    const contain = getContainRect();
    const yInDrawn = (yNorm * (videoMeta.height || 1080)) * contain.scale;
    const topPx = contain.y + yInDrawn;

    lineEl.style.top = `${topPx}px`;
  }

  async function sendLineToBackend(yNorm) {
    const lineUrl = URLS.line || "/video-ao-vivo/api/line/";
    const csrftoken = getCookie("csrftoken");

    const body = JSON.stringify({ line_y_norm: yNorm });

    await fetchJSON(lineUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrftoken ? { "X-CSRFToken": csrftoken } : {}),
      },
      body,
    });
  }

  function scheduleSendLine(yNorm) {
    // rate limit simples (no máximo 10 envios/seg)
    const now = Date.now();
    const minInterval = 100;

    // atualiza visual sempre
    setLineVisual(yNorm);

    if (now - lastSendTs >= minInterval) {
      lastSendTs = now;
      sendLineToBackend(yNorm).catch((e) => console.error("Falha ao enviar linha:", e));
      return;
    }

    // se já tem envio pendente, substitui pelo mais recente
    if (pendingSend) clearTimeout(pendingSend);

    pendingSend = setTimeout(() => {
      lastSendTs = Date.now();
      pendingSend = null;
      sendLineToBackend(lastYNorm).catch((e) => console.error("Falha ao enviar linha:", e));
    }, minInterval);
  }

  // ===== Status poll =====
  async function refreshStatus() {
    if (!URLS.status) return;
    try {
      const data = await fetchJSON(URLS.status);
      if (countInEl) countInEl.textContent = String(data.in ?? 0);
      if (countOutEl) countOutEl.textContent = String(data.out ?? 0);

      // mantém coerente com backend
      isPaused = !!data.paused;

      if (btnPlay) {
        btnPlay.textContent = isPaused ? "▶" : "⏸";
        btnPlay.title = isPaused ? "Retomar" : "Pausar";
      }
    } catch (e) {
      // Se falhar, não spamma console
    }
  }

  async function refreshEvents() {
    if (!URLS.events) {
      console.warn("URLS.events não definido");
      return;
    }
    if (!logListEl) {
      console.warn("logListEl não encontrado no DOM");
      return;
    }

    const data = await fetchJSON(`${URLS.events}?after=${lastEventId}`);
    for (const ev of (data.events || [])) {
      addLogItem(ev);
      lastEventId = Math.max(lastEventId, ev.id);
    }
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

  // ===== Controls (start/pause/resume/stop) =====
  async function callStart() {
    if (!URLS.start) return;
    await fetchJSON(URLS.start);
  }

  async function callPause() {
    if (!URLS.pause) return;
    await fetchJSON(URLS.pause);
  }

  async function callResume() {
    if (!URLS.resume) return;
    await fetchJSON(URLS.resume);
  }

  async function callStop() {
    if (!URLS.stop) return;
    await fetchJSON(URLS.stop);
  }

  async function handleTogglePause() {
    try {
      if (isPaused) {
        await callResume();
        isPaused = false;
      } else {
        await callPause();
        isPaused = true;
      }
      await refreshStatus();
    } catch (e) {
      console.error(e);
    }
  }

  async function handleReload() {
    try {
      // Reinicia processamento e stream
      await callStop().catch(() => {});
      clearStreamSrc();
      await sleep(150);
      await callStart();
      setStreamSrc();
      await refreshStatus();
    } catch (e) {
      console.error(e);
    }
  }

  // ===== Overlay events =====
  function bindOverlayEvents() {
    if (!overlayEl) return;

    overlayEl.addEventListener("mousedown", (e) => {
      isDragging = true;
      const yNorm = clientYToNorm(e.clientY);
      scheduleSendLine(yNorm);
    });

    window.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      const yNorm = clientYToNorm(e.clientY);
      scheduleSendLine(yNorm);
    });

    window.addEventListener("mouseup", () => {
      if (!isDragging) return;
      isDragging = false;
      // envio final “certeiro”
      scheduleSendLine(lastYNorm);
    });

    // Clique simples (sem arrastar)
    overlayEl.addEventListener("click", (e) => {
      const yNorm = clientYToNorm(e.clientY);
      scheduleSendLine(yNorm);
    });

    window.addEventListener("resize", () => {
      setLineVisual(lastYNorm);
    });
  }

  // ===== Init =====
  async function init() {
    ensureOverlay();

    // 1) meta
    await loadVideoMeta();

    // 2) linha default (visual + backend)
    setLineVisual(lastYNorm);
    // tenta persistir no backend sem quebrar caso endpoint não exista ainda
    if (URLS.line || true) {
      sendLineToBackend(lastYNorm).catch(() => {});
    }

    // 3) iniciar processamento e stream (se for MJPEG)
    //    (se você estiver usando <video> direto, isso não atrapalha)
    if (URLS.start) {
      callStart().catch(() => {});
    }
    if (imgStream) {
      setStreamSrc();
    }

    // 4) bind controls
    if (btnPlay) btnPlay.addEventListener("click", handleTogglePause);
    if (btnReload) btnReload.addEventListener("click", handleReload);

    // 5) bind overlay
    bindOverlayEvents();

    // 6) status
    startStatusPolling();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
