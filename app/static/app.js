const body = document.body;
const state = {
  appName: body.dataset.appName,
  clientIp: body.dataset.clientIp,
  csrfToken: null,
  currentUser: null,
  roles: [],
};

const elements = {
  flash: document.getElementById("flash"),
  authPanel: document.getElementById("auth-panel"),
  dashboard: document.getElementById("dashboard"),
  sessionName: document.getElementById("session-name"),
  sessionMeta: document.getElementById("session-meta"),
  refreshButton: document.getElementById("refresh-button"),
  logoutButton: document.getElementById("logout-button"),
  loginForm: document.getElementById("login-form"),
  registerForm: document.getElementById("register-form"),
  reservationForm: document.getElementById("reservation-form"),
  maintenanceForm: document.getElementById("maintenance-form"),
  borrowingForm: document.getElementById("borrowing-form"),
  labForm: document.getElementById("lab-form"),
  equipmentForm: document.getElementById("equipment-form"),
  reservationLab: document.getElementById("reservation-lab"),
  maintenanceEquipment: document.getElementById("maintenance-equipment"),
  borrowingEquipment: document.getElementById("borrowing-equipment"),
  borrowingUser: document.getElementById("borrowing-user"),
  adminEquipmentLab: document.getElementById("admin-equipment-lab"),
  operatorPanel: document.getElementById("operator-panel"),
  technicianPanel: document.getElementById("technician-panel"),
  adminPanel: document.getElementById("admin-panel"),
};

function setFlash(message, tone = "idle") {
  elements.flash.textContent = message;
  elements.flash.className = `flash flash--${tone}`;
}

function formatDate(value) {
  if (!value) return "N/A";
  return new Date(value).toLocaleString();
}

function formatRole(roleName) {
  return roleName ? roleName.toUpperCase() : "GUEST";
}

function toIso(localValue) {
  return new Date(localValue).toISOString();
}

function renderStack(containerId, entries) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = entries.length ? entries.join("") : '<div class="empty-state">No records yet.</div>';
}

function setCount(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = String(value);
}

