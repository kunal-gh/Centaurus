const $ = (id) => document.getElementById(id);

function setTab(name) {
  for (const btn of document.querySelectorAll(".tab")) {
    btn.classList.toggle("active", btn.dataset.tab === name);
  }
  for (const panel of document.querySelectorAll(".panel")) {
    panel.classList.toggle("active", panel.id === `tab-${name}`);
  }
}

function addBubble(role, text, sources = null) {
  const div = document.createElement("div");
  div.className = `bubble ${role === "user" ? "user" : "bot"}`;
  
  const textEl = document.createElement("div");
  textEl.className = "text";
  if (text.includes("**")) {
    textEl.innerHTML = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  } else {
    textEl.textContent = text;
  }
  div.appendChild(textEl);

  if (sources && sources.length > 0) {
    const sourcesEl = document.createElement("div");
    sourcesEl.className = "bubble-sources";
    
    const title = document.createElement("div");
    title.className = "sources-title";
    title.textContent = "Sources & Citations:";
    sourcesEl.appendChild(title);

    const list = document.createElement("ul");
    for (const src of sources) {
      const li = document.createElement("li");
      const scorePct = ((src.score ?? 0) * 100).toFixed(0);
      li.innerHTML = `<strong>${src.section ?? "Policy"}</strong> <span class="score">(${scorePct}% relevance)</span> <span class="file">${src.source ?? ""}</span>`;
      list.appendChild(li);
    }
    sourcesEl.appendChild(list);
    div.appendChild(sourcesEl);
  }

  $("chatlog").appendChild(div);
  $("chatlog").scrollTop = $("chatlog").scrollHeight;
}

function setMeta(meta) {
  const host = $("chatMeta");
  host.innerHTML = "";
  const conf = Number(meta.confidence ?? 0);
  const confClass = conf >= 0.8 ? "good" : conf >= 0.6 ? "warn" : "bad";
  const pills = [
    { text: `Confidence ${(conf * 100).toFixed(0)}%`, cls: confClass },
    { text: `Intent ${meta.intent ?? "unknown"}`, cls: "" },
    { text: meta.escalated ? "Escalated" : "Auto-resolved", cls: meta.escalated ? "bad" : "good" },
    { text: meta.author_found ? "Profile matched" : "No profile match", cls: meta.author_found ? "good" : "warn" },
  ];
  for (const pill of pills) {
    const el = document.createElement("span");
    el.className = `pill ${pill.cls}`.trim();
    el.textContent = pill.text;
    host.appendChild(el);
  }
}

let API_BASE = localStorage.getItem("CENTAURUS_API_URL") || "";

async function postJson(url, body) {
  const fullUrl = API_BASE ? `${API_BASE.replace(/\/$/, '')}${url}` : url;
  const res = await fetch(fullUrl, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

async function getJson(url) {
  const fullUrl = API_BASE ? `${API_BASE.replace(/\/$/, '')}${url}` : url;
  const res = await fetch(fullUrl);
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
    host.innerHTML = `<div class="muted">No pending reviewer items right now.</div>`;
    return;
  }

  for (const item of items) {
    const el = document.createElement("div");
    el.className = "item";
    const conf = Number(item.match_confidence ?? 0);
    const confClass = conf >= 0.8 ? "good" : conf >= 0.6 ? "warn" : "bad";

    el.innerHTML = `
      <div class="top">
        <div>
          <div><strong>Mapping</strong> <code>${item.id}</code></div>
          <div class="muted">Platform <code>${item.platform}</code> · Identifier <code>${item.platform_identifier}</code></div>
          <div class="muted">Profile <code>${item.authors?.email ?? item.author_id ?? "unknown"}</code></div>
        </div>
        <div class="actions">
          <button class="ghost" data-action="reject">Reject</button>
          <button data-action="approve">Approve</button>
        </div>
      </div>
      <div class="meta">
        <span class="pill ${confClass}">Match ${(conf * 100).toFixed(0)}%</span>
        <span class="pill">Verified ${String(item.verified)}</span>
      </div>
    `;

    el.querySelector('[data-action="approve"]').addEventListener("click", async () => {
      await postJson(`/admin/identity-review/${item.id}/approve`, { note: "approved via Centaurus UI" });
      await refreshAdmin();
    });

    el.querySelector('[data-action="reject"]').addEventListener("click", async () => {
      await postJson(`/admin/identity-review/${item.id}/reject`, { note: "rejected via Centaurus UI" });
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

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});

document.querySelectorAll(".prompt-chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    $("message").value = btn.dataset.prompt;
    $("message").focus();
    setTab("playground");
  });
});

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
    addBubble("bot", data.response ?? "(no response)", data.sources);
    setMeta(data);
  } catch (e) {
    addBubble("bot", `Error: ${String(e)}`);
  }
});

$("identityRun").addEventListener("click", runIdentity);
$("identitySeed").addEventListener("click", () => {
  seedIdentity();
  runIdentity();
});

$("adminRefresh").addEventListener("click", refreshAdmin);

const apiBaseInput = $("api_base_url");
if (apiBaseInput) {
  apiBaseInput.value = API_BASE;
  apiBaseInput.addEventListener("input", (e) => {
    API_BASE = e.target.value.trim();
    localStorage.setItem("CENTAURUS_API_URL", API_BASE);
  });
}

addBubble(
  "bot",
  "Centaurus is ready. Ask about launch status, royalties, workspace access, service programs, author copies, or sales. If confidence drops or the request needs a person, I’ll route it to review."
);
refreshAdmin();
