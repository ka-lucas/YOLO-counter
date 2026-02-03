const video = document.getElementById('video');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');
const baterPontoBtn = document.getElementById('baterPontoBtn');
const statusBadge = document.getElementById('statusBadge');

let cameraStream = null;
let cameraLigada = false;
let isRunning = false;
let detectionInterval = null;
let detectedFaces = [];
let maxConfidence = 0;
let faceApiLoaded = false;

// LISTENERS
document.getElementById("abrirCameraBtn").addEventListener("click", abrirCamera);
document.getElementById("fecharCameraBtn").addEventListener("click", fecharCamera);
document.getElementById("baterPontoBtn").addEventListener("click", baterPonto);

// ABRIR CÂMERA
function abrirCamera() {
    document.getElementById("cameraBox").style.display = "block";
    document.getElementById("cameraButtons").style.display = "flex";
    document.getElementById("abrirCameraBtn").style.display = "none";

    iniciarCamera();
}

// FECHAR CÂMERA
function fecharCamera() {
    document.getElementById("cameraBox").style.display = "none";
    document.getElementById("cameraButtons").style.display = "none";
    document.getElementById("abrirCameraBtn").style.display = "block";

    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        cameraLigada = false;
        isRunning = false;
    }

    stopDetection();
}

// INICIAR CÂMERA
function iniciarCamera() {
    navigator.mediaDevices.getUserMedia({
        video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user'
        }
    })
    .then(stream => {
        cameraStream = stream;
        video.srcObject = stream;
        cameraLigada = true;
        isRunning = true;

        // ✅ BOTÃO SEMPRE HABILITADO (independente da face-api)
        baterPontoBtn.disabled = false;

        statusBadge.className = 'status-badge status-no-face';
        statusBadge.innerHTML = '<i class="fas fa-hourglass-split me-1"></i> Iniciando...';

        video.onloadedmetadata = async () => {
            overlay.width = video.videoWidth;
            overlay.height = video.videoHeight;
            overlay.style.width = '100%';
            overlay.style.height = '100%';

            // Tenta carregar face-api, mas não bloqueia se falhar
            await loadFaceApiJs();

            if (faceApiLoaded) {
                startDetection();
            } else {
                // Se face-api falhar, apenas mostra mensagem mas mantém botão ativo
                statusBadge.className = 'status-badge status-detected';
                statusBadge.innerHTML = '<i class="fas fa-camera me-1"></i> Câmera pronta';
                showToast('info', 'Câmera ativa', 'Detecção facial não disponível, mas você pode registrar o ponto.');
            }
        };
    })
    .catch(err => {
        console.error('Erro ao acessar câmera:', err);
        showToast('error', 'Erro', 'Erro ao acessar a câmera: ' + err.message);
        statusBadge.className = 'status-badge status-no-face';
        statusBadge.innerHTML = '<i class="fas fa-times-circle me-1"></i> Erro na câmera';
    });
}

// CARREGAR MODELOS (NÃO BLOQUEIA O SISTEMA SE FALHAR)
async function loadFaceApiJs() {
    try {
        statusBadge.className = 'status-badge status-no-face';
        statusBadge.innerHTML = '<i class="fas fa-hourglass-split me-1"></i> Carregando detecção...';

        await faceapi.nets.tinyFaceDetector.loadFromUri('https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.12/model');
        console.log('✅ face-api.js carregado com sucesso');

        faceApiLoaded = true;
        showToast('success', 'Sistema pronto', 'Detecção facial carregada!');

    } catch (error) {
        console.error('❌ Erro ao carregar face-api:', error);
        faceApiLoaded = false;

        // Não bloqueia - apenas avisa
        statusBadge.className = 'status-badge status-detected';
        statusBadge.innerHTML = '<i class="fas fa-camera me-1"></i> Câmera pronta (sem detecção)';
    }
}