function optionMarkup(value, label, selected = false) {
  return `<option value="${value}"${selected ? " selected" : ""}>${label}</option>`;
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (state.csrfToken && options.method && options.method !== "GET" && options.method !== "HEAD") {
    headers.set("X-CSRF-Token", state.csrfToken);
  }

  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const csrfToken = response.headers.get("X-CSRF-Token");
  if (csrfToken) state.csrfToken = csrfToken;

  const contentType = response.headers.get("Content-Type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof payload === "object" && payload !== null ? payload.detail || JSON.stringify(payload) : payload;
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return payload;
}

async function loadCurrentUser() {
  try {
    const user = await api("/auth/me");
    state.currentUser = user;
    return user;
  } catch (_) {
    state.currentUser = null;
    state.csrfToken = null;
    return null;
  }
}

function roleFlags() {
  const role = state.currentUser?.role_name;
  return {
    staff: role === "Staff" || role === "Admin",
    technician: role === "Technician" || role === "Admin",
    admin: role === "Admin",
  };
}

function renderOverview(common, staffSummary) {
  const cards = [
    { label: "Role", value: formatRole(state.currentUser.role_name) },
    { label: "Open Reservations", value: common.reservations.filter((item) => item.status !== "Cancelled").length },
    { label: "Borrowed Items", value: common.borrowings.filter((item) => item.status === "Borrowed").length },
    { label: "Unread Notices", value: common.notifications.filter((item) => !item.is_read).length },
  ];

  if (staffSummary) {
    cards.push(
      { label: "Total Users", value: staffSummary.total_users },
      { label: "Active Repairs", value: staffSummary.active_repairs }
    );
  }

  document.getElementById("overview-cards").innerHTML = cards
    .map((item) => `
      <article class="stat-card">
        <span class="stat-card__label">${item.label}</span>
        <strong class="stat-card__value">${item.value}</strong>
      </article>
    `)
    .join("");
}

function renderCommon(common) {
  setCount("labs-count", common.labs.length);
  setCount("equipment-count", common.equipments.length);
  setCount("my-reservations-count", common.reservations.length);
  setCount("my-borrowings-count", common.borrowings.length);
  setCount("my-penalties-count", common.penalties.length);
  setCount("my-notifications-count", common.notifications.length);

  renderStack(
    "labs-list",
    common.labs.map(
      (lab) => `
        <article class="list-item">
          <div>
            <strong>${lab.room_name}</strong>
            <p>Capacity ${lab.capacity} | ${lab.status}</p>
          </div>
        </article>
      `
    )
  );

  renderStack(
    "equipment-list",
    common.equipments.map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>${item.equipment_name}</strong>
            <p>Status ${item.status} | Lab ${item.lab_id ?? "Unassigned"}</p>
          </div>
        </article>
      `
    )
  );

  renderStack(
    "my-reservations",
    common.reservations.map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>Reservation #${item.reservation_id}</strong>
            <p>Lab ${item.lab_id} | ${formatDate(item.start_time)} to ${formatDate(item.end_time)}</p>
            <p>Status ${item.status}</p>
          </div>
          ${item.status !== "Cancelled" ? `<button class="inline-action" data-action="cancel-reservation" data-id="${item.reservation_id}">Cancel</button>` : ""}
        </article>
      `
    )
  );

  renderStack(
    "my-borrowings",
    common.borrowings.map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>Borrowing #${item.borrow_id}</strong>
            <p>Equipment ${item.equipment_id} | Due ${formatDate(item.expected_return)}</p>
            <p>Status ${item.status}</p>
          </div>
        </article>
      `
    )
  );

  renderStack(
    "my-penalties",
    common.penalties.map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>Penalty #${item.penalty_id}</strong>
            <p>Borrowing ${item.borrow_id} | ${Number(item.fine_amount).toFixed(2)} THB</p>
            <p>${item.is_resolved ? "Resolved" : "Pending"}</p>
          </div>
        </article>
      `
    )
  );

  renderStack(
    "my-notifications",
    common.notifications.map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>${item.is_read ? "Read" : "Unread"} notification</strong>
            <p>${item.message}</p>
            <p>${formatDate(item.created_at)}</p>
          </div>
        </article>
      `
    )
  );

  elements.reservationLab.innerHTML = common.labs.length
    ? common.labs.map((lab, index) => optionMarkup(lab.lab_id, `${lab.room_name} (${lab.capacity})`, index === 0)).join("")
    : optionMarkup("", "No available labs", true);

  const availableEquipment = common.equipments.filter((item) => item.status === "Available");
  const equipmentOptions = availableEquipment.length
    ? availableEquipment.map((item, index) => optionMarkup(item.equipment_id, `${item.equipment_name} (#${item.equipment_id})`, index === 0)).join("")
    : optionMarkup("", "No available equipment", true);

  elements.maintenanceEquipment.innerHTML = equipmentOptions;
  elements.borrowingEquipment.innerHTML = equipmentOptions;
  elements.adminEquipmentLab.innerHTML =
    optionMarkup("", "Unassigned", true) +
    common.labs.map((lab) => optionMarkup(lab.lab_id, lab.room_name)).join("");
}

function renderStaff(staffSummary, staffUsers, borrowings) {
  document.getElementById("staff-summary").innerHTML = `
    <div class="metric-row"><span>Total users</span><strong>${staffSummary.total_users}</strong></div>
    <div class="metric-row"><span>Total labs</span><strong>${staffSummary.total_labs}</strong></div>
    <div class="metric-row"><span>Total equipment</span><strong>${staffSummary.total_equipments}</strong></div>
    <div class="metric-row"><span>Active borrowings</span><strong>${staffSummary.active_borrowings}</strong></div>
    <div class="metric-row"><span>Active repairs</span><strong>${staffSummary.active_repairs}</strong></div>
  `;

  elements.borrowingUser.innerHTML = staffUsers.length
    ? staffUsers.map((user, index) => optionMarkup(user.user_id, `${user.first_name} ${user.last_name} (${user.role_name})`, index === 0)).join("")
    : optionMarkup("", "No users", true);

  setCount("active-borrowings-count", borrowings.length);
  renderStack(
    "active-borrowings",
    borrowings.map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>Borrowing #${item.borrow_id}</strong>
            <p>User ${item.user_id} | Equipment ${item.equipment_id}</p>
            <p>Due ${formatDate(item.expected_return)} | ${item.status}</p>
          </div>
          ${item.status === "Borrowed" ? `<button class="inline-action" data-action="return-borrowing" data-id="${item.borrow_id}">Mark Returned</button>` : ""}
        </article>
      `
    )
  );
}

function renderMaintenance(queue) {
  setCount("maintenance-count", queue.length);
  const statuses = ["Reported", "In Progress", "Fixed"];
  renderStack(
    "maintenance-queue",
    queue.map(
      (item) => `
        <article class="list-item list-item--vertical">
          <div>
            <strong>Repair #${item.repair_id}</strong>
            <p>Equipment ${item.equipment_id} | Reported by ${item.reported_by}</p>
            <p>${item.issue_detail}</p>
            <p>Status ${item.status}</p>
          </div>
          <div class="action-cluster">
            ${statuses
              .map(
                (status) =>
                  `<button class="inline-action" data-action="maintenance-status" data-id="${item.repair_id}" data-status="${status}">${status}</button>`
              )
              .join("")}
          </div>
        </article>
      `
    )
  );
}

function renderAdmin(users, auditLogs) {
  setCount("admin-users-count", users.length);
  setCount("audit-count", auditLogs.length);
  renderStack(
    "admin-users",
    users.map((user) => {
      const options = state.roles
        .map((role) => optionMarkup(role.role_name, role.role_name, role.role_name === user.role_name))
        .join("");
      return `
        <article class="list-item list-item--vertical">
          <div>
            <strong>${user.first_name} ${user.last_name}</strong>
            <p>${user.email}</p>
            <p>Current role ${user.role_name}</p>
          </div>
          <div class="action-cluster">
            <select class="inline-select" data-role-user="${user.user_id}">
              ${options}
            </select>
            <button class="inline-action" data-action="update-role" data-id="${user.user_id}">Update Role</button>
          </div>
        </article>
      `;
    })
  );

  renderStack(
    "audit-logs",
    auditLogs.map(
      (item) => `
        <article class="list-item list-item--vertical">
          <div>
            <strong>${item.action}</strong>
            <p>${item.target_type} #${item.target_id ?? "N/A"} | Actor ${item.actor_user_id ?? "system"}</p>
            <p>${formatDate(item.created_at)}</p>
            <pre>${JSON.stringify(item.details || {}, null, 2)}</pre>
          </div>
        </article>
      `
    )
  );
}

function updateVisibility() {
  const flags = roleFlags();
  elements.authPanel.hidden = Boolean(state.currentUser);
  elements.dashboard.hidden = !state.currentUser;
  elements.operatorPanel.hidden = !flags.staff;
  elements.technicianPanel.hidden = !flags.technician;
  elements.adminPanel.hidden = !flags.admin;

  if (state.currentUser) {
    elements.sessionName.textContent = `${state.currentUser.first_name} ${state.currentUser.last_name}`;
    elements.sessionMeta.textContent = `${state.currentUser.email} | ${state.currentUser.role_name} | Client ${state.clientIp}`;
  }
}

async function refreshDashboard() {
  if (!state.currentUser) {
    updateVisibility();
    return;
  }

  setFlash("Refreshing workspace...", "busy");
  updateVisibility();

  const commonResults = await Promise.all([
    api("/labs"),
    api("/equipments"),
    api("/reservations/my"),
    api("/borrowings/my"),
    api("/penalties/my"),
    api("/notifications/my"),
  ]);

  const common = {
    labs: commonResults[0],
    equipments: commonResults[1],
    reservations: commonResults[2],
    borrowings: commonResults[3],
    penalties: commonResults[4],
    notifications: commonResults[5],
  };

  const flags = roleFlags();
  let staffSummary = null;
  if (flags.staff) {
    const [summary, staffUsers, activeBorrowings] = await Promise.all([
      api("/staff/reports/summary"),
      api("/staff/users"),
      api("/borrowings?status_filter=Borrowed"),
    ]);
    staffSummary = summary;
    renderStaff(summary, staffUsers, activeBorrowings);
  }

  if (flags.technician) {
    const queue = await api("/maintenance/queue");
    renderMaintenance(queue);
  }

  if (flags.admin) {
    const [adminUsers, roles, auditLogs] = await Promise.all([
      api("/admin/users"),
      api("/admin/roles"),
      api("/admin/audit-logs"),
    ]);
    state.roles = roles;
    renderAdmin(adminUsers, auditLogs);
  } else {
    state.roles = [];
  }

  renderCommon(common);
  renderOverview(common, staffSummary);
  setFlash("Workspace synced.", "success");
}

function bindSubmit(form, buildPayload, request) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      setFlash("Submitting...", "busy");
      await api(request.path, { method: request.method, body: buildPayload(new FormData(form)) });
      form.reset();
      await loadCurrentUser();
      await refreshDashboard();
    } catch (error) {
      setFlash(error.message, "error");
    }
  });
}

bindSubmit(
  elements.loginForm,
  (formData) => ({ email: formData.get("email"), password: formData.get("password") }),
  { path: "/auth/login", method: "POST" }
);

bindSubmit(
  elements.registerForm,
  (formData) => ({
    first_name: formData.get("first_name"),
    last_name: formData.get("last_name"),
    email: formData.get("email"),
    password: formData.get("password"),
  }),
  { path: "/auth/register", method: "POST" }
);

bindSubmit(
  elements.reservationForm,
  (formData) => ({
    lab_id: Number(formData.get("lab_id")),
    start_time: toIso(formData.get("start_time")),
    end_time: toIso(formData.get("end_time")),
  }),
  { path: "/reservations", method: "POST" }
);

bindSubmit(
  elements.maintenanceForm,
  (formData) => ({
    equipment_id: Number(formData.get("equipment_id")),
    issue_detail: formData.get("issue_detail"),
  }),
  { path: "/maintenance", method: "POST" }
);

bindSubmit(
  elements.borrowingForm,
  (formData) => ({
    user_id: Number(formData.get("user_id")),
    equipment_id: Number(formData.get("equipment_id")),
    expected_return: toIso(formData.get("expected_return")),
  }),
  { path: "/borrowings", method: "POST" }
);

bindSubmit(
  elements.labForm,
  (formData) => ({
    room_name: formData.get("room_name"),
    capacity: Number(formData.get("capacity")),
    status: formData.get("status"),
  }),
  { path: "/admin/labs", method: "POST" }
);

bindSubmit(
  elements.equipmentForm,
  (formData) => ({
    equipment_name: formData.get("equipment_name"),
    lab_id: formData.get("lab_id") ? Number(formData.get("lab_id")) : null,
    category_id: formData.get("category_id") ? Number(formData.get("category_id")) : null,
    status: formData.get("status"),
  }),
  { path: "/admin/equipments", method: "POST" }
);

elements.refreshButton.addEventListener("click", async () => {
  try {
    await loadCurrentUser();
    await refreshDashboard();
  } catch (error) {
    setFlash(error.message, "error");
  }
});

elements.logoutButton.addEventListener("click", async () => {
  try {
    await api("/auth/logout", { method: "POST" });
    state.currentUser = null;
    state.csrfToken = null;
    state.roles = [];
    updateVisibility();
    setFlash("Logged out.", "success");
  } catch (error) {
    setFlash(error.message, "error");
  }
});

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  try {
    const action = button.dataset.action;
    if (action === "cancel-reservation") {
      await api(`/reservations/${button.dataset.id}/cancel`, { method: "POST" });
    }
    if (action === "return-borrowing") {
      await api(`/borrowings/${button.dataset.id}/return`, { method: "PATCH" });
    }
    if (action === "maintenance-status") {
      await api(`/maintenance/${button.dataset.id}`, {
        method: "PATCH",
        body: { status: button.dataset.status },
      });
    }
    if (action === "update-role") {
      const select = document.querySelector(`[data-role-user="${button.dataset.id}"]`);
      await api(`/admin/users/${button.dataset.id}/role`, {
        method: "PATCH",
        body: { role_name: select.value },
      });
    }
    await loadCurrentUser();
    await refreshDashboard();
  } catch (error) {
    setFlash(error.message, "error");
  }
});

// ---------------------------------------------------------------------------
// Advanced Reports
// ---------------------------------------------------------------------------

const REPORT_COLUMNS = {
  "late-borrowings": [
    { key: "borrow_id",       label: "#" },
    { key: "borrower_name",   label: "Borrower" },
    { key: "equipment_name",  label: "Equipment" },
    { key: "lab_name",        label: "Lab" },
    { key: "expected_return", label: "Due",        fmt: formatDate },
    { key: "actual_return",   label: "Returned",   fmt: formatDate },
    { key: "hours_late",      label: "Hours Late" },
    { key: "fine_amount",     label: "Fine (THB)",
      fmt: (v) => v != null ? Number(v).toFixed(2) : "—" },
    { key: "status",          label: "Status" },
  ],
  "top-borrowers": [
    { key: "user_id",          label: "#" },
    { key: "full_name",        label: "Name" },
    { key: "email",            label: "Email" },
    { key: "role_name",        label: "Role" },
    { key: "total_borrowings", label: "Borrowings" },
    { key: "penalty_count",    label: "Penalties" },
    { key: "total_fines",      label: "Total Fines (THB)",
      fmt: (v) => Number(v).toFixed(2) },
  ],
  "lab-utilization": [
    { key: "room_name",             label: "Lab" },
    { key: "lab_type",              label: "Type" },
    { key: "capacity",              label: "Capacity" },
    { key: "status",                label: "Status" },
    { key: "total_reservations",    label: "Total Reservations" },
    { key: "approved_reservations", label: "Approved" },
    { key: "equipment_count",       label: "Equipment Items" },
  ],
  "equipment-repairs": [
    { key: "equipment_id",   label: "#" },
    { key: "equipment_name", label: "Equipment" },
    { key: "category_name",  label: "Category" },
    { key: "lab_name",       label: "Lab" },
    { key: "current_status", label: "Status" },
    { key: "repair_count",   label: "Total Repairs" },
    { key: "open_repairs",   label: "Open Repairs" },
    { key: "last_reported",  label: "Last Reported", fmt: formatDate },
  ],
  "reservation-summary": [
    { key: "reservation_id",    label: "#" },
    { key: "room_name",         label: "Lab" },
    { key: "reserved_by_name",  label: "Booked By" },
    { key: "start_time",        label: "Start",    fmt: formatDate },
    { key: "end_time",          label: "End",      fmt: formatDate },
    { key: "duration_hours",    label: "Hours" },
    { key: "participant_count", label: "Participants" },
    { key: "status",            label: "Status" },
  ],
};

const REPORT_TITLES = {
  "late-borrowings":    "Q1 — Late Borrowings (5-table JOIN)",
  "top-borrowers":      "Q2 — Top Borrowers (GROUP BY + HAVING)",
  "lab-utilization":    "Q3 — Lab Utilisation (GROUP BY + CASE)",
  "equipment-repairs":  "Q4 — Equipment Repair Frequency (GROUP BY + MAX)",
  "reservation-summary":"Q5 — Reservation Summary (GROUP BY + EXTRACT)",
};

function renderReportTable(reportKey, rows) {
  const output = document.getElementById("report-output");
  if (!output) return;

  const cols = REPORT_COLUMNS[reportKey] || [];
  const title = REPORT_TITLES[reportKey] || reportKey;

  if (!rows.length) {
    output.innerHTML = `<p class="empty-state"><strong>${title}</strong> — No data found.</p>`;
    return;
  }

  const headerCells = cols.map((c) => `<th>${c.label}</th>`).join("");
  const bodyRows = rows
    .map((row) => {
      const cells = cols
        .map((c) => {
          const raw = row[c.key];
          const display = c.fmt ? c.fmt(raw) : (raw ?? "—");
          return `<td>${display}</td>`;
        })
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  output.innerHTML = `
    <p class="report-title"><strong>${title}</strong> — ${rows.length} row(s)</p>
    <div class="table-wrap">
      <table class="report-table">
        <thead><tr>${headerCells}</tr></thead>
        <tbody>${bodyRows}</tbody>
      </table>
    </div>
  `;
}

document.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-report]");
  if (!btn) return;
  const reportKey = btn.dataset.report;
  try {
    setFlash(`Loading report: ${REPORT_TITLES[reportKey] || reportKey}…`, "busy");
    const rows = await api(`/reports/${reportKey}`);
    renderReportTable(reportKey, rows);
    setFlash("Report loaded.", "success");
  } catch (error) {
    setFlash(error.message, "error");
  }
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

async function boot() {
  await loadCurrentUser();
  updateVisibility();
  if (state.currentUser) {
    await refreshDashboard();
  } else {
    setFlash("Login or register to begin.", "idle");
  }
}

boot().catch((error) => {
  setFlash(error.message, "error");
});
