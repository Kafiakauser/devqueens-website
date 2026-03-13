// Shared interactions for all DevQueens pages.
document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.querySelector("[data-menu-btn]");
  const navLinks = document.querySelector("[data-nav-links]");

  if (menuButton && navLinks) {
    menuButton.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });
  }

  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (event) => {
      const targetId = link.getAttribute("href");
      if (!targetId || targetId === "#") return;
      const targetElement = document.querySelector(targetId);
      if (!targetElement) return;

      event.preventDefault();
      targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
      navLinks?.classList.remove("open");
    });
  });

  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.15 }
  );

  document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));

  document.querySelectorAll(".faq-item").forEach((item) => {
    const button = item.querySelector(".faq-btn");
    const answer = item.querySelector(".faq-answer");
    if (!button || !answer) return;

    const syncState = (isOpen) => {
      item.classList.toggle("open", isOpen);
      button.setAttribute("aria-expanded", String(isOpen));
      answer.hidden = !isOpen;
    };

    // Initialize state so first interaction is always deterministic.
    syncState(item.classList.contains("open"));

    const toggleFaq = () => {
      syncState(!item.classList.contains("open"));
    };

    button.addEventListener("click", (event) => {
      event.preventDefault();
      toggleFaq();
    });

    item.addEventListener("click", (event) => {
      // Make the header/card area tappable, but ignore clicks inside expanded answer content.
      if (event.target.closest(".faq-btn") || event.target.closest(".faq-answer")) return;
      toggleFaq();
    });
  });

  initParticles();
});

function initParticles() {
  const canvas = document.getElementById("particles");
  if (!canvas) return;

  const context = canvas.getContext("2d");
  if (!context) return;

  let particles = [];
  const density = 0.00007;

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const amount = Math.max(18, Math.floor(canvas.width * canvas.height * density));
    particles = Array.from({ length: amount }, createParticle);
  };

  const createParticle = () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    radius: Math.random() * 1.9 + 0.4,
    speedX: (Math.random() - 0.5) * 0.3,
    speedY: (Math.random() - 0.5) * 0.3,
    alpha: Math.random() * 0.5 + 0.15,
  });

  const draw = () => {
    context.clearRect(0, 0, canvas.width, canvas.height);
    for (const particle of particles) {
      particle.x += particle.speedX;
      particle.y += particle.speedY;

      if (particle.x < 0) particle.x = canvas.width;
      if (particle.x > canvas.width) particle.x = 0;
      if (particle.y < 0) particle.y = canvas.height;
      if (particle.y > canvas.height) particle.y = 0;

      context.beginPath();
      context.fillStyle = `rgba(0, 230, 118, ${particle.alpha})`;
      context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
      context.fill();
    }
    requestAnimationFrame(draw);
  };

  resize();
  draw();
  window.addEventListener("resize", resize);
}