// DETECTAR ROSTOS (só roda se face-api carregou)
async function detectFaces() {
    if (!isRunning || !cameraLigada || !faceApiLoaded || video.readyState !== 4) return;

    try {
        const detections = await faceapi.detectAllFaces(
            video,
            new faceapi.TinyFaceDetectorOptions({
                inputSize: 224,
                scoreThreshold: 0.5
            })
        );

        detectedFaces = detections.map(d => ({
            boundingBox: {
                x: d.box.x,
                y: d.box.y,
                width: d.box.width,
                height: d.box.height
            },
            confidence: d.score
        }));

        ctx.clearRect(0, 0, overlay.width, overlay.height);

        const scaleX = overlay.width / video.videoWidth;
        const scaleY = overlay.height / video.videoHeight;

        maxConfidence = 0;

        detectedFaces.forEach((face, index) => {
            const box = face.boundingBox;
            const confidence = face.confidence || 0.9;

            maxConfidence = Math.max(maxConfidence, confidence);

            const x = box.x * scaleX;
            const y = box.y * scaleY;
            const width = box.width * scaleX;
            const height = box.height * scaleY;

            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, width, height);

            const cornerSize = 20;
            ctx.lineWidth = 4;

            // Cantos
            ctx.beginPath();
            ctx.moveTo(x, y + cornerSize);
            ctx.lineTo(x, y);
            ctx.lineTo(x + cornerSize, y);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(x + width - cornerSize, y);
            ctx.lineTo(x + width, y);
            ctx.lineTo(x + width, y + cornerSize);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(x, y + height - cornerSize);
            ctx.lineTo(x, y + height);
            ctx.lineTo(x + cornerSize, y + height);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(x + width - cornerSize, y + height);
            ctx.lineTo(x + width, y + height);
            ctx.lineTo(x + width, y + height - cornerSize);
            ctx.stroke();
        });

        const hasFace = detectedFaces.length > 0;
        updateDetectionStatus(hasFace, detectedFaces.length);

    } catch (err) {
        console.error('Erro na detecção:', err);
    }
}

// ATUALIZAR STATUS
function updateDetectionStatus(hasFace, count) {
    if (hasFace) {
        statusBadge.className = 'status-badge status-detected';
        statusBadge.innerHTML = '<i class="fas fa-check-circle me-1"></i> Rosto Detectado';
    } else {
        statusBadge.className = 'status-badge status-no-face';
        statusBadge.innerHTML = '<i class="fas fa-search me-1"></i> Procurando rosto...';
    }
    // Botão sempre habilitado
    baterPontoBtn.disabled = false;
}

// INICIAR DETECÇÃO
function startDetection() {
    if (!faceApiLoaded) return;
    isRunning = true;
    detectionInterval = setInterval(detectFaces, 100);
}

// PARAR DETECÇÃO
function stopDetection() {
    isRunning = false;
    if (detectionInterval) {
        clearInterval(detectionInterval);
        detectionInterval = null;
    }
    ctx.clearRect(0, 0, overlay.width, overlay.height);
}

