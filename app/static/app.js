const body = document.body;
const state = {
  appName: body.dataset.appName,
  clientIp: body.dataset.clientIp,
  csrfToken: null,
  currentUser: null,
  roles: [],
  reservationAvailability: null,
};

const BOOKING_TIMEZONE = "Asia/Bangkok";
const FIXED_SLOT_DEFS = {
  morning: { label: "08:00-12:00", start: "08:00:00", end: "12:00:00" },
  afternoon: { label: "12:00-16:00", start: "12:00:00", end: "16:00:00" },
  evening: { label: "16:00-20:00", start: "16:00:00", end: "20:00:00" },
};
const LAB_STATUSES = ["Available", "Reserved", "Maintenance", "Closed"];
const EQUIPMENT_STATUSES = ["Available", "Borrowed", "In_Repair"];
const RESERVATION_STATUSES = ["Pending", "Approved", "Cancelled"];
const EMPTY_MESSAGES = {
  "labs-list": "ยังไม่มีห้องที่พร้อมใช้งาน",
  "equipment-list": "ยังไม่มีอุปกรณ์ที่พร้อมใช้งาน",
  "my-reservations": "ยังไม่มีรายการจอง",
  "my-borrowings": "ยังไม่มีรายการยืม",
  "my-penalties": "ยังไม่มีค่าปรับ",
  "my-notifications": "ยังไม่มีการแจ้งเตือน",
  "active-borrowings": "ยังไม่มีรายการยืมที่กำลังใช้งาน",
  "maintenance-queue": "ยังไม่มีคิวงานซ่อม",
  "admin-labs": "ยังไม่มีข้อมูลห้อง",
  "admin-equipments": "ยังไม่มีข้อมูลอุปกรณ์",
  "admin-reservations": "ยังไม่มีรายการจอง",
  "admin-users": "ยังไม่มีข้อมูลผู้ใช้",
  "audit-logs": "ยังไม่มี audit log",
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
  reservationDate: document.getElementById("reservation-date"),
  maintenanceForm: document.getElementById("maintenance-form"),
  borrowingForm: document.getElementById("borrowing-form"),
  labForm: document.getElementById("lab-form"),
  equipmentForm: document.getElementById("equipment-form"),
  reservationLab: document.getElementById("reservation-lab"),
  reservationSlot: document.getElementById("reservation-slot"),
  reservationSlotOptions: document.getElementById("reservation-slot-options"),
  reservationSelection: document.getElementById("reservation-selection"),
  reservationSchedule: document.getElementById("reservation-schedule"),
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
  return new Intl.DateTimeFormat("th-TH", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: BOOKING_TIMEZONE,
  }).format(new Date(value));
}

function formatRole(roleName) {
  return roleName ? roleName.toUpperCase() : "GUEST";
}

function statusTone(status) {
  if (["Available", "Approved", "Returned", "Resolved", "Fixed"].includes(status)) return "success";
  if (["Pending", "Reserved", "Borrowed", "Reported", "In Progress"].includes(status)) return "warn";
  if (["Cancelled", "Closed", "Maintenance", "In_Repair"].includes(status)) return "danger";
  return "muted";
}

function statusBadge(status, label = status) {
  return `<span class="status-pill status-pill--${statusTone(status)}">${label}</span>`;
}

function toIso(localValue) {
  return new Date(localValue).toISOString();
}

function todayInBookingTimezone() {
  return new Intl.DateTimeFormat("sv-SE", {
    timeZone: BOOKING_TIMEZONE,
  }).format(new Date());
}

function fixedSlotToIso(dateValue, slotKey, edge) {
  const slot = FIXED_SLOT_DEFS[slotKey];
  if (!slot || !dateValue) return null;
  const timeValue = edge === "start" ? slot.start : slot.end;
  return new Date(`${dateValue}T${timeValue}+07:00`).toISOString();
}

function formatBookingDate(dateValue) {
  return new Intl.DateTimeFormat("th-TH", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: BOOKING_TIMEZONE,
  }).format(new Date(`${dateValue}T00:00:00+07:00`));
}

