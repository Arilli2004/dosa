import os, glob

d = 'templates/admin_pages'
files = glob.glob(d+'/*.html')

mobile_css = """
    <style>
      /* Perfect Mobile Interface Overrides */
      @media (max-width: 768px) {
        .topbar { flex-direction: column !important; height: auto !important; padding: 15px !important; gap: 15px !important; }
        .topbar-right { width: 100% !important; justify-content: space-between !important; flex-wrap: wrap !important; gap: 10px !important; }
        .topbar-brand { font-size: 1.2rem !important; }
        .topbar-page { font-size: 0.9rem !important; }
        .main-content { padding: 10px !important; }
        .page-header { flex-direction: column !important; align-items: flex-start !important; gap: 15px !important; }
        .page-header-right { width: 100% !important; justify-content: flex-start !important; }
        .panel, .stat-card, .data-card, .user-card, .challenge-card { width: 100% !important; }
      }
    </style>
</head>
"""

c_changed = 0

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    if "Perfect Mobile Interface Overrides" not in c:
        c = c.replace('</head>', mobile_css)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(c)
        c_changed += 1

print(f"Added mobile CSS to {c_changed} files")
