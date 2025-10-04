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
    const captureBtn = document.getElementById('captureAndRecognize');
    const tryAgainBtn = document.getElementById('tryAgain');
    const statusMessage = document.getElementById('statusMessage');
    const processing = document.querySelector('.processing');
    
    let stream = null;

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
            captureBtn.style.display = 'inline-block';
            showMessage('Câmera ativada! Posicione seu rosto e clique em "Reconhecer Rosto".', 'success');
        } catch (err) {
            console.error('Erro ao acessar câmera:', err);
            showMessage('Erro ao acessar a câmera. Verifique se deu permissão.', 'error');
        }
    }

    /**
     * Captura imagem da webcam e envia para reconhecimento
     */
    async function captureAndRecognize() {
        try {
            // Capturar frame do vídeo
            context.drawImage(video, 0, 0, 640, 480);
            const imageData = canvas.toDataURL('image/jpeg', 0.8);

            // Desabilitar botão e mostrar loading
            captureBtn.disabled = true;
            processing.classList.add('active');
            showMessage('Processando reconhecimento facial...', 'info');

            // Obter URL do endpoint (configurada no template)
            const recognizeUrl = captureBtn.dataset.recognizeUrl;

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
            captureBtn.disabled = false;

            if (data.success) {
                // Reconhecimento bem-sucedido
                showMessage(
                    `✅ ${data.message}<br>Confiança: ${data.confidence}<br>Redirecionando...`,
                    'success'
                );
                
                // Parar câmera
                stopCamera();

                // Obter URL de redirecionamento (configurada no template)
                const indexUrl = captureBtn.dataset.indexUrl;

                // Redirecionar após 2 segundos
                setTimeout(() => {
                    window.location.href = indexUrl;
                }, 2000);
            } else {
                // Falha no reconhecimento
                showMessage(`❌ ${data.message}`, 'error');
                captureBtn.style.display = 'none';
                tryAgainBtn.style.display = 'inline-block';
            }
        } catch (error) {
            processing.classList.remove('active');
            captureBtn.disabled = false;
            console.error('Erro:', error);
            showMessage('Erro ao processar reconhecimento. Tente novamente.', 'error');
        }
    }

    /**
     * Para a transmissão da câmera
     */
    function stopCamera() {
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
        captureBtn.style.display = 'inline-block';
        showMessage('Posicione seu rosto e tente novamente.', 'info');
    }

    // Event Listeners
    startCameraBtn.addEventListener('click', startCamera);
    captureBtn.addEventListener('click', captureAndRecognize);
    tryAgainBtn.addEventListener('click', tryAgain);

    // Limpar recursos ao sair da página
    window.addEventListener('beforeunload', function() {
        stopCamera();
    });

    // Mensagem inicial
    showMessage('Clique em "Iniciar Câmera" para começar o reconhecimento facial.', 'info');
});