async function loadReservationAvailability() {
  const dateValue = elements.reservationDate.value || todayInBookingTimezone();
  if (!elements.reservationDate.value) {
    elements.reservationDate.value = dateValue;
  }

  const availability = await api(`/reservations/availability?booking_date=${dateValue}`);
  state.reservationAvailability = availability;

  const selectedLabStillExists = availability.labs.some((lab) => lab.lab_id === Number(elements.reservationLab.value));
  if (!selectedLabStillExists && availability.labs.length) {
    elements.reservationLab.value = String(availability.labs[0].lab_id);
  }

  const selectedLab = availability.labs.find((lab) => lab.lab_id === Number(elements.reservationLab.value));
  const selectedSlot = selectedLab?.slots.find((slot) => slot.slot_key === elements.reservationSlot.value && slot.is_available);
  if (!selectedSlot) {
    const firstAvailableSlot = selectedLab?.slots.find((slot) => slot.is_available);
    elements.reservationSlot.value = firstAvailableSlot?.slot_key || "";
  }

  renderReservationSlotOptions();
  renderReservationSelection();
  renderReservationSchedule();
}

function renderReservationSelection() {
  const dateValue = elements.reservationDate.value;
  const labId = Number(elements.reservationLab.value);
  const slotKey = elements.reservationSlot.value;
  const availability = state.reservationAvailability;
  const selectedLab = availability?.labs.find((lab) => lab.lab_id === labId);
  const selectedSlot = selectedLab?.slots.find((slot) => slot.slot_key === slotKey && slot.is_available);

  if (!dateValue || !selectedLab || !selectedSlot) {
    elements.reservationSelection.innerHTML = `
      <strong>ยังไม่ได้เลือกรอบเวลา</strong>
      <p>เลือกวันที่ ห้อง และรอบเวลาที่ต้องการก่อนยืนยันการจอง</p>
    `;
    return;
  }

  elements.reservationSelection.innerHTML = `
    <strong>${selectedLab.room_name}</strong>
    <p>${formatBookingDate(dateValue)} | รอบ ${selectedSlot.label}</p>
  `;
}

function renderReservationSlotOptions() {
  const availability = state.reservationAvailability;
  const selectedLab = availability?.labs.find((lab) => lab.lab_id === Number(elements.reservationLab.value));

  if (!selectedLab) {
    elements.reservationSlotOptions.innerHTML = '<div class="empty-state">ยังไม่มีรอบเวลาให้เลือก</div>';
    return;
  }

  elements.reservationSlotOptions.innerHTML = selectedLab.slots
    .map((slot) => {
      const isSelected = elements.reservationSlot.value === slot.slot_key;
      const tone = !slot.is_available && selectedLab.status !== "Available"
        ? "unavailable"
        : isSelected
          ? "selected"
          : slot.is_available
            ? "available"
            : "busy";
      const helper =
        tone === "unavailable"
          ? "ห้องไม่พร้อมใช้งาน"
          : tone === "busy"
            ? "รอบนี้ถูกจองแล้ว"
            : isSelected
              ? "เลือกรอบนี้แล้ว"
              : "กดเพื่อเลือกรอบ";
      const disabled = tone === "busy" || tone === "unavailable" ? "disabled" : "";

      return `
        <button
          type="button"
          class="slot-option-button slot-option-button--${tone}"
          data-slot-select="${slot.slot_key}"
          data-lab-id="${selectedLab.lab_id}"
          ${disabled}
        >
          <strong>${slot.label}</strong>
          <small>${helper}</small>
        </button>
      `;
    })
    .join("");
}

