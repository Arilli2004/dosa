// ANIME-STYLE CURSOR with particles, sword, and trail effects
const outer = document.getElementById('cursor-outer');
const inner = document.getElementById('cursor-inner');
const sword = document.getElementById('cursor-sword');
let mouseX = 0, mouseY = 0;
let outerX = 0, outerY = 0;
let lastX = 0, lastY = 0;

document.addEventListener('mousemove', (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
  
  // immediate inner circle update
  inner.style.left = mouseX + 'px';
  inner.style.top = mouseY + 'px';
  sword.style.left = mouseX + 'px';
  sword.style.top = mouseY + 'px';
  
  // trail effect: create floating particles every few pixels
  const dx = Math.abs(mouseX - lastX);
  const dy = Math.abs(mouseY - lastY);
  if (dx + dy > 8) {
    createTrailParticle(mouseX, mouseY);
    lastX = mouseX;
    lastY = mouseY;
  }
  
  // smooth outer ring lag (anime-style)
  requestAnimationFrame(() => {
    outerX += (mouseX - outerX) * 0.25;
    outerY += (mouseY - outerY) * 0.25;
    outer.style.left = outerX + 'px';
    outer.style.top = outerY + 'px';
  });
});

function createTrailParticle(x, y) {
  const particle = document.createElement('div');
  particle.className = 'trail-particle';
  particle.style.left = x + 'px';
  particle.style.top = y + 'px';
  document.body.appendChild(particle);
  setTimeout(() => { particle.remove(); }, 800);
}

function createClickSparks(x, y) {
  for (let i = 0; i < 8; i++) {
    const spark = document.createElement('div');
    spark.className = 'click-spark';
    const angle = (i / 8) * Math.PI * 2;
    const offsetX = Math.cos(angle) * (Math.random() * 20 + 8);
    const offsetY = Math.sin(angle) * (Math.random() * 20 + 8);
    spark.style.setProperty('--tx', offsetX + 'px');
    spark.style.setProperty('--ty', offsetY + 'px');
    spark.style.left = x + 'px';
    spark.style.top = y + 'px';
    document.body.appendChild(spark);
    setTimeout(() => spark.remove(), 500);
  }
  // also create floating orbs
  for (let i = 0; i < 5; i++) {
    const orb = document.createElement('div');
    orb.className = 'floating-orb';
    orb.style.left = x + (Math.random() - 0.5) * 40 + 'px';
    orb.style.top = y + (Math.random() - 0.5) * 40 + 'px';
    orb.style.setProperty('--fx', (Math.random() - 0.5) * 60 + 'px');
    orb.style.setProperty('--fy', (Math.random() - 0.5) * 50 - 30 + 'px');
    document.body.appendChild(orb);
    setTimeout(() => orb.remove(), 1200);
  }
  // outer pulse animation
  outer.classList.add('cursor-pulse');
  setTimeout(() => outer.classList.remove('cursor-pulse'), 800);
}

// hover detection for interactive elements (anime sword style)
const interactiveElements = document.querySelectorAll('a, button, .challenge-card, .feature-card, .stat-card, .btn-cta, .view-all, .challenge-link, .btn-hero, .btn-outline, .logo');
interactiveElements.forEach(el => {
  el.addEventListener('mouseenter', () => {
    document.body.classList.add('cursor-hover');
  });
  el.addEventListener('mouseleave', () => {
    document.body.classList.remove('cursor-hover');
  });
  el.addEventListener('click', (e) => {
    document.body.classList.add('cursor-click');
    createClickSparks(e.clientX, e.clientY);
    setTimeout(() => document.body.classList.remove('cursor-click'), 150);
  });
});

// global click for sparks on any area
document.addEventListener('click', (e) => {
  createClickSparks(e.clientX, e.clientY);
  document.body.classList.add('cursor-click');
  setTimeout(() => document.body.classList.remove('cursor-click'), 150);
});

// Scroll reveal and counter animation
const reveals = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); } });
}, { threshold: 0.12 });
reveals.forEach(el => observer.observe(el));

const statNums = document.querySelectorAll('.stat-num');
const parseNum = str => { const m = str.match(/^([\d.]+)([^0-9.]*)$/); return m ? { value: parseFloat(m[1]), suffix: m[2] } : null; };
const countObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target;
    const parsed = parseNum(el.textContent);
    if (!parsed) return;
    const { value, suffix } = parsed;
    let start = 0;
    const duration = 1400;
    const step = timestamp => {
      if (!start) start = timestamp;
      const prog = Math.min((timestamp - start) / duration, 1);
      const eased = 1 - Math.pow(1 - prog, 3);
      el.textContent = (value < 100 ? (eased * value).toFixed(value % 1 ? 1 : 0) : Math.round(eased * value)) + suffix;
      if (prog < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
    countObserver.unobserve(el);
  });
}, { threshold: 0.5 });
statNums.forEach(el => countObserver.observe(el));