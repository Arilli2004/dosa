/* ============================================================
   DOSA CTF — GLOBAL JAVASCRIPT
   Handles Cursor, Particles, Scroll Reveal, and Counters.
   ============================================================ */

(function() {
  'use strict';

  // 1. ANIME-STYLE CURSOR (Desktop only — disabled on mobile/touch devices)
  // Disabled as per Phase 1 bug fix request to remove cursor glitch
  const isMobile = window.innerWidth < 768;

  const outer = document.getElementById('cursor-outer');
  const inner = document.getElementById('cursor-inner');
  const sword = document.getElementById('cursor-sword');

  if (outer && inner && !isMobile) {
    let mouseX = -100, mouseY = -100;
    let outerX = -100, outerY = -100;
    let lastX = -100, lastY = -100;
    
    document.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      
      inner.style.left = mouseX + 'px';
      inner.style.top = mouseY + 'px';
      if(sword) {
        sword.style.left = mouseX + 'px';
        sword.style.top = mouseY + 'px';
      }
      
      // Trail effect
      const dx = Math.abs(mouseX - lastX);
      const dy = Math.abs(mouseY - lastY);
      if (dx + dy > 12) {
        createTrailParticle(mouseX, mouseY);
        lastX = mouseX;
        lastY = mouseY;
      }
    });

    // Smooth outer ring lag
    function animateCursor() {
      outerX += (mouseX - outerX) * 0.25;
      outerY += (mouseY - outerY) * 0.25;
      outer.style.left = outerX + 'px';
      outer.style.top = outerY + 'px';
      requestAnimationFrame(animateCursor);
    }
    requestAnimationFrame(animateCursor);

    function createTrailParticle(x, y) {
      const particle = document.createElement('div');
      particle.className = 'trail-particle';
      particle.style.left = x + 'px';
      particle.style.top = y + 'px';
      // Inline styles in case CSS is missing
      particle.style.position = 'fixed';
      particle.style.width = '4px';
      particle.style.height = '4px';
      particle.style.background = 'var(--primary, #D9A441)';
      particle.style.borderRadius = '50%';
      particle.style.pointerEvents = 'none';
      particle.style.zIndex = '99997';
      particle.style.transform = 'translate(-50%, -50%)';
      particle.style.animation = 'trail-fade 0.5s ease-out forwards';
      document.body.appendChild(particle);
      setTimeout(() => particle.remove(), 500);
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
        
        // Ensure inline styles for sparks
        spark.style.position = 'fixed';
        spark.style.width = '3px';
        spark.style.height = '12px';
        spark.style.background = 'var(--primary, #D9A441)';
        spark.style.borderRadius = '4px';
        spark.style.pointerEvents = 'none';
        spark.style.zIndex = '99998';
        spark.style.transform = 'translate(-50%, -50%)';
        spark.style.animation = 'spark-fly 0.5s ease-out forwards';
        
        document.body.appendChild(spark);
        setTimeout(() => spark.remove(), 500);
      }
      outer.classList.add('cursor-pulse');
      setTimeout(() => outer.classList.remove('cursor-pulse'), 800);
    }

    // Add styles dynamically if not present
    if (!document.getElementById('cursor-styles-dynamic')) {
      const style = document.createElement('style');
      style.id = 'cursor-styles-dynamic';
      style.textContent = `
        @keyframes trail-fade { to { opacity: 0; transform: translate(-50%,-50%) scale(0.2); } }
        @keyframes spark-fly { to { opacity: 0; transform: translate(calc(-50% + var(--tx)), calc(-50% + var(--ty))) scale(0); } }
        body { cursor: none !important; }
        a, button { cursor: none !important; }
        input, select, textarea { cursor: auto !important; }
      `;
      document.head.appendChild(style);
    }

    // Global click listener for sparks
    document.addEventListener('click', (e) => {
      createClickSparks(e.clientX, e.clientY);
      document.body.classList.add('cursor-click');
      setTimeout(() => document.body.classList.remove('cursor-click'), 150);
    });

    // Hover detection
    const interactiveElements = document.querySelectorAll('a, button, .challenge-card, .feature-card, .stat-card, .logo');
    interactiveElements.forEach(el => {
      el.addEventListener('mouseenter', () => document.body.classList.add('cursor-hover'));
      el.addEventListener('mouseleave', () => document.body.classList.remove('cursor-hover'));
    });

    // Hide custom cursor and show standard cursor on text/selection inputs
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(inp => {
      inp.addEventListener('mouseenter', () => {
        if (outer) outer.style.opacity = '0';
        if (inner) inner.style.opacity = '0';
        if (sword) sword.style.opacity = '0';
      });
      inp.addEventListener('mouseleave', () => {
        if (outer) outer.style.opacity = '1';
        if (inner) inner.style.opacity = '1';
        if (sword) sword.style.opacity = '1';
      });
    });
  }

  // 2. PARTICLES SYSTEM
  const particlesContainer = document.getElementById('particles');
  if (particlesContainer) {
    for (let i = 0; i < 30; i++) {
      const p = document.createElement('div');
      p.className = 'particle';
      p.style.position = 'absolute';
      p.style.borderRadius = '50%';
      p.style.left = Math.random() * 100 + 'vw';
      p.style.bottom = '-10px';
      p.style.animation = 'float-up linear infinite';
      p.style.animationDuration = (8 + Math.random() * 14) + 's';
      p.style.animationDelay = (Math.random() * 10) + 's';
      const sz = Math.random() > 0.6 ? 3 : 2;
      p.style.width = p.style.height = sz + 'px';
      p.style.background = Math.random() > 0.5 ? 'var(--primary, #D9A441)' : 'var(--accent, #FF7A30)';
      particlesContainer.appendChild(p);
    }
  }

  // 3. SCROLL REVEAL
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length > 0 && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          observer.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(el => observer.observe(el));
  } else {
    // Fallback
    reveals.forEach(el => el.classList.add('visible'));
  }

  // 4. COUNTER ANIMATION
  const statNums = document.querySelectorAll('.stat-num');
  if (statNums.length > 0 && 'IntersectionObserver' in window) {
    const parseNum = str => {
      const m = str.match(/^([\d.]+)([^0-9.]*)$/);
      return m ? { value: parseFloat(m[1]), suffix: m[2] } : null;
    };
    const countObserver = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        const el = e.target;
        const parsed = parseNum(el.textContent);
        if (!parsed) return;
        const { value, suffix } = parsed;
        let start = null;
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
  }

})();