function renderReservationSchedule() {
  const availability = state.reservationAvailability;
  if (!availability) {
    elements.reservationSchedule.innerHTML = '<div class="empty-state">กำลังโหลดตารางการจอง...</div>';
    return;
  }

  if (!availability.labs.length) {
    elements.reservationSchedule.innerHTML = '<div class="empty-state">ยังไม่มีห้องในระบบ</div>';
    return;
  }

  const header = availability.slots.map((slot) => `<th>${slot.label}</th>`).join("");
  const bodyRows = availability.labs
    .map((lab) => {
      const slotCells = lab.slots
        .map((slot) => {
          const isSelected =
            Number(elements.reservationLab.value) === lab.lab_id && elements.reservationSlot.value === slot.slot_key;
          const tone = !slot.is_available && lab.status !== "Available"
            ? "unavailable"
            : isSelected
              ? "selected"
              : slot.is_available
                ? "available"
                : "busy";
          const label =
            tone === "unavailable"
              ? "ห้องไม่พร้อม"
              : tone === "busy"
                ? "จองแล้ว"
                : isSelected
                  ? "เลือกรอบนี้แล้ว"
                  : "กดเพื่อเลือก";
          const disabled = tone === "busy" || tone === "unavailable" ? "disabled" : "";

          return `
            <td>
              <button
                type="button"
                class="slot-button slot-button--${tone}"
                data-slot-select="${slot.slot_key}"
                data-lab-id="${lab.lab_id}"
                ${disabled}
              >
                <strong>${slot.label}</strong>
                <small>${label}</small>
              </button>
            </td>
          `;
        })
        .join("");

      return `
        <tr>
          <td class="lab-cell">
            <strong>${lab.room_name}</strong>
            <div class="lab-meta">ความจุ ${lab.capacity} คน | ${lab.status}</div>
          </td>
          ${slotCells}
        </tr>
      `;
    })
    .join("");

  elements.reservationSchedule.innerHTML = `
    <div class="schedule-table">
      <table>
        <thead>
          <tr>
            <th>ห้อง</th>
            ${header}
          </tr>
        </thead>
        <tbody>${bodyRows}</tbody>
      </table>
    </div>
  `;
}

function renderStack(containerId, entries) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = entries.length
    ? entries.join("")
    : `<div class="empty-state">${EMPTY_MESSAGES[containerId] || "ยังไม่มีข้อมูล"}</div>`;
}

function setCount(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = String(value);
}

function optionMarkup(value, label, selected = false) {
  return `<option value="${value}"${selected ? " selected" : ""}>${label}</option>`;
}

function statusOptions(statuses, selectedValue) {
  return statuses.map((status) => optionMarkup(status, status, status === selectedValue)).join("");
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

function updateVisibility() {
  const flags = roleFlags();
  elements.authPanel.hidden = Boolean(state.currentUser);
  elements.dashboard.hidden = !state.currentUser;
  elements.operatorPanel.hidden = !flags.staff;
  elements.technicianPanel.hidden = !flags.technician;
  elements.adminPanel.hidden = !flags.admin;

  const navOperator = document.querySelector('.quick-nav__item[href="#operator-panel"]');
  const navTechnician = document.querySelector('.quick-nav__item[href="#technician-panel"]');
  const navAdmin = document.querySelector('.quick-nav__item[href="#admin-panel"]');
  if (navOperator) navOperator.hidden = !flags.staff;
  if (navTechnician) navTechnician.hidden = !flags.technician;
  if (navAdmin) navAdmin.hidden = !flags.admin;

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

  setFlash("กำลังรีเฟรชข้อมูล...", "busy");
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
    const [adminLabs, adminEquipments, adminReservations, adminUsers, roles, auditLogs] = await Promise.all([
      api("/admin/labs"),
      api("/admin/equipments"),
      api("/reservations"),
      api("/admin/users"),
      api("/admin/roles"),
      api("/admin/audit-logs"),
    ]);
    state.roles = roles;
    renderCommon(common);
    renderAdmin(adminLabs, adminEquipments, adminReservations, adminUsers, auditLogs);
  } else {
    state.roles = [];
    renderCommon(common);
  }
  await loadReservationAvailability();
  renderOverview(common, staffSummary);
  setFlash("อัปเดตข้อมูลล่าสุดแล้ว", "success");
}

function goToDashboard() {
  if (!state.currentUser || !elements.dashboard) return;
  updateVisibility();
  requestAnimationFrame(() => {
    elements.dashboard.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function bindSubmit(form, buildPayload, request, options = {}) {
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      setFlash("กำลังบันทึกข้อมูล...", "busy");
      await api(request.path, { method: request.method, body: buildPayload(new FormData(form)) });
      form.reset();
      await loadCurrentUser();
      if (options.afterLoadCurrentUser) {
        await options.afterLoadCurrentUser();
      }
      await refreshDashboard();
      if (options.afterSuccess) {
        await options.afterSuccess();
      }
    } catch (error) {
      setFlash(error.message, "error");
    }
  });
}

