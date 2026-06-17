/* PASSWORD STRENGTH */
function updateStrength(val) {
  var fill = document.getElementById('s-fill');
  var lbl = document.getElementById('s-label');
  var score = 0;
  
  if (val.length >= 8) score += 25;
  if (val.length >= 12) score += 15;
  if (/[A-Z]/.test(val)) score += 20;
  if (/[0-9]/.test(val)) score += 20;
  if (/[^A-Za-z0-9]/.test(val)) score += 20;
  
  fill.style.width = Math.min(score, 100) + '%';
  
  if (score < 30) {
    fill.style.background = '#FF3B3B';
    lbl.textContent = 'WEAK';
    lbl.style.color = 'var(--primary)';
  } else if (score < 60) {
    fill.style.background = 'linear-gradient(90deg,#FF6B00,#FFB300)';
    lbl.textContent = 'FAIR';
    lbl.style.color = '#FFB300';
  } else if (score < 85) {
    fill.style.background = 'linear-gradient(90deg,#FFB300,#00E676)';
    lbl.textContent = 'STRONG';
    lbl.style.color = '#00E676';
  } else {
    fill.style.background = 'linear-gradient(90deg,var(--secondary),var(--primary))';
    lbl.textContent = 'SECURED';
    lbl.style.color = 'var(--green)';
  }
}

/* Handle Registration */
function handleRegister() {
  var check = document.getElementById('terms-check');
  var username = document.getElementById('username').value.trim();
  var email = document.getElementById('email').value.trim();
  var password = document.getElementById('pw1').value;
  var confirm = document.getElementById('pw2').value;
  var btn = document.getElementById('register-btn');
  
  if (!username || !email || !password || !confirm) {
    btn.style.background = '#660000';
    btn.textContent = '⚠ Fill All Fields';
    setTimeout(function() {
      btn.style.background = '';
      btn.textContent = 'Initialize Account  →';
    }, 1600);
    return;
  }
  
  if (!check.classList.contains('on')) {
    check.style.borderColor = 'var(--primary)';
    check.style.boxShadow = '0 0 8px rgba(255,59,59,0.5)';
    setTimeout(function() {
      check.style.borderColor = '';
      check.style.boxShadow = '';
    }, 1000);
    return;
  }
  
  if (password !== confirm) {
    btn.style.background = '#660000';
    btn.textContent = '⚠ Passwords Mismatch';
    setTimeout(function() {
      btn.style.background = '';
      btn.textContent = 'Initialize Account  →';
    }, 1600);
    return;
  }
  
  if (password.length < 8) {
    btn.style.background = '#660000';
    btn.textContent = '⚠ Password Too Weak';
    setTimeout(function() {
      btn.style.background = '';
      btn.textContent = 'Initialize Account  →';
    }, 1600);
    return;
  }
  
  btn.textContent = 'Creating Account...';
  btn.style.opacity = '0.75';
  setTimeout(function() {
    btn.style.opacity = '1';
    btn.style.background = '#007d3a';
    btn.textContent = '✓ Account Created';
    setTimeout(function() {
      window.location.href = 'login.html';
    }, 800);
  }, 1200);
}

/* FLOATING PARTICLES */
var pCont = document.getElementById('particles');
for (var i = 0; i < 28; i++) {
  var p = document.createElement('div');
  p.className = 'particle';
  p.style.left = Math.random() * 100 + 'vw';
  p.style.bottom = '-10px';
  p.style.animationDuration = (7 + Math.random() * 14) + 's';
  p.style.animationDelay = (Math.random() * 12) + 's';
  var sz = Math.random() > 0.6 ? 3 : 2;
  p.style.width = p.style.height = sz + 'px';
  p.style.background = Math.random() > 0.5 ? 'var(--primary)' : 'var(--accent)';
  pCont.appendChild(p);
}

/* CHECKBOX TOGGLE */
var termsCheck = document.getElementById('terms-check');
if (termsCheck) {
  termsCheck.addEventListener('click', function() {
    this.classList.toggle('on');
  });
}

/* PASSWORD STRENGTH LISTENER */
var pw1 = document.getElementById('pw1');
if (pw1) {
  pw1.addEventListener('input', function() {
    updateStrength(this.value);
  });
}

/* ENHANCED ANIME CURSOR */
var cursorOuter = document.getElementById('cursor-outer');
var cursorInner = document.getElementById('cursor-inner');
var cursorSword = document.getElementById('cursor-sword');

var mouseX = 0, mouseY = 0;
var outerX = 0, outerY = 0;
var lastX = 0, lastY = 0;
var isInsideInput = false;

