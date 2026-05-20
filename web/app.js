const $ = (id) => document.getElementById(id);

function setTab(name) {
  for (const btn of document.querySelectorAll(".tab")) {
    btn.classList.toggle("active", btn.dataset.tab === name);
  }
  for (const panel of document.querySelectorAll(".panel")) {
    panel.classList.toggle("active", panel.id === `tab-${name}`);
  }
}

function addBubble(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role === "user" ? "user" : "bot"}`;
  div.textContent = text;
  $("chatlog").appendChild(div);
  $("chatlog").scrollTop = $("chatlog").scrollHeight;
}

function setMeta(meta) {
  const host = $("chatMeta");
  host.innerHTML = "";
  const conf = Number(meta.confidence ?? 0);
  const confClass = conf >= 0.8 ? "good" : conf >= 0.6 ? "warn" : "bad";
  const pills = [
    { text: `Confidence: ${(conf * 100).toFixed(0)}%`, cls: confClass },
    { text: `Intent: ${meta.intent ?? "unknown"}`, cls: "" },
    { text: meta.escalated ? "Escalated" : "Not escalated", cls: meta.escalated ? "bad" : "good" },
    { text: meta.author_found ? "Author matched" : "Author not matched", cls: meta.author_found ? "good" : "warn" },
  ];
  for (const p of pills) {
    const el = document.createElement("span");
    el.className = `pill ${p.cls}`.trim();
    el.textContent = p.text;
    host.appendChild(el);
  }
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

async function getJson(url) {
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

function getIdentityPayload(prefix) {
  return {
    email: $(prefix + "_email")?.value || null,
    phone: $(prefix + "_phone")?.value || null,
    name: $(prefix + "_name")?.value || null,
    instagram: $(prefix + "_instagram")?.value || null,
  };
}

async function runIdentity() {
  const payload = getIdentityPayload("id");
  const out = $("identityOut");
  out.textContent = "Loading...";
  try {
    const data = await postJson("/identity/resolve", payload);
    out.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = JSON.stringify({ error: String(e) }, null, 2);
  }
}

function seedIdentity() {
  $("id_email").value = "sara.johnson@xyz.com";
  $("id_phone").value = "+91 9876543210";
  $("id_name").value = "Sara J.";
  $("id_instagram").value = "@sarapoetry23";
}

function renderQueue(items) {
  const host = $("adminQueue");
  host.innerHTML = "";
  if (!items?.length) {
    host.innerHTML = `<div class="muted">No pending items. (Tip: trigger a borderline identity match to create one.)</div>`;
    return;
  }

  for (const it of items) {
    const el = document.createElement("div");
    el.className = "item";
    const conf = Number(it.match_confidence ?? 0);
    const confClass = conf >= 0.8 ? "good" : conf >= 0.6 ? "warn" : "bad";

    el.innerHTML = `
      <div class="top">
        <div>
          <div><strong>Mapping</strong> <code>${it.id}</code></div>
          <div class="muted">Platform: <code>${it.platform}</code> • Identifier: <code>${it.platform_identifier}</code></div>
          <div class="muted">Author: <code>${it.authors?.email ?? it.author_id ?? "unknown"}</code></div>
        </div>
        <div class="actions">
          <button class="ghost" data-action="reject">Reject</button>
          <button data-action="approve">Approve</button>
        </div>
      </div>
      <div class="meta">
        <span class="pill ${confClass}">Match confidence: ${(conf * 100).toFixed(0)}%</span>
        <span class="pill">Verified: ${String(it.verified)}</span>
      </div>
    `;

    el.querySelector('[data-action="approve"]').addEventListener("click", async () => {
      await postJson(`/admin/identity-review/${it.id}/approve`, { note: "approved via demo UI" });
      await refreshAdmin();
    });
    el.querySelector('[data-action="reject"]').addEventListener("click", async () => {
      await postJson(`/admin/identity-review/${it.id}/reject`, { note: "rejected via demo UI" });
      await refreshAdmin();
    });
    host.appendChild(el);
  }
}

async function refreshAdmin() {
  const raw = $("adminRaw");
  raw.textContent = "";
  try {
    const data = await getJson("/admin/identity-review");
    raw.textContent = JSON.stringify(data, null, 2);
    renderQueue(data.pending_review || []);
  } catch (e) {
    renderQueue([]);
    raw.textContent = JSON.stringify({ error: String(e) }, null, 2);
  }
}

// Tabs
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});

// Chat
$("chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = $("message").value.trim();
  if (!msg) return;
  $("message").value = "";
  addBubble("user", msg);

  const payload = {
    channel: "web",
    message: msg,
    user_email: $("user_email").value.trim() || null,
    user_phone: $("user_phone").value.trim() || null,
    user_name: $("user_name").value.trim() || null,
    user_instagram: $("user_instagram").value.trim() || null,
  };

  try {
    const data = await postJson("/chat", payload);
    addBubble("bot", data.response ?? "(no response)");
    setMeta(data);
  } catch (e) {
    addBubble("bot", `Error: ${String(e)}`);
  }
});

// Identity
$("identityRun").addEventListener("click", runIdentity);
$("identitySeed").addEventListener("click", () => { seedIdentity(); runIdentity(); });

// Admin
$("adminRefresh").addEventListener("click", refreshAdmin);

// Default boot
addBubble("bot", "Hi! Ask me about publishing timelines, royalties, dashboard access, add-ons, author copies, or sales. If I’m not confident (or the system hits an error), I’ll escalate to a human.");
refreshAdmin();