bindSubmit(
  elements.loginForm,
  (formData) => ({ email: formData.get("email"), password: formData.get("password") }),
  { path: "/auth/login", method: "POST" },
  {
    afterLoadCurrentUser: () => {
      if (!state.currentUser) {
        throw new Error("Login completed but session was not created");
      }
    },
    afterSuccess: () => {
      goToDashboard();
      setFlash("เข้าสู่ระบบเรียบร้อยแล้ว", "success");
    },
  }
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
  (formData) => {
    const reservationDate = formData.get("reservation_date");
    const slotKey = formData.get("slot_key");
    if (!reservationDate || !slotKey) {
      throw new Error("กรุณาเลือกวันที่และรอบเวลาที่ต้องการจอง");
    }

    return {
      lab_id: Number(formData.get("lab_id")),
      start_time: fixedSlotToIso(reservationDate, slotKey, "start"),
      end_time: fixedSlotToIso(reservationDate, slotKey, "end"),
    };
  },
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
    setFlash("ออกจากระบบแล้ว", "success");
  } catch (error) {
    setFlash(error.message, "error");
  }
});

document.addEventListener("click", async (event) => {
  const slotButton = event.target.closest("[data-slot-select]");
  if (slotButton) {
    elements.reservationLab.value = slotButton.dataset.labId;
    elements.reservationSlot.value = slotButton.dataset.slotSelect;
    renderReservationSlotOptions();
    renderReservationSelection();
    renderReservationSchedule();
    return;
  }

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
    if (action === "toggle-user-status") {
      await api(`/admin/users/${button.dataset.id}/status`, {
        method: "PATCH",
        body: { is_active: button.dataset.active !== "true" },
      });
    }
    if (action === "mark-notification-read") {
      await api(`/notifications/${button.dataset.id}`, {
        method: "PATCH",
        body: { is_read: true },
      });
    }
    if (action === "update-lab") {
      const roomInput = document.querySelector(`[data-lab-room="${button.dataset.id}"]`);
      const capacityInput = document.querySelector(`[data-lab-capacity="${button.dataset.id}"]`);
      const statusInput = document.querySelector(`[data-lab-status="${button.dataset.id}"]`);
      await api(`/admin/labs/${button.dataset.id}`, {
        method: "PATCH",
        body: {
          room_name: roomInput.value,
          capacity: Number(capacityInput.value),
          status: statusInput.value,
        },
      });
    }
    if (action === "delete-lab") {
      await api(`/admin/labs/${button.dataset.id}`, { method: "DELETE" });
    }
    if (action === "update-equipment") {
      const nameInput = document.querySelector(`[data-equipment-name="${button.dataset.id}"]`);
      const labSelect = document.querySelector(`[data-equipment-lab="${button.dataset.id}"]`);
      const categoryInput = document.querySelector(`[data-equipment-category="${button.dataset.id}"]`);
      const statusInput = document.querySelector(`[data-equipment-status="${button.dataset.id}"]`);
      await api(`/admin/equipments/${button.dataset.id}`, {
        method: "PATCH",
        body: {
          equipment_name: nameInput.value,
          lab_id: labSelect.value ? Number(labSelect.value) : null,
          category_id: categoryInput.value ? Number(categoryInput.value) : null,
          status: statusInput.value,
        },
      });
    }
    if (action === "delete-equipment") {
      await api(`/admin/equipments/${button.dataset.id}`, { method: "DELETE" });
    }
    if (action === "update-reservation-status") {
      const statusInput = document.querySelector(`[data-reservation-status="${button.dataset.id}"]`);
      await api(`/reservations/${button.dataset.id}`, {
        method: "PATCH",
        body: { status: statusInput.value },
      });
    }
    if (action === "delete-reservation") {
      await api(`/reservations/${button.dataset.id}`, { method: "DELETE" });
    }
    await loadCurrentUser();
    await refreshDashboard();
  } catch (error) {
    setFlash(error.message, "error");
  }
});

elements.reservationDate.addEventListener("change", async () => {
  if (!state.currentUser) return;

  try {
    setFlash("กำลังอัปเดตตารางการจอง...", "busy");
    elements.reservationSlot.value = "";
    await loadReservationAvailability();
    setFlash("อัปเดตตารางการจองแล้ว", "success");
  } catch (error) {
    setFlash(error.message, "error");
  }
});

