import os, glob, re

d = 'templates/admin_pages'
files = glob.glob(d+'/*.html')

# CSS to disable animated cursor completely + smooth scrolling
disable_cursor_css = """
    <style>
      /* ── DISABLE ANIMATED CURSOR (ADMIN PAGES) ── */
      #cursor-outer, #cursor-inner, #cursor-sword, .trail-particle, .click-spark, .floating-orb {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
      }
      * { cursor: default !important; }
      a, button, [onclick], select, label, input[type="submit"], .topbar-icon-btn, .btn-panel, .btn-outline, .manage-list li, .pwd-toggle-btn {
        cursor: pointer !important;
      }
      /* ── SMOOTH SCROLL + TRANSITIONS ── */
      html { scroll-behavior: smooth; }
      body { transition: none !important; }
      .panel, .stat-card, .mini-stat, .data-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
      }
      /* ── SMOOTH SCROLLBAR ── */
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: #111; }
      ::-webkit-scrollbar-thumb { background: rgba(217, 164, 65, 0.4); border-radius: 3px; }
      ::-webkit-scrollbar-thumb:hover { background: rgba(217, 164, 65, 0.7); }
    </style>
"""

# JS to kill cursor animation runtime (in case any JS tries to move the cursor)
disable_cursor_js = """
    <script>
      // Disable animated cursor on all admin pages
      window.__cursorDisabled = true;
      document.addEventListener('DOMContentLoaded', function() {
        ['cursor-outer','cursor-inner','cursor-sword'].forEach(function(id) {
          var el = document.getElementById(id);
          if (el) { el.style.display = 'none'; el.style.visibility = 'hidden'; }
        });
        // Remove all trail particles if any appear
        var observer = new MutationObserver(function(mutations) {
          mutations.forEach(function(m) {
            m.addedNodes.forEach(function(node) {
              if (node.classList && (node.classList.contains('trail-particle') || node.classList.contains('click-spark') || node.classList.contains('floating-orb'))) {
                node.remove();
              }
            });
          });
        });
        observer.observe(document.body, { childList: true });
      });
    </script>
"""

c_changed = 0
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    changed = False
    
    # Inject the disable cursor CSS just before </head>
    if 'DISABLE ANIMATED CURSOR (ADMIN PAGES)' not in c:
        c = c.replace('</head>', disable_cursor_css + '\n</head>')
        changed = True
    
    # Inject the JS just before </body>
    if 'window.__cursorDisabled = true' not in c:
        c = c.replace('</body>', disable_cursor_js + '\n</body>')
        changed = True
    
    if changed:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(c)
        c_changed += 1
        print(f"  Updated: {os.path.basename(f)}")

print(f"\nDone! Updated {c_changed} admin pages.")
