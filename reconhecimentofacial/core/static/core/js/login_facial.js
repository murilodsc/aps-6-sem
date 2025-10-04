/**
 * JavaScript para Login com Reconhecimento Facial
 * Gerencia captura de vídeo, reconhecimento e comunicação com backend
 */

// Aguardar carregamento completo do DOM
document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    const startCameraBtn = document.getElementById('startCamera');
    const tryAgainBtn = document.getElementById('tryAgain');
    const statusMessage = document.getElementById('statusMessage');
    const processing = document.querySelector('.processing');
    const faceOverlay = document.querySelector('.face-overlay');
    
    let stream = null;
    let detectionInterval = null;
    let isProcessing = false;
    let faceDetectedTime = null;

    /**
     * Exibe mensagem de status com estilo
     * @param {string} message - Mensagem a ser exibida
     * @param {string} type - Tipo: info, success, error, warning
     */
    function showMessage(message, type = 'info') {
        statusMessage.innerHTML = `<div class="status-message status-${type}">${message}</div>`;
    }

    /**
     * Inicializa a câmera do dispositivo
     */
    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 640,
                    height: 480,
                    facingMode: 'user'
                }
            });

            video.srcObject = stream;
            canvas.width = 640;
            canvas.height = 480;

            startCameraBtn.style.display = 'none';
            
            // Aguardar vídeo estar pronto e iniciar detecção
            video.addEventListener('loadedmetadata', function() {
                startFaceDetection();
            });
            
            showMessage('Câmera ativada! Posicione seu rosto no círculo para reconhecimento automático.', 'success');
        } catch (err) {
            console.error('Erro ao acessar câmera:', err);
            showMessage('Erro ao acessar a câmera. Verifique se deu permissão.', 'error');
        }
    }

    /**
     * Inicia detecção contínua de rosto
     */
    function startFaceDetection() {
        detectionInterval = setInterval(() => {
            if (isProcessing) return;
            
            // Detectar se há rosto na região do círculo
            const faceDetected = detectFaceInCircle();
            
            if (faceDetected) {
                faceOverlay.classList.add('face-detected');
                
                // Marcar o tempo da primeira detecção
                if (!faceDetectedTime) {
                    faceDetectedTime = Date.now();
                }
                
                // Se rosto ficou posicionado por 1.5 segundos, capturar
                if (Date.now() - faceDetectedTime >= 1500) {
                    captureAndRecognize();
                }
            } else {
                faceOverlay.classList.remove('face-detected');
                faceDetectedTime = null;
            }
        }, 100);
    }

    /**
     * Detecta se há rosto na região do círculo central
     * Usa análise de pixels para determinar presença de conteúdo
     */
    function detectFaceInCircle() {
        if (!video.videoWidth || !video.videoHeight) return false;
        
        // Criar canvas temporário para análise
        const tempCanvas = document.createElement('canvas');
        const tempContext = tempCanvas.getContext('2d');
        
        // Configurar dimensões
        tempCanvas.width = video.videoWidth;
        tempCanvas.height = video.videoHeight;
        
        // Desenhar frame atual
        tempContext.drawImage(video, 0, 0);
        
        // Calcular região central (onde está o círculo)
        const centerX = tempCanvas.width / 2;
        const centerY = tempCanvas.height / 2;
        const radius = 120;
        
        // Analisar pixels na região central
        const imageData = tempContext.getImageData(
            centerX - radius,
            centerY - radius,
            radius * 2,
            radius * 2
        );
        
        // Calcular variação de pixels
        let totalBrightness = 0;
        let pixelCount = 0;
        
        for (let i = 0; i < imageData.data.length; i += 4) {
            const r = imageData.data[i];
            const g = imageData.data[i + 1];
            const b = imageData.data[i + 2];
            const brightness = (r + g + b) / 3;
            totalBrightness += brightness;
            pixelCount++;
        }
        
        const avgBrightness = totalBrightness / pixelCount;
        
        // Se a média de brilho estiver em uma faixa razoável, considera que há um rosto
        return avgBrightness > 30 && avgBrightness < 220;
    }

    /**
     * Para a detecção de rosto
     */
    function stopFaceDetection() {
        if (detectionInterval) {
            clearInterval(detectionInterval);
            detectionInterval = null;
        }
        faceDetectedTime = null;
    }

    /**
     * Captura imagem da webcam e envia para reconhecimento
     */
    async function captureAndRecognize() {
        if (isProcessing) return;
        isProcessing = true;
        stopFaceDetection();
        try {
            // Capturar frame do vídeo
            context.drawImage(video, 0, 0, 640, 480);
            const imageData = canvas.toDataURL('image/jpeg', 0.8);

            // Mostrar loading
            processing.classList.add('active');
            showMessage('Rosto detectado! Processando reconhecimento facial...', 'info');

            // Obter URL do endpoint
            const recognizeUrl = startCameraBtn.dataset.recognizeUrl;

            // Enviar imagem para o servidor
            const response = await fetch(recognizeUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `foto_base64=${encodeURIComponent(imageData)}`
            });

            const data = await response.json();

            processing.classList.remove('active');

            if (data.success) {
                isProcessing = false;
                // Reconhecimento bem-sucedido
                showMessage(
                    `✅ ${data.message}<br>Confiança: ${data.confidence}<br>Redirecionando...`,
                    'success'
                );
                
                // Parar câmera
                stopCamera();

                // Obter URL de redirecionamento
                const indexUrl = startCameraBtn.dataset.indexUrl;

                // Redirecionar após 2 segundos
                setTimeout(() => {
                    window.location.href = indexUrl;
                }, 2000);
            } else {
                // Falha no reconhecimento
                isProcessing = false;
                showMessage(`❌ ${data.message}<br>Tentando novamente em 3 segundos...`, 'error');
                faceOverlay.classList.remove('face-detected');
                
                // Reiniciar automaticamente após 3 segundos
                setTimeout(() => {
                    tryAgain();
                }, 3000);
            }
        } catch (error) {
            processing.classList.remove('active');
            isProcessing = false;
            console.error('Erro:', error);
            showMessage('Erro ao processar reconhecimento. Tentando novamente em 3 segundos...', 'error');
            faceOverlay.classList.remove('face-detected');
            
            // Reiniciar automaticamente após 3 segundos
            setTimeout(() => {
                tryAgain();
            }, 3000);
        }
    }

    /**
     * Para a transmissão da câmera
     */
    function stopCamera() {
        stopFaceDetection();
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    }

    /**
     * Reinicia o processo de reconhecimento
     */
    function tryAgain() {
        tryAgainBtn.style.display = 'none';
        isProcessing = false;
        faceOverlay.classList.remove('face-detected');
        startFaceDetection();
        showMessage('Posicione seu rosto no círculo para tentar novamente.', 'info');
    }

    // Event Listeners
    startCameraBtn.addEventListener('click', startCamera);
    tryAgainBtn.addEventListener('click', tryAgain);

    // Limpar recursos ao sair da página
    window.addEventListener('beforeunload', function() {
        stopCamera();
    });

    // Mensagem inicial
    showMessage('Clique em "Iniciar Câmera" para começar o reconhecimento facial.', 'info');
});
