/* ==========================================
   EDES VENEZUELA - Lógica de Interactividad
   ========================================== */

document.addEventListener("DOMContentLoaded", () => {
  // 1. LÓGICA DEL CARRUSEL "ANTES Y DESPUÉS"
  const track = document.getElementById("baCarouselTrack");
  const prevBtn = document.getElementById("baPrev");
  const nextBtn = document.getElementById("baNext");
  const dots = document.querySelectorAll(".ba-dot");

  if (track && prevBtn && nextBtn) {
    const slides = Array.from(track.children);
    let currentIndex = 0;

    function updateCarousel(index) {
      // Mover el track
      track.style.transform = `translateX(-${index * 100}%)`;

      // Actualizar puntos
      dots.forEach((dot) => dot.classList.remove("active"));
      if (dots[index]) dots[index].classList.add("active");

      currentIndex = index;
    }

    // Eventos de botones
    nextBtn.addEventListener("click", () => {
      const index = (currentIndex + 1) % slides.length;
      updateCarousel(index);
    });

    prevBtn.addEventListener("click", () => {
      const index = (currentIndex - 1 + slides.length) % slides.length;
      updateCarousel(index);
    });

    // Eventos de puntos
    dots.forEach((dot, index) => {
      dot.addEventListener("click", () => {
        updateCarousel(index);
      });
    });

    // Autoplay opcional cada 7 segundos
    setInterval(() => {
      const index = (currentIndex + 1) % slides.length;
      updateCarousel(index);
    }, 7000);
  }

  // 2. LÓGICA DEL HEADER (CAMBIO DE COLOR AL HACER SCROLL)
  const header = document.getElementById("mainHeader");

  if (header) {
    function checkScroll() {
      if (window.scrollY > 50) {
        header.classList.add("scrolled");
      } else {
        header.classList.remove("scrolled");
      }
    }

    // Ejecutar al cargar y al hacer scroll
    window.addEventListener("scroll", checkScroll);
    checkScroll();
  }

  // 3. INICIALIZACIÓN DE TOASTS (NOTIFICACIONES)
  // Nota: Requiere Bootstrap para funcionar. Si no tienes Bootstrap cargado, este código no hará nada.
  const toastElements = document.querySelectorAll(".toast");
  const bootstrap = window.bootstrap; // Declare the bootstrap variable

  if (toastElements.length > 0 && typeof bootstrap !== "undefined") {
    toastElements.forEach((toastEl) => {
      const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
      toast.show();
    });
  }
});

document.addEventListener(
  "contextmenu",
  function (e) {
    if (e.target.nodeName === "IMG") {
      e.preventDefault();
    }
  },
  false
);

// Opcional: Evitar atajos de teclado como Ctrl+S o Ctrl+U (Ver código fuente)
document.addEventListener("keydown", function (e) {
  if (e.ctrlKey && (e.key === "s" || e.key === "u")) {
    e.preventDefault();
  }
});
