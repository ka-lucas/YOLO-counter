(() => {
  console.log('JavaScript carregado');
  
  // Estados
  let selectedCamera = null;
  let lineYNorm = 0.5;

  // Elementos DOM
  const cameraSelection = document.getElementById('cameraSelection');
  const lineSetup = document.getElementById('lineSetup');
  const countingActive = document.getElementById('countingActive');
  const cameraSelect = document.getElementById('cameraSelect');
  const animalFilter = document.getElementById('animalFilter');
  const btnSelectCamera = document.getElementById('btnSelectCamera');
  const btnStartCount = document.getElementById('btnStartCount');
  const btnPause = document.getElementById('btn-pause');
  const btnStop = document.getElementById('btn-stop');
  const snapshotImage = document.getElementById('snapshotImage');
  const snapshotVideo = document.getElementById('snapshotVideo');
  const lineOverlay = document.getElementById('lineOverlay');
  const countLine = document.getElementById('countLine');
  const liveStatus = document.getElementById('liveStatus');

  // Verificar se os elementos existem
  if (!cameraSelect || !btnSelectCamera) {
    console.error('Elementos não encontrados');
    return;
  }

  console.log('Elementos encontrados, configurando eventos');

  // Etapa 1: Seleção de câmera
  cameraSelect.addEventListener('change', (e) => {
    const hasValue = e.target.value && e.target.value.trim() !== '';
    btnSelectCamera.disabled = !hasValue;
    selectedCamera = e.target.value;
    console.log('Camera selecionada:', selectedCamera, 'Botão habilitado:', hasValue);
  });

  // Filtrar opções de câmera pelo tipo de animal (detection_class_name)
  if (animalFilter) {
    animalFilter.addEventListener('change', (e) => {
      const filterVal = e.target.value;
      let anyVisible = false;
      for (let i = 0; i < cameraSelect.options.length; i++) {
        const opt = cameraSelect.options[i];
        // manter a primeira opção placeholder visível
        if (!opt.value) {
          opt.style.display = '';
          continue;
        }
        const optAnimal = (opt.getAttribute('data-detection-class') || '').trim();
        if (!filterVal || filterVal === '') {
          opt.style.display = '';
          anyVisible = true;
        } else {
          if (optAnimal === filterVal) {
            opt.style.display = '';
            anyVisible = true;
          } else {
            opt.style.display = 'none';
          }
        }
      }
      // Se o item selecionado for agora invisível, limpar seleção
      const selOpt = cameraSelect.options[cameraSelect.selectedIndex];
      if (selOpt && selOpt.style.display === 'none') {
        cameraSelect.value = '';
        selectedCamera = null;
        btnSelectCamera.disabled = true;
      }
      // Se não há opções visíveis além do placeholder, opcionalmente mostrar mensagem (console por agora)
      if (!anyVisible) console.log('Nenhuma câmera corresponde ao filtro selecionado');
    });
  }

  btnSelectCamera.addEventListener('click', () => {
    if (!selectedCamera) return;
    
    console.log('Avançando para configuração da linha');
    
    // Mostrar etapa 2
    if (cameraSelection) cameraSelection.style.display = 'none';
    if (lineSetup) lineSetup.style.display = 'block';
    
    const selectedOption = cameraSelect.options[cameraSelect.selectedIndex];
    console.log('selectedOption element:', selectedOption);
    console.log('selectedOption attributes:', {
      'data-detection-class': selectedOption.getAttribute('data-detection-class'),
      'dataset.detectionClass': selectedOption.dataset.detectionClass,
      'data-stream-type': selectedOption.getAttribute('data-stream-type'),
      'text': selectedOption.text
    });
    
    // Usar somente detection_class_name associado à câmera
    // Mostrar o NOME da câmera na interface; usar detection_class_name apenas para o form
    const cameraNameText = selectedOption.text || selectedOption.getAttribute('data-name') || 'Câmera';
    const cameraNameEl = document.getElementById('cameraName');
    if (cameraNameEl) {
      cameraNameEl.textContent = cameraNameText;
      console.log('Atualizado cameraName para:', cameraNameText);
    }
    
    // Mostrar imagem/vídeo da câmera
    if (snapshotImage && snapshotVideo) {
      const cameraUrl = cameraSelect.options[cameraSelect.selectedIndex].getAttribute('data-url');
      console.log('URL da câmera:', cameraUrl);
      
      if (cameraUrl && cameraUrl.startsWith('http') && !cameraUrl.startsWith('rtsp')) {
        console.log('Detectada câmera HTTP/MJPEG');
        snapshotImage.src = cameraUrl;
        snapshotImage.style.display = 'block';
        snapshotVideo.style.display = 'none';
      } else if (cameraUrl && cameraUrl.startsWith('rtsp')) {
        console.log('Detectada câmera RTSP, configurando WebRTC...');
        snapshotImage.style.display = 'none';
        snapshotVideo.style.display = 'block';
        setupRTSPWebRTC(cameraUrl, snapshotVideo);
      } else {
        console.log('Câmera sem URL válida, usando placeholder');
        snapshotImage.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkPDom1lcmEgbsOjbyBkaXNwb27DrXZlbDwvdGV4dD48L3N2Zz4=';
        snapshotImage.style.display = 'block';
        snapshotVideo.style.display = 'none';
      }
    }
  });

  // Etapa 2: Configuração da linha
  function setupLineInteraction() {
    if (!lineOverlay || !countLine) return;

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

  if (btnStartCount) {
    btnStartCount.addEventListener('click', async () => {
      console.log('Iniciando contagem com camera:', selectedCamera);
      
      try {
        // Enviar linha para backend
        const URLS = window.VIDEO_AO_VIVO_URLS || {};
        console.log('URLs disponíveis:', URLS);
        
        if (URLS.line) {
          console.log('Enviando posição da linha:', lineYNorm);
          const lineResponse = await fetch(URLS.line, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ line_y_norm: lineYNorm })
          });
          console.log('Resposta da linha:', lineResponse.status);
          const lineData = await lineResponse.json();
          console.log('Dados da linha:', lineData);
        }

        // Iniciar contagem com camera_id
        if (URLS.start) {
          console.log('Iniciando contador com URL:', `${URLS.start}?camera_id=${selectedCamera}`);
          const response = await fetch(`${URLS.start}?camera_id=${selectedCamera}`, {
            method: 'POST'
          });
          
          console.log('Status da resposta:', response.status);
          const responseData = await response.json();
          console.log('Dados da resposta:', responseData);
          
          if (!response.ok) {
            throw new Error(responseData.error || 'Erro ao iniciar');
          }
        }

        console.log('Contador iniciado com sucesso, mudando para tela ativa');
        
        // Mostrar etapa 3
        if (lineSetup) lineSetup.style.display = 'none';
        if (countingActive) countingActive.style.display = 'block';
        if (liveStatus) liveStatus.style.display = 'inline-block';
        
        const selectedOption = cameraSelect.options[cameraSelect.selectedIndex];
        const cameraNameText = selectedOption.text || selectedOption.getAttribute('data-name') || 'Câmera';
        const cameraNameActiveEl = document.getElementById('cameraNameActive');
        if (cameraNameActiveEl) cameraNameActiveEl.textContent = cameraNameText;
        
        // Sempre usar stream MJPEG processado durante contagem
        const liveStreamEl = document.getElementById('liveStream');
        if (liveStreamEl && URLS.stream) {
          console.log('Iniciando stream processado:', URLS.stream);
          liveStreamEl.src = URLS.stream;
          liveStreamEl.onerror = () => console.error('Erro ao carregar stream processado');
          liveStreamEl.onload = () => console.log('Stream processado carregado');
        }

        // Iniciar polling de status
        startStatusPolling();
        
      } catch (error) {
        console.error('Erro completo:', error);
        alert('Erro ao iniciar contagem: ' + error.message);
      }
    });
  }
  
  
  // Função para configurar WebRTC para RTSP
  async function setupRTSPWebRTC(rtspUrl, videoElement) {
    console.log('Iniciando WebRTC para:', rtspUrl);
    try {
      // Verificar se servidor WebRTC está disponível
      const healthCheck = await fetch("http://127.0.0.1:8887/health");
      if (!healthCheck.ok) {
        throw new Error('Servidor WebRTC não está rodando');
      }
      console.log('Servidor WebRTC disponível');
      
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });

      pc.addTransceiver('video', { direction: 'recvonly' });

      pc.ontrack = (event) => {
        console.log('Stream WebRTC recebido');
        videoElement.srcObject = event.streams[0];
      };

      const offer = await pc.createOffer({
        offerToReceiveVideo: true,
        offerToReceiveAudio: false
      });

      await pc.setLocalDescription(offer);
      console.log('Enviando offer para servidor WebRTC...');

      const response = await fetch("http://127.0.0.1:8887/offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          offer: { sdp: offer.sdp, type: offer.type },
          rtsp_url: rtspUrl
        })
      });

      if (response.ok) {
        const data = await response.json();
        await pc.setRemoteDescription(data.answer);
        console.log('WebRTC configurado com sucesso');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erro no servidor WebRTC');
      }
    } catch (error) {
      console.error('Erro WebRTC:', error);
      // Mostrar erro no elemento video
      videoElement.style.display = 'none';
      const img = document.getElementById('snapshotImage');
      if (img) {
        img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI0MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iI2FhYSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+U2Vydmlkb3IgV2ViUlRDPC90ZXh0Pjx0ZXh0IHg9IjUwJSIgeT0iNjAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM4ODgiIHRleHQtYW5jaG9yPSJtaWRkbGUiPmluZGlzcG9u7XZlbDwvdGV4dD48L3N2Zz4=';
        img.style.display = 'block';
      }
    }
  }
  
  // Funções auxiliares
  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : null;
  }
  
  function startStatusPolling() {
    const URLS = window.VIDEO_AO_VIVO_URLS || {};
    
    // Limpar polling anterior se existir
    if (window.statusInterval) {
      clearInterval(window.statusInterval);
    }
    
    window.statusInterval = setInterval(async () => {
      try {
        if (URLS.status) {
          const response = await fetch(URLS.status);
          const data = await response.json();
          
          const countInEl = document.getElementById('countIn');
          const countOutEl = document.getElementById('countOut');
          const countBalanceEl = document.getElementById('countBalance');
          
          if (countInEl) countInEl.textContent = data.in || 0;
          if (countOutEl) countOutEl.textContent = data.out || 0;
          if (countBalanceEl) countBalanceEl.textContent = (data.in || 0) - (data.out || 0);
          
          // Atualizar botão pause/resume
          if (btnPause) {
            if (data.paused) {
              btnPause.textContent = '▶ Retomar';
              btnPause.onclick = async () => {
                try {
                  const response = await fetch(URLS.resume, { method: 'POST' });
                  if (!response.ok) throw new Error('Erro ao retomar');
                  console.log('Contagem retomada');
                } catch (error) {
                  alert('Erro ao retomar: ' + error.message);
                }
              };
            } else {
              btnPause.textContent = '⏸ Pausar';
              btnPause.onclick = async () => {
                try {
                  const response = await fetch(URLS.pause, { method: 'POST' });
                  if (!response.ok) throw new Error('Erro ao pausar');
                  console.log('Contagem pausada');
                } catch (error) {
                  alert('Erro ao pausar: ' + error.message);
                }
              };
            }
          }
        }
      } catch (e) {
        console.error('Erro no polling:', e);
      }
    }, 1000);
  }

  // Etapa 3: Controles
  if (btnPause) {
    btnPause.addEventListener('click', async () => {
      try {
        const URLS = window.VIDEO_AO_VIVO_URLS || {};
        const response = await fetch(URLS.pause, { method: 'POST' });
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Erro ao pausar');
        }
        
        console.log('Contagem pausada');
      } catch (error) {
        alert('Erro ao pausar: ' + error.message);
      }
    });
  }

  if (btnStop) {
    btnStop.addEventListener('click', async () => {
      // Mostrar modal ao invés de parar diretamente
      const countingInfoModal = new bootstrap.Modal(document.getElementById('countingInfoModal'));
      
      // Pré-preencher o tipo de animal baseado na câmera - usar somente detection_class_name
      const selectedOption = cameraSelect.options[cameraSelect.selectedIndex];
      const detectionClassName = selectedOption.dataset.detectionClass || selectedOption.getAttribute('data-detection-class') || '';
      console.log('selectedOption:', selectedOption);
      console.log('dataset.detectionClass:', selectedOption.dataset.detectionClass);
      console.log('getAttribute(data-detection-class):', selectedOption.getAttribute('data-detection-class'));
      console.log('detectionClassName final:', detectionClassName);
      document.getElementById('animalType').value = detectionClassName;
      
      countingInfoModal.show();
    });
  }

  // Confirmar parada com informações
  const btnConfirmCounting = document.getElementById('btnConfirmCounting');
  if (btnConfirmCounting) {
    btnConfirmCounting.addEventListener('click', async () => {
      try {
        // Validar se o tipo de animal foi preenchido
        const animalType = document.getElementById('animalType').value;
        if (!animalType.trim()) {
          alert('Por favor, preencha o tipo de animal');
          return;
        }

        // Coletar dados do formulário
        const countingData = {
          animal_type: animalType,
          batch_number: document.getElementById('batchNumber').value,
          recipient: document.getElementById('recipient').value,
          additional_notes: document.getElementById('additionalNotes').value,
        };

        const URLS = window.VIDEO_AO_VIVO_URLS || {};
        const response = await fetch(URLS.stop, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
          },
          body: JSON.stringify(countingData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Erro ao parar');
        }
        
        // Fechar modal
        bootstrap.Modal.getInstance(document.getElementById('countingInfoModal')).hide();
        
        // Parar polling
        if (window.statusInterval) {
          clearInterval(window.statusInterval);
          window.statusInterval = null;
        }
        
        // Parar stream
        const liveStreamEl = document.getElementById('liveStream');
        if (liveStreamEl) {
          liveStreamEl.src = '';
        }
        
        // Voltar para seleção
        if (countingActive) countingActive.style.display = 'none';
        if (cameraSelection) cameraSelection.style.display = 'block';
        if (liveStatus) liveStatus.style.display = 'none';
        
        // Limpar contadores
        const countInEl = document.getElementById('countIn');
        const countOutEl = document.getElementById('countOut');
        const countBalanceEl = document.getElementById('countBalance');
        const logListEl = document.getElementById('logList');
        
        if (countInEl) countInEl.textContent = '0';
        if (countOutEl) countOutEl.textContent = '0';
        if (countBalanceEl) countBalanceEl.textContent = '0';
        if (logListEl) logListEl.innerHTML = '';
        
        // Limpar formulário
        document.getElementById('countingInfoForm').reset();
        
        console.log('Contagem parada com informações, voltando para seleção');
        
      } catch (error) {
        alert('Erro ao parar: ' + error.message);
      }
    });
  }

  // Inicializar
  btnSelectCamera.disabled = true;
  setupLineInteraction();
  
  // Salvar sessão ao sair da página
  window.addEventListener('beforeunload', async (e) => {
    const URLS = window.VIDEO_AO_VIVO_URLS || {};
    if (countingActive && countingActive.style.display !== 'none' && URLS.stop) {
      // Tentar parar a contagem antes de sair
      try {
        await fetch(URLS.stop, { method: 'POST' });
      } catch (error) {
        console.error('Erro ao parar contagem:', error);
      }
    }
  });
  
  console.log('JavaScript inicializado com sucesso');
})();