elements.reservationLab.addEventListener("change", () => {
  const selectedLab = state.reservationAvailability?.labs.find((lab) => lab.lab_id === Number(elements.reservationLab.value));
  const selectedSlot = selectedLab?.slots.find((slot) => slot.slot_key === elements.reservationSlot.value && slot.is_available);
  if (!selectedSlot) {
    elements.reservationSlot.value = selectedLab?.slots.find((slot) => slot.is_available)?.slot_key || "";
  }
  renderReservationSlotOptions();
  renderReservationSelection();
  renderReservationSchedule();
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

document.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-report]");
  if (!btn) return;
  const reportKey = btn.dataset.report;
  try {
    setFlash(`Loading report: ${REPORT_TITLES[reportKey] || reportKey}…`, "busy");
    const rows = await api(`/reports/${reportKey}`);
    renderReportTable(reportKey, rows);
    setFlash("โหลดรายงานเรียบร้อยแล้ว", "success");
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
    setFlash("เข้าสู่ระบบหรือสมัครสมาชิกเพื่อเริ่มใช้งาน", "idle");
  }
}

boot().catch((error) => {
  setFlash(error.message, "error");
});

function reportTitleV2(reportKey) {
  const titles = {
    "late-borrowings": "รายการยืมล่าช้า",
    "top-borrowers": "ผู้ยืมสูงสุด",
    "lab-utilization": "ภาพรวมการใช้งานห้อง",
    "equipment-repairs": "สถิติการซ่อมอุปกรณ์",
    "reservation-summary": "สรุปรายการจอง",
  };
  return titles[reportKey] || reportKey;
}

function maintenanceActionLabelV2(status) {
  if (status === "Reported") return "รับเรื่อง";
  if (status === "In Progress") return "กำลังซ่อม";
  if (status === "Fixed") return "ซ่อมเสร็จ";
  return status;
}