// BATER PONTO (FUNCIONA SEMPRE, COM OU SEM DETECÇÃO)
async function baterPonto() {
    if (!cameraLigada) {
        showToast('error', 'Câmera não ativa', 'Ative a câmera antes de registrar.');
        return;
    }

    const btn = baterPontoBtn;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Verificando identidade...';

    // Mostra badge de processamento
    statusBadge.className = 'status-badge status-no-face';
    statusBadge.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processando...';

    try {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const canvasCtx = canvas.getContext('2d');

        // Desenha a imagem SEM espelhar
        canvasCtx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Desenha os retângulos se houver faces detectadas (SEM TEXTO)
        if (faceApiLoaded && detectedFaces.length > 0) {
            detectedFaces.forEach((face, index) => {
                const box = face.boundingBox;

                // Desenha o retângulo
                canvasCtx.strokeStyle = '#00ff00';
                canvasCtx.lineWidth = 3;
                canvasCtx.strokeRect(box.x, box.y, box.width, box.height);

                const cornerSize = 20;
                canvasCtx.lineWidth = 4;

                // Cantos superiores
                canvasCtx.beginPath();
                canvasCtx.moveTo(box.x, box.y + cornerSize);
                canvasCtx.lineTo(box.x, box.y);
                canvasCtx.lineTo(box.x + cornerSize, box.y);
                canvasCtx.stroke();

                canvasCtx.beginPath();
                canvasCtx.moveTo(box.x + box.width - cornerSize, box.y);
                canvasCtx.lineTo(box.x + box.width, box.y);
                canvasCtx.lineTo(box.x + box.width, box.y + cornerSize);
                canvasCtx.stroke();

                // Cantos inferiores
                canvasCtx.beginPath();
                canvasCtx.moveTo(box.x, box.y + box.height - cornerSize);
                canvasCtx.lineTo(box.x, box.y + box.height);
                canvasCtx.lineTo(box.x + cornerSize, box.y + box.height);
                canvasCtx.stroke();

                canvasCtx.beginPath();
                canvasCtx.moveTo(box.x + box.width - cornerSize, box.y + box.height);
                canvasCtx.lineTo(box.x + box.width, box.y + box.height);
                canvasCtx.lineTo(box.x + box.width, box.y + box.height - cornerSize);
                canvasCtx.stroke();
            });
        }

        canvas.toBlob(async (blob) => {
            try {
                const formData = new FormData();
                formData.append("image", blob, "ponto_face.jpg");

                const response = await fetch("/bater_ponto/", {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-CSRFToken": getCookie('csrftoken')
                    }
                });

                const data = await response.json();

                if (data.erro) {
                    showToast('error', 'Erro', data.erro);
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-check me-1"></i>Confirmar';

                    // Restaura badge para procurar rosto
                    if (faceApiLoaded) {
                        statusBadge.className = 'status-badge status-no-face';
                        statusBadge.innerHTML = '<i class="fas fa-search me-1"></i> Procurando rosto...';
                    } else {
                        statusBadge.className = 'status-badge status-detected';
                        statusBadge.innerHTML = '<i class="fas fa-camera me-1"></i> Câmera pronta';
                    }
                } else {
                    const successMsg = `${data.mensagem} registrada com sucesso!`;
                    const detailMsg = data.similarity ?
                        `Confiança: ${data.confidence} | Similaridade: ${data.similarity}` :
                        '';

                    showToast('success', 'Ponto Registrado', `${successMsg}<br><small>${detailMsg}</small>`);
                    setTimeout(() => location.reload(), 2000);
                }

            } catch (err) {
                console.error('Erro ao enviar ponto:', err);
                showToast('error', 'Erro de Conexão', 'Não foi possível conectar ao servidor. Verifique sua conexão.');
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-check me-1"></i>Confirmar';
            }
        }, 'image/jpeg', 0.95);

    } catch (err) {
        console.error('Erro ao bater ponto:', err);
        showToast('error', 'Erro', 'Falha ao processar a imagem.');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check me-1"></i>Confirmar';
    }
}

// CSRF TOKEN
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// DATA ATUAL
function carregarDataAtual() {
    const elemento = document.getElementById("dataAtual");
    if (!elemento) return;

    const agora = new Date();
    const opcoes = { weekday: "long", day: "numeric", month: "long", year: "numeric" };
    const dataFormatada = agora.toLocaleDateString("pt-BR", opcoes);
    elemento.textContent = dataFormatada.charAt(0).toUpperCase() + dataFormatada.slice(1);
}

// TOAST NOTIFICATION
function showToast(type, title, message) {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    const alertType = type === 'success' ? 'success' : type === 'info' ? 'info' : 'danger';
    const toast = document.createElement('div');
    toast.className = `alert alert-${alertType} alert-dismissible fade show`;
    toast.style.minWidth = '300px';
    toast.style.marginBottom = '10px';
    toast.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

window.addEventListener("load", carregarDataAtual);
