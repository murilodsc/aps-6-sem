// Script para captura de foto no formulário de usuário

document.addEventListener("DOMContentLoaded", function () {
  let video = document.getElementById("video");
  let canvas = document.getElementById("canvas");
  
  if (!canvas) {
    console.error("Canvas não encontrado");
    return;
  }
  
  let context = canvas.getContext("2d");
  let capturedPhotoData = null;

  const startCameraBtn = document.getElementById("startCamera");
  const capturePhotoBtn = document.getElementById("capturePhoto");
  const retakePhotoBtn = document.getElementById("retakePhoto");
  const selectFileBtn = document.getElementById("selectFile");
  const fileInput = document.getElementById("fileInput");
  const deletePhotoBtn = document.getElementById("deletePhoto");
  const fotoBase64Input = document.getElementById("foto_base64");
  const deleteFotoInput = document.getElementById("delete_foto");

  // Selecionar arquivo do dispositivo
  if (selectFileBtn) {
    selectFileBtn.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Botão selecionar foto clicado");
      fileInput.click();
    });
  }

  // Processar arquivo selecionado
  if (fileInput) {
    fileInput.addEventListener("change", function (e) {
      console.log("Arquivo selecionado", e.target.files);
      const file = e.target.files[0];
      if (file && file.type.startsWith("image/")) {
        const reader = new FileReader();

        reader.onload = function (event) {
          capturedPhotoData = event.target.result;

          // Atualizar preview
          let currentPreview = document.getElementById("previewImage");
          if (currentPreview.tagName === "IMG") {
            currentPreview.src = capturedPhotoData;
          } else {
            const imgElement = document.createElement("img");
            imgElement.src = capturedPhotoData;
            imgElement.alt = "Foto selecionada";
            imgElement.id = "previewImage";
            currentPreview.parentNode.replaceChild(imgElement, currentPreview);
          }

          // Salvar no campo hidden
          fotoBase64Input.value = capturedPhotoData;

          // Mostrar botão de tirar novamente
          if (retakePhotoBtn) {
            retakePhotoBtn.style.display = "inline-block";
          }

          // Mostrar botão de deletar se existir
          if (deletePhotoBtn) {
            deletePhotoBtn.style.display = "inline-block";
          }
        };

        reader.readAsDataURL(file);
      } else {
        alert("Por favor, selecione um arquivo de imagem válido.");
      }
    });
  }

  // Deletar foto
  if (deletePhotoBtn) {
    deletePhotoBtn.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Botão deletar foto clicado");
      
      if (confirm("Tem certeza que deseja deletar a foto do perfil?")) {
        // Limpar preview
        let currentPreview = document.getElementById("previewImage");
        if (currentPreview && currentPreview.tagName === "IMG") {
          const placeholderDiv = document.createElement("div");
          placeholderDiv.className = "photo-placeholder";
          placeholderDiv.id = "previewImage";
          placeholderDiv.innerHTML = '<span>📷</span><p>Sem foto</p>';
          currentPreview.parentNode.replaceChild(placeholderDiv, currentPreview);
        }

        // Marcar para deletar
        if (deleteFotoInput) {
          deleteFotoInput.value = "true";
        }
        if (fotoBase64Input) {
          fotoBase64Input.value = "";
        }
        capturedPhotoData = null;

        // Esconder botão de deletar
        deletePhotoBtn.style.display = "none";
        
        console.log("Foto marcada para deleção");
      }
    });
  }

  // Iniciar câmera
  if (startCameraBtn) {
    startCameraBtn.addEventListener("click", async function (e) {
      e.preventDefault();
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: 640,
            height: 480,
            facingMode: "user",
          },
        });

        video.srcObject = stream;
        video.style.display = "block";
        canvas.width = 640;
        canvas.height = 480;

        startCameraBtn.style.display = "none";
        if (selectFileBtn) {
          selectFileBtn.style.display = "none";
        }
        capturePhotoBtn.style.display = "inline-block";
      } catch (err) {
        console.error("Erro ao acessar a câmera:", err);
        alert(
          "Erro ao acessar a câmera. Verifique se você deu permissão para usar a câmera."
        );
      }
    });
  }

  // Capturar foto
  if (capturePhotoBtn) {
    capturePhotoBtn.addEventListener("click", function (e) {
      e.preventDefault();
      context.drawImage(video, 0, 0, 640, 480);
      capturedPhotoData = canvas.toDataURL("image/jpeg", 0.8);

      // Parar o stream da câmera
      let stream = video.srcObject;
      if (stream) {
        let tracks = stream.getTracks();
        tracks.forEach((track) => track.stop());
      }
      video.srcObject = null;
      video.style.display = "none";

      // Atualizar preview
      let currentPreview = document.getElementById("previewImage");
      if (currentPreview.tagName === "IMG") {
        currentPreview.src = capturedPhotoData;
      } else {
        const imgElement = document.createElement("img");
        imgElement.src = capturedPhotoData;
        imgElement.alt = "Foto capturada";
        imgElement.id = "previewImage";
        currentPreview.parentNode.replaceChild(imgElement, currentPreview);
      }

      // Salvar no campo hidden
      fotoBase64Input.value = capturedPhotoData;

      // Ajustar botões
      capturePhotoBtn.style.display = "none";
      if (retakePhotoBtn) {
        retakePhotoBtn.style.display = "inline-block";
      }
      startCameraBtn.style.display = "none";
      if (selectFileBtn) {
        selectFileBtn.style.display = "none";
      }

      // Mostrar botão de deletar se existir
      if (deletePhotoBtn) {
        deletePhotoBtn.style.display = "inline-block";
      }
    });
  }

  // Tirar novamente
  if (retakePhotoBtn) {
    retakePhotoBtn.addEventListener("click", function (e) {
      e.preventDefault();
      capturedPhotoData = null;
      fotoBase64Input.value = "";

      // Resetar botões
      if (startCameraBtn) {
        startCameraBtn.style.display = "inline-block";
      }
      if (selectFileBtn) {
        selectFileBtn.style.display = "inline-block";
      }
      if (capturePhotoBtn) {
        capturePhotoBtn.style.display = "none";
      }
      retakePhotoBtn.style.display = "none";
    });
  }

  // Validação de senha no formulário
  const form = document.getElementById("userForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      const password = document.querySelector(
        'input[name="password"], input[name="new_password"]'
      );
      const passwordConfirm = document.querySelector(
        'input[name="password_confirm"]'
      );

      if (password && passwordConfirm) {
        if (password.value && passwordConfirm.value) {
          if (password.value !== passwordConfirm.value) {
            e.preventDefault();
            alert("As senhas não coincidem!");
            return false;
          }
        }
      }
    });
  }

  // Máscara para CPF
  const cpfInput = document.getElementById("cpf");
  if (cpfInput) {
    cpfInput.addEventListener("input", function (e) {
      let value = e.target.value.replace(/\D/g, "");
      if (value.length <= 11) {
        value = value.replace(/(\d{3})(\d)/, "$1.$2");
        value = value.replace(/(\d{3})(\d)/, "$1.$2");
        value = value.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
      }
      e.target.value = value;
    });
  }

  // Máscara para telefone
  const telefoneInput = document.getElementById("telefone");
  if (telefoneInput) {
    telefoneInput.addEventListener("input", function (e) {
      let value = e.target.value.replace(/\D/g, "");
      if (value.length <= 11) {
        value = value.replace(/^(\d{2})(\d)/g, "($1) $2");
        value = value.replace(/(\d)(\d{4})$/, "$1-$2");
      }
      e.target.value = value;
    });
  }

  // Contador de caracteres para bio
  const bioTextarea = document.getElementById("bio");
  if (bioTextarea) {
    const maxLength = bioTextarea.getAttribute("maxlength");
    const formHelp = bioTextarea.nextElementSibling;

    if (formHelp) {
      bioTextarea.addEventListener("input", function () {
        const remaining = maxLength - this.value.length;
        formHelp.textContent = `${remaining} caracteres restantes`;
      });
    }
  }
});