function renderOverview(common, staffSummary) {
  const cards = [
    { label: "Role", value: formatRole(state.currentUser.role_name) },
    { label: "รายการจองที่ยังใช้งาน", value: common.reservations.filter((item) => item.status !== "Cancelled").length },
    { label: "อุปกรณ์ที่กำลังถูกยืม", value: common.borrowings.filter((item) => item.status === "Borrowed").length },
    { label: "การแจ้งเตือนที่ยังไม่อ่าน", value: common.notifications.filter((item) => !item.is_read).length },
  ];

  if (staffSummary) {
    cards.push(
      { label: "ผู้ใช้ทั้งหมด", value: staffSummary.total_users },
      { label: "งานซ่อมที่ยังเปิด", value: staffSummary.active_repairs }
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
  const labNameById = new Map(common.labs.map((lab) => [lab.lab_id, lab.room_name]));
  const equipmentNameById = new Map(common.equipments.map((item) => [item.equipment_id, item.equipment_name]));

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
            <div class="list-item__meta">
              ${statusBadge(lab.status)}
              <p>ความจุ ${lab.capacity} คน</p>
            </div>
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
            <div class="list-item__meta">
              ${statusBadge(item.status)}
              <p>${item.lab_id ? `อยู่ที่ ${labNameById.get(item.lab_id) || `ห้อง #${item.lab_id}`}` : "ยังไม่ได้ระบุห้อง"}</p>
            </div>
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
            <strong>รายการจอง #${item.reservation_id}</strong>
            <p>${labNameById.get(item.lab_id) || `ห้อง #${item.lab_id}`}</p>
            <p>${formatDate(item.start_time)} ถึง ${formatDate(item.end_time)}</p>
            <div class="list-item__meta">${statusBadge(item.status)}</div>
          </div>
          ${item.status !== "Cancelled" ? `<button class="inline-action" data-action="cancel-reservation" data-id="${item.reservation_id}">ยกเลิก</button>` : ""}
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
            <strong>รายการยืม #${item.borrow_id}</strong>
            <p>${equipmentNameById.get(item.equipment_id) || `อุปกรณ์ #${item.equipment_id}`}</p>
            <p>กำหนดคืน ${formatDate(item.expected_return)}</p>
            <div class="list-item__meta">${statusBadge(item.status)}</div>
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
            <strong>ค่าปรับ #${item.penalty_id}</strong>
            <p>รายการยืม #${item.borrow_id} | ${Number(item.fine_amount).toFixed(2)} THB</p>
            <div class="list-item__meta">${statusBadge(item.is_resolved ? "Resolved" : "Pending", item.is_resolved ? "ชำระแล้ว" : "ค้างชำระ")}</div>
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
            <strong>${item.is_read ? "อ่านแล้ว" : "ยังไม่อ่าน"}</strong>
            <p>${item.message}</p>
            <p>${formatDate(item.created_at)}</p>
          </div>
          ${!item.is_read ? `<button class="inline-action" data-action="mark-notification-read" data-id="${item.notification_id}">ทำเครื่องหมายว่าอ่านแล้ว</button>` : ""}
        </article>
      `
    )
  );

  elements.reservationLab.innerHTML = common.labs.length
    ? common.labs.map((lab, index) => optionMarkup(lab.lab_id, `${lab.room_name} (${lab.capacity})`, index === 0)).join("")
    : optionMarkup("", "ไม่มีห้องที่พร้อมใช้งาน", true);

  const availableEquipment = common.equipments.filter((item) => item.status === "Available");
  const equipmentOptions = availableEquipment.length
    ? availableEquipment.map((item, index) => optionMarkup(item.equipment_id, `${item.equipment_name} (#${item.equipment_id})`, index === 0)).join("")
    : optionMarkup("", "ไม่มีอุปกรณ์ที่พร้อมใช้งาน", true);

  elements.maintenanceEquipment.innerHTML = equipmentOptions;
  elements.borrowingEquipment.innerHTML = equipmentOptions;
  elements.adminEquipmentLab.innerHTML =
    optionMarkup("", "ยังไม่ได้กำหนดห้อง", true) +
    common.labs.map((lab) => optionMarkup(lab.lab_id, lab.room_name)).join("");
}

function renderStaff(staffSummary, staffUsers, borrowings) {
  document.getElementById("staff-summary").innerHTML = `
    <div class="metric-row"><span>ผู้ใช้ทั้งหมด</span><strong>${staffSummary.total_users}</strong></div>
    <div class="metric-row"><span>ห้องทั้งหมด</span><strong>${staffSummary.total_labs}</strong></div>
    <div class="metric-row"><span>อุปกรณ์ทั้งหมด</span><strong>${staffSummary.total_equipments}</strong></div>
    <div class="metric-row"><span>รายการยืมที่ยังเปิด</span><strong>${staffSummary.active_borrowings}</strong></div>
    <div class="metric-row"><span>งานซ่อมที่ยังเปิด</span><strong>${staffSummary.active_repairs}</strong></div>
  `;

  elements.borrowingUser.innerHTML = staffUsers.length
    ? staffUsers.map((user, index) => optionMarkup(user.user_id, `${user.first_name} ${user.last_name} (${user.role_name})`, index === 0)).join("")
    : optionMarkup("", "ไม่มีผู้ใช้", true);

  setCount("active-borrowings-count", borrowings.length);
  renderStack(
    "active-borrowings",
    borrowings.map(
      (item) => `
        <article class="list-item">
          <div>
            <strong>รายการยืม #${item.borrow_id}</strong>
            <p>ผู้ใช้ #${item.user_id} | อุปกรณ์ #${item.equipment_id}</p>
            <p>กำหนดคืน ${formatDate(item.expected_return)}</p>
            <div class="list-item__meta">${statusBadge(item.status)}</div>
          </div>
          ${item.status === "Borrowed" ? `<button class="inline-action" data-action="return-borrowing" data-id="${item.borrow_id}">รับคืน</button>` : ""}
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
            <strong>งานซ่อม #${item.repair_id}</strong>
            <p>อุปกรณ์ #${item.equipment_id} | ผู้แจ้ง #${item.reported_by}</p>
            <p>${item.issue_detail}</p>
            <div class="list-item__meta">${statusBadge(item.status)}</div>
          </div>
          <div class="action-cluster">
            ${statuses
              .map(
                (status) =>
                  `<button class="inline-action" data-action="maintenance-status" data-id="${item.repair_id}" data-status="${status}">${maintenanceActionLabelV2(status)}</button>`
              )
              .join("")}
          </div>
        </article>
      `
    )
  );
}

function renderAdmin(labs, equipments, reservations, users, auditLogs) {
  const allLabOptions =
    optionMarkup("", "ยังไม่ได้ระบุห้อง", true) +
    labs.map((lab) => optionMarkup(lab.lab_id, lab.room_name)).join("");

  elements.adminEquipmentLab.innerHTML = allLabOptions;
  setCount("admin-labs-count", labs.length);
  setCount("admin-equipments-count", equipments.length);
  setCount("admin-reservations-count", reservations.length);
  setCount("admin-users-count", users.length);
  setCount("audit-count", auditLogs.length);

  renderStack(
    "admin-labs",
    labs.map(
      (lab) => `
        <article class="list-item list-item--vertical">
          <div>
            <strong>${lab.room_name}</strong>
            <p>ความจุ ${lab.capacity} คน | ${lab.status}</p>
          </div>
          <div class="action-cluster">
            <input class="inline-input" data-lab-room="${lab.lab_id}" value="${lab.room_name}">
            <input class="inline-input inline-input--small" data-lab-capacity="${lab.lab_id}" type="number" min="1" value="${lab.capacity}">
            <select class="inline-select" data-lab-status="${lab.lab_id}">
              ${statusOptions(LAB_STATUSES, lab.status)}
            </select>
            <button class="inline-action" data-action="update-lab" data-id="${lab.lab_id}">บันทึก</button>
            <button class="button-ghost" data-action="delete-lab" data-id="${lab.lab_id}">ลบ</button>
          </div>
        </article>
      `
    )
  );

  renderStack(
    "admin-equipments",
    equipments.map(
      (equipment) => `
        <article class="list-item list-item--vertical">
          <div>
            <strong>${equipment.equipment_name}</strong>
            <p>ห้อง ${equipment.lab_id ?? "ยังไม่ได้ระบุ"} | Category ${equipment.category_id ?? "ยังไม่ได้ระบุ"} | ${equipment.status}</p>
          </div>
          <div class="action-cluster">
            <input class="inline-input" data-equipment-name="${equipment.equipment_id}" value="${equipment.equipment_name}">
            <select class="inline-select" data-equipment-lab="${equipment.equipment_id}">
              ${allLabOptions}
            </select>
            <input class="inline-input inline-input--small" data-equipment-category="${equipment.equipment_id}" type="number" min="1" value="${equipment.category_id ?? ""}" placeholder="Category">
            <select class="inline-select" data-equipment-status="${equipment.equipment_id}">
              ${statusOptions(EQUIPMENT_STATUSES, equipment.status)}
            </select>
            <button class="inline-action" data-action="update-equipment" data-id="${equipment.equipment_id}">บันทึก</button>
            <button class="button-ghost" data-action="delete-equipment" data-id="${equipment.equipment_id}">ลบ</button>
          </div>
        </article>
      `
    )
  );

  equipments.forEach((equipment) => {
    const select = document.querySelector(`[data-equipment-lab="${equipment.equipment_id}"]`);
    if (select) select.value = equipment.lab_id == null ? "" : String(equipment.lab_id);
  });

  renderStack(
    "admin-reservations",
    reservations.map(
      (reservation) => `
        <article class="list-item list-item--vertical">
          <div>
            <strong>รายการจอง #${reservation.reservation_id}</strong>
            <p>ห้อง ${reservation.lab_id} | ผู้จอง ${reservation.reserved_by}</p>
            <p>${formatDate(reservation.start_time)} ถึง ${formatDate(reservation.end_time)}</p>
          </div>
          <div class="action-cluster">
            <select class="inline-select" data-reservation-status="${reservation.reservation_id}">
              ${statusOptions(RESERVATION_STATUSES, reservation.status)}
            </select>
            <button class="inline-action" data-action="update-reservation-status" data-id="${reservation.reservation_id}">บันทึก</button>
            <button class="button-ghost" data-action="delete-reservation" data-id="${reservation.reservation_id}">ลบ</button>
          </div>
        </article>
      `
    )
  );

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
            <p>สิทธิ์ปัจจุบัน ${user.role_name}</p>
          </div>
          <div class="action-cluster">
            <select class="inline-select" data-role-user="${user.user_id}">
              ${options}
            </select>
            <button class="inline-action" data-action="update-role" data-id="${user.user_id}">อัปเดตสิทธิ์</button>
            <button class="button-ghost" data-action="toggle-user-status" data-id="${user.user_id}" data-active="${user.is_active}">
              ${user.is_active ? "ปิดการใช้งาน" : "เปิดการใช้งาน"}
            </button>
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
            <p>${item.target_type} #${item.target_id ?? "N/A"} | ผู้กระทำ ${item.actor_user_id ?? "system"}</p>
            <p>${formatDate(item.created_at)}</p>
            <pre>${JSON.stringify(item.details || {}, null, 2)}</pre>
          </div>
        </article>
      `
    )
  );
}

function renderReportTable(reportKey, rows) {
  const output = document.getElementById("report-output");
  if (!output) return;

  const columns = {
    "late-borrowings": [
      { key: "borrow_id", label: "#" },
      { key: "borrower_name", label: "ผู้ยืม" },
      { key: "equipment_name", label: "อุปกรณ์" },
      { key: "lab_name", label: "ห้อง" },
      { key: "expected_return", label: "กำหนดคืน", fmt: formatDate },
      { key: "actual_return", label: "คืนจริง", fmt: formatDate },
      { key: "hours_late", label: "ชั่วโมงที่เกินกำหนด" },
      { key: "fine_amount", label: "ค่าปรับ (บาท)", fmt: (v) => v != null ? Number(v).toFixed(2) : "-" },
      { key: "status", label: "สถานะ" },
    ],
    "top-borrowers": [
      { key: "user_id", label: "#" },
      { key: "full_name", label: "ชื่อ" },
      { key: "email", label: "อีเมล" },
      { key: "role_name", label: "สิทธิ์" },
      { key: "total_borrowings", label: "จำนวนครั้งที่ยืม" },
      { key: "penalty_count", label: "จำนวนค่าปรับ" },
      { key: "total_fines", label: "ค่าปรับรวม (บาท)", fmt: (v) => Number(v).toFixed(2) },
    ],
    "lab-utilization": [
      { key: "room_name", label: "ห้อง" },
      { key: "lab_type", label: "ประเภท" },
      { key: "capacity", label: "ความจุ" },
      { key: "status", label: "สถานะ" },
      { key: "total_reservations", label: "จำนวนการจองทั้งหมด" },
      { key: "approved_reservations", label: "อนุมัติแล้ว" },
      { key: "equipment_count", label: "จำนวนอุปกรณ์" },
    ],
    "equipment-repairs": [
      { key: "equipment_id", label: "#" },
      { key: "equipment_name", label: "อุปกรณ์" },
      { key: "category_name", label: "หมวด" },
      { key: "lab_name", label: "ห้อง" },
      { key: "current_status", label: "สถานะปัจจุบัน" },
      { key: "repair_count", label: "จำนวนครั้งที่ซ่อม" },
      { key: "open_repairs", label: "งานซ่อมที่ยังเปิด" },
      { key: "last_reported", label: "แจ้งล่าสุด", fmt: formatDate },
    ],
    "reservation-summary": [
      { key: "reservation_id", label: "#" },
      { key: "room_name", label: "ห้อง" },
      { key: "reserved_by_name", label: "ผู้จอง" },
      { key: "start_time", label: "เริ่ม", fmt: formatDate },
      { key: "end_time", label: "สิ้นสุด", fmt: formatDate },
      { key: "duration_hours", label: "ชั่วโมง" },
      { key: "participant_count", label: "จำนวนผู้ใช้" },
      { key: "status", label: "สถานะ" },
    ],
  };

  const cols = columns[reportKey] || [];
  const title = reportTitleV2(reportKey);

  if (!rows.length) {
    output.innerHTML = `<p class="empty-state"><strong>${title}</strong> - ไม่พบข้อมูล</p>`;
    return;
  }

  const headerCells = cols.map((c) => `<th>${c.label}</th>`).join("");
  const bodyRows = rows
    .map((row) => {
      const cells = cols
        .map((c) => {
          const raw = row[c.key];
          const display = c.fmt ? c.fmt(raw) : (raw ?? "-");
          return `<td>${display}</td>`;
        })
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  output.innerHTML = `
    <p class="report-title"><strong>${title}</strong> - ${rows.length} รายการ</p>
    <div class="table-wrap">
      <table class="report-table">
        <thead><tr>${headerCells}</tr></thead>
        <tbody>${bodyRows}</tbody>
      </table>
    </div>
  `;
}
