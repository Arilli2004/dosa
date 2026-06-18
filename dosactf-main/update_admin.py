import os, glob

d = 'templates/admin_pages'
files = glob.glob(d+'/*.html')

old_btn = '<a href="/logout" class="topbar-icon-btn" title="Logout" style="color: var(--red); border-color: rgba(255, 59, 59, 0.22); text-decoration: none;">⏻</a>'
new_btn = '<a href="/logout" class="btn btn-outline-danger btn-sm d-flex align-items-center" title="Logout" style="text-decoration: none; padding: 4px 10px; font-family: \'Share Tech Mono\', monospace; font-weight: bold; border-color: rgba(255, 59, 59, 0.4);">⏻ LOGOUT</a>'
boot_link = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">'

c_changed = 0

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    if old_btn in c:
        c = c.replace(old_btn, new_btn)
        
        if boot_link not in c:
            c = c.replace('<link rel="stylesheet" href="/static/css/main.css">', '<link rel="stylesheet" href="/static/css/main.css">\n    ' + boot_link)
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(c)
        c_changed += 1

print(f"Changed {c_changed} files")
