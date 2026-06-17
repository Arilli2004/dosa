/* ============================================================
   DOSA CTF — EDIT ROLE USER JAVASCRIPT
   Handles loading users, selecting roles, updating permissions
   preview, and persisting changes via LocalStorage.
   ============================================================ */

(function() {
  'use strict';

  let users = [];

  function loadUsers() {
    fetch('/api/admin/users')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          users = data.users;
          renderUserList();
          if (selectedUser) {
            const updated = users.find(u => u.db_id === selectedUser.db_id);
            if (updated) {
              selectedUser = updated;
              if (selAvatar) selAvatar.textContent = initials(updated.name);
              if (selName) selName.textContent = updated.name;
              if (selMeta) selMeta.textContent = `${updated.role.toUpperCase()} // ${updated.email} // ${updated.status.toUpperCase()}`;
            }
          }
        }
      })
      .catch(err => console.error("Error loading admin users for role edit:", err));
  }

  // Initial load
  loadUsers();

  // Poll every 3 seconds for real-time list update
  setInterval(loadUsers, 3000);

  // 2. STATE
  let selectedUser = null;
  let chosenRole = 'Player';

  // 3. HELPERS
  function initials(name) {
    return name
      .split(/[_\s]/)
      .map(w => w[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }

  // 4. DOM ELEMENTS
  const userListContainer = document.getElementById('userList');
  const selectedCard = document.getElementById('selectedCard');
  const selAvatar = document.getElementById('selAvatar');
  const selName = document.getElementById('selName');
  const selMeta = document.getElementById('selMeta');
  const reasonInput = document.getElementById('reasonInput');
  const permList = document.getElementById('permList');
  const toast = document.getElementById('toast');
  const roleOptions = document.querySelectorAll('.role-option');

  // 5. RENDERING USER LIST
  function renderUserList() {
    if (!userListContainer) return;
    userListContainer.innerHTML = '';
    
    // Update count in header label
    const userCountEl = document.querySelector('.user-count');
    if (userCountEl) {
      userCountEl.textContent = `${users.length} USERS`;
    }

    users.forEach(u => {
      const div = document.createElement('div');
      div.className = 'user-item' + (selectedUser && selectedUser.db_id === u.db_id ? ' selected' : '');
      
      const status = u.status.toLowerCase();
      const dotClass = status === 'active' ? 'dot-active' : (status === 'banned' ? 'dot-banned' : 'dot-inactive');
      
      div.innerHTML = `
        <div class="u-avatar">${initials(u.name)}</div>
        <div class="u-info">
          <div class="u-name">${u.name}</div>
          <div class="u-role">${u.role}</div>
        </div>
        <div class="u-status-dot ${dotClass}"></div>
      `;
      
      div.addEventListener('click', () => {
        selectUser(u);
      });
      
      userListContainer.appendChild(div);
    });
  }

  // 6. SELECT USER
  window.selectUser = function(user) {
    selectedUser = user;
    renderUserList();
    
    // Populate user card details
    if (selAvatar) selAvatar.textContent = initials(user.name);
    if (selName) selName.textContent = user.name;
    if (selMeta) selMeta.textContent = `${user.role.toUpperCase()} // ${user.email} // ${user.status.toUpperCase()}`;
    
    // Select correct role button card
    updateSelectedRoleUI(user.role);
  };

  // 7. ROLE SELECTION
  window.selectRole = function(role) {
    updateSelectedRoleUI(role);
  };

  function updateSelectedRoleUI(role) {
    chosenRole = role;
    roleOptions.forEach(opt => {
      opt.classList.remove('selected-role');
      // Opt name is uppercase inside the div
      const optName = opt.querySelector('.role-opt-name').textContent.trim();
      if (optName === role.toUpperCase()) {
        opt.classList.add('selected-role');
      }
    });
    renderPermissionsPreview(role);
  }

  // Bind click listeners on role option cards
  roleOptions.forEach(opt => {
    opt.addEventListener('click', () => {
      const optNameEl = opt.querySelector('.role-opt-name');
      if (optNameEl) {
        let role = optNameEl.textContent.trim();
        // Capitalize role correctly (Admin, Moderator, Player)
        role = role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();
        updateSelectedRoleUI(role);
      }
    });
  });

  // 8. PERMISSIONS PREVIEW
  function renderPermissionsPreview(role) {
    if (!permList) return;
    
    const perms = [
      { name: 'View Challenges', admin: true, mod: true, player: true },
      { name: 'Submit Flags', admin: true, mod: true, player: true },
      { name: 'Manage Users', admin: true, mod: true, player: false },
      { name: 'Create Challenges', admin: true, mod: false, player: false },
      { name: 'System Config', admin: true, mod: false, player: false }
    ];

    permList.innerHTML = perms.map(p => {
      let active = false;
      if (role === 'Admin') active = p.admin;
      else if (role === 'Moderator') active = p.mod;
      else if (role === 'Player') active = p.player;

      const itemClass = active ? 'perm-active' : 'perm-inactive';
      const icon = active ? '✓' : '✕';

      return `<div class="permission-item ${itemClass}"><span class="perm-icon">${icon}</span>${p.name}</div>`;
    }).join('');
  }

  // 9. SAVE & RESET ACTIONS
  window.saveRole = function() {
    if (!selectedUser) {
      alert('Please select a user from the list first.');
      return;
    }
    
    const reason = reasonInput.value.trim();
    if (!reason) {
      alert('Audit log requires a reason for this role change.');
      return;
    }

    const dbId = selectedUser.db_id;
    const oldRole = selectedUser.role;

    fetch(`/api/admin/users/role/${dbId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ role: chosenRole })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        // Add audit log entry dynamically (mock audit log append)
        const auditContainer = document.querySelector('.audit-panel .panel-body');
        if (auditContainer) {
          const date = new Date();
          const timeStr = date.toTimeString().split(' ')[0].slice(0, 5);
          const logEntry = document.createElement('div');
          logEntry.className = 'audit-entry';
          logEntry.innerHTML = `
            <span class="audit-time">${timeStr}</span>
            <span class="audit-icon">✎</span>
            <span class="audit-text">
              <span class="audit-hl">${selectedUser.name}</span> changed from ${oldRole} to <span class="audit-hl">${chosenRole}</span>
            </span>
          `;
          auditContainer.insertBefore(logEntry, auditContainer.firstChild);
        }

        // Display Toast
        if (toast) {
          toast.textContent = `✓ ${selectedUser.name}'s role updated to ${chosenRole}`;
          toast.classList.add('show');
          setTimeout(() => {
            toast.classList.remove('show');
          }, 3000);
        }

        reasonInput.value = '';
        loadUsers();
      } else {
        alert('Failed to update role: ' + data.message);
      }
    })
    .catch(err => {
      console.error("Error saving user role:", err);
      alert('Error connecting to server.');
    });
  };

  window.resetForm = function() {
    if (selectedUser) {
      selectUser(selectedUser);
      reasonInput.value = '';
    }
  };

  // Initial load loaded in loadUsers()
  // renderUserList() called inside loadUsers()

})();
