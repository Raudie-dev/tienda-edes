/* ==========================================
   EDES VENEZUELA - Lógica de Interactividad
   ========================================== */

document.addEventListener("DOMContentLoaded", () => {
  const brandsTrackLTR = document.getElementById("brandsCarouselTrackLTR");

  // simple infinite auto-scroll for brands (continuous, no start/end pause)
  function createInfiniteCarousel(track) {
    if (!track) return;
    if (track.dataset.infiniteReady === "true") return;

    const originalItems = Array.from(track.children);
    const itemCount = originalItems.length;
    if (itemCount === 0) return;

    // clone once to ensure seamless loop
    originalItems.forEach(item => track.appendChild(item.cloneNode(true)));

    track.style.animation = "none";
    let offset = 0;
    const duration = 100000;
    let lastTime = Date.now();
    let paused = false;
    const dir = track.classList.contains("brands-carousel-rtl") ? 1 : -1;
    let singleSetWidth = 0;

    const wrapper = track.parentElement;
    if (wrapper) {
      wrapper.addEventListener("mouseenter", () => (paused = true));
      wrapper.addEventListener("mouseleave", () => {
        paused = false;
        lastTime = Date.now();
      });
    }

    function measure() {
      const gap = parseInt(getComputedStyle(track).gap) || 48;
      const totalWidth = track.scrollWidth;
      if (totalWidth > 0) {
        singleSetWidth = totalWidth / 2;
        return;
      }

      const items = Array.from(track.children).slice(0, itemCount);
      const widths = items.map(item => item.getBoundingClientRect().width);
      const maxWidth = Math.max(0, ...widths);
      singleSetWidth = (maxWidth + gap) * itemCount;
    }

    function step() {
      const now = Date.now();
      const elapsed = now - lastTime;
      lastTime = now;
      if (paused) { requestAnimationFrame(step); return; }

      if (!singleSetWidth) {
        measure();
        if (!singleSetWidth) { requestAnimationFrame(step); return; }
      }

      offset += dir * (singleSetWidth / duration) * elapsed;

      if (dir < 0 && offset <= -singleSetWidth) offset = 0;
      if (dir > 0 && offset >= singleSetWidth) offset = 0;

      track.style.transform = `translateX(${offset}px)`;
      requestAnimationFrame(step);
    }

    // start immediately, then re-measure when images load
    measure();
    track.dataset.infiniteReady = "true";
    requestAnimationFrame(step);

    const images = Array.from(track.querySelectorAll("img"));
    images.forEach(img => {
      if (!img.complete) {
        img.addEventListener("load", () => measure(), { once: true });
        img.addEventListener("error", () => measure(), { once: true });
      }
    });

    window.addEventListener("resize", () => {
      measure();
    });
  }

  createInfiniteCarousel(brandsTrackLTR);

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
      resetAuto();
    });

    prevBtn.addEventListener("click", () => {
      const index = (currentIndex - 1 + slides.length) % slides.length;
      updateCarousel(index);
      resetAuto();
    });

    // Eventos de puntos
    dots.forEach((dot, index) => {
      dot.addEventListener("click", () => {
        updateCarousel(index);
        resetAuto();
      });
    });

    // Autoplay controlado (permite pausa extra al reiniciar ciclo)
    const autoDelay = 7000; // ms entre slides
    const wrapPauseDelay = 2000; // ms extra cuando completa la vuelta
    let autoTimer = null;

    function scheduleAuto(delay = autoDelay) {
      if (autoTimer) clearTimeout(autoTimer);
      autoTimer = setTimeout(() => {
        advance();
      }, delay);
    }

    function advance() {
      const nextIndex = (currentIndex + 1) % slides.length;
      updateCarousel(nextIndex);
      const nextDelay = nextIndex === 0 ? wrapPauseDelay : autoDelay;
      scheduleAuto(nextDelay);
    }

    // Iniciar autoplay
    scheduleAuto();

    // Reiniciar autoplay después de interacción
    function resetAuto() {
      scheduleAuto(autoDelay);
    }
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