document.addEventListener('mousemove', function(e) {
  mouseX = e.clientX;
  mouseY = e.clientY;

  if (!isInsideInput) {
    cursorInner.style.left = mouseX + 'px';
    cursorInner.style.top = mouseY + 'px';
    cursorSword.style.left = (mouseX + 18) + 'px';
    cursorSword.style.top = (mouseY - 18) + 'px';
  }

  var dx = mouseX - lastX, dy = mouseY - lastY;
  if ((Math.abs(dx) > 1 || Math.abs(dy) > 1) && !isInsideInput) {
    var angle = Math.atan2(dy, dx) * 180 / Math.PI;
    cursorSword.style.transform = 'translate(-50%,-50%) rotate(' + (angle - 45) + 'deg)';
    createTrailParticle(mouseX, mouseY);
  }
  lastX = mouseX;
  lastY = mouseY;

  requestAnimationFrame(function() {
    outerX += (mouseX - outerX) * 0.25;
    outerY += (mouseY - outerY) * 0.25;
    if (!isInsideInput) {
      cursorOuter.style.left = outerX + 'px';
      cursorOuter.style.top = outerY + 'px';
    }
  });
});

function createTrailParticle(x, y) {
  var particle = document.createElement('div');
  particle.className = 'trail-particle';
  particle.style.left = x + 'px';
  particle.style.top = y + 'px';
  document.body.appendChild(particle);
  setTimeout(function() { particle.remove(); }, 800);
}

function createClickSparks(x, y) {
  for (var i = 0; i < 8; i++) {
    var spark = document.createElement('div');
    spark.className = 'click-spark';
    var angle = (i / 8) * Math.PI * 2;
    var offsetX = Math.cos(angle) * (Math.random() * 20 + 8);
    var offsetY = Math.sin(angle) * (Math.random() * 20 + 8);
    spark.style.setProperty('--tx', offsetX + 'px');
    spark.style.setProperty('--ty', offsetY + 'px');
    spark.style.left = x + 'px';
    spark.style.top = y + 'px';
    document.body.appendChild(spark);
    setTimeout(function() { spark.remove(); }, 500);
  }
  for (var i = 0; i < 5; i++) {
    var orb = document.createElement('div');
    orb.className = 'floating-orb';
    orb.style.left = x + (Math.random() - 0.5) * 40 + 'px';
    orb.style.top = y + (Math.random() - 0.5) * 40 + 'px';
    orb.style.setProperty('--fx', (Math.random() - 0.5) * 60 + 'px');
    orb.style.setProperty('--fy', (Math.random() - 0.5) * 50 - 30 + 'px');
    document.body.appendChild(orb);
    setTimeout(function() { orb.remove(); }, 1200);
  }
}

/* Interactive hover */
var interactiveEls = document.querySelectorAll('a, button, .check-box, .header-logo, .back-link, .btn-submit, .card-link a');
for (var i = 0; i < interactiveEls.length; i++) {
  var el = interactiveEls[i];
  el.addEventListener('mouseenter', function() {
    if (!isInsideInput) {
      document.body.classList.add('cursor-hover');
    }
  });
  el.addEventListener('mouseleave', function() {
    document.body.classList.remove('cursor-hover');
  });
  el.addEventListener('click', function(e) {
    document.body.classList.add('cursor-click');
    createClickSparks(e.clientX, e.clientY);
    setTimeout(function() { document.body.classList.remove('cursor-click'); }, 150);
  });
}

/* Global click listener */
document.addEventListener('click', function(e) {
  var isInput = e.target.classList && e.target.classList.contains('form-input');
  if (!isInput) {
    createClickSparks(e.clientX, e.clientY);
    document.body.classList.add('cursor-click');
    setTimeout(function() { document.body.classList.remove('cursor-click'); }, 150);
  }
});

/* INPUT FOCUS: HIDE CURSOR */
var formInputs = document.querySelectorAll('.form-input');
for (var i = 0; i < formInputs.length; i++) {
  var input = formInputs[i];
  input.style.cursor = 'text';

  input.addEventListener('mouseenter', function() {
    isInsideInput = true;
    cursorOuter.style.opacity = '0';
    cursorInner.style.opacity = '0';
    cursorSword.style.opacity = '0';
  });

  input.addEventListener('mouseleave', function() {
    isInsideInput = false;
    cursorInner.style.left = mouseX + 'px';
    cursorInner.style.top = mouseY + 'px';
    cursorOuter.style.left = mouseX + 'px';
    cursorOuter.style.top = mouseY + 'px';
    outerX = mouseX;
    outerY = mouseY;
    cursorOuter.style.opacity = '1';
    cursorInner.style.opacity = '1';
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      this.blur();
    }
  });
}

/* Attach register function to button */
var registerBtn = document.getElementById('register-btn');
if (registerBtn) {
  registerBtn.addEventListener('click', handleRegister);
}



