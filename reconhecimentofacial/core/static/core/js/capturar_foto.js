let video = document.getElementById("video");
let canvas = document.getElementById("canvas");
let context = canvas.getContext("2d");
let capturedImageData = null;

// Elementos dos botões
const startCameraBtn = document.getElementById("startCamera");
const captureBtn = document.getElementById("captureBtn");
const retakeBtn = document.getElementById("retakeBtn");
const saveBtn = document.getElementById("saveBtn");
const preview = document.getElementById("preview");
const capturedImage = document.getElementById("capturedImage");
const messagesDiv = document.getElementById("messages");
const form = document.getElementById("captureForm");

// Iniciar câmera
startCameraBtn.addEventListener("click", async function () {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: 480,
        height: 360,
        facingMode: "user",
      },
    });
    video.srcObject = stream;

    startCameraBtn.disabled = true;
    startCameraBtn.textContent = "✅ Câmera Ativa";
    captureBtn.disabled = false;

    showMessage(
      'Câmera iniciada com sucesso! Posicione-se e clique em "Capturar Foto".',
      "success"
    );
  } catch (err) {
    console.error("Erro ao acessar a câmera:", err);
    showMessage(
      "Erro ao acessar a câmera. Verifique se você deu permissão para usar a câmera.",
      "danger"
    );
  }
});

// Capturar foto
captureBtn.addEventListener("click", function () {
  context.drawImage(video, 0, 0, 480, 360);
  capturedImageData = canvas.toDataURL("image/jpeg", 0.8);

  // Mostrar preview
  capturedImage.src = capturedImageData;
  preview.style.display = "block";

  // Parar o stream da câmera
  let stream = video.srcObject;
  let tracks = stream.getTracks();
  tracks.forEach((track) => track.stop());
  video.srcObject = null;

  // Ajustar botões
  captureBtn.style.display = "none";
  retakeBtn.style.display = "inline-block";
  saveBtn.style.display = "inline-block";
  saveBtn.disabled = false;

  showMessage(
    'Foto capturada! Verifique se está boa e clique em "Salvar Foto".',
    "info"
  );
});

// Tirar novamente
retakeBtn.addEventListener("click", function () {
  preview.style.display = "none";
  capturedImageData = null;

  // Resetar botões
  startCameraBtn.disabled = false;
  startCameraBtn.textContent = "🎥 Iniciar Câmera";
  captureBtn.disabled = true;
  captureBtn.style.display = "inline-block";
  retakeBtn.style.display = "none";
  saveBtn.style.display = "none";

  clearMessages();
});

// Salvar foto
form.addEventListener("submit", async function (e) {
  e.preventDefault();

  const nome = document.getElementById("nome").value.trim();

  if (!nome) {
    showMessage("Por favor, digite o nome da pessoa.", "warning");
    return;
  }

  if (!capturedImageData) {
    showMessage("Por favor, capture uma foto primeiro.", "warning");
    return;
  }

  saveBtn.disabled = true;
  saveBtn.textContent = "⏳ Salvando...";

  try {
    const response = await fetch("/salvar-foto/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        nome: nome,
        imagem: capturedImageData,
      }),
    });

    const data = await response.json();

    if (data.success) {
      showMessage(data.message, "success");
      setTimeout(() => {
        window.location.href = data.redirect_url;
      }, 2000);
    } else {
      showMessage("Erro: " + data.error, "danger");
      saveBtn.disabled = false;
      saveBtn.textContent = "💾 Salvar Foto";
    }
  } catch (error) {
    console.error("Erro:", error);
    showMessage("Erro ao salvar a foto. Tente novamente.", "danger");
    saveBtn.disabled = false;
    saveBtn.textContent = "💾 Salvar Foto";
  }
});

function showMessage(message, type) {
  messagesDiv.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

function clearMessages() {
  messagesDiv.innerHTML = "";
}

// Limpar mensagens ao carregar a página
document.addEventListener("DOMContentLoaded", function () {
  clearMessages();
});
