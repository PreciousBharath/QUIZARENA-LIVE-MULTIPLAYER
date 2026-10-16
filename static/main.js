/* Shared UI behaviour: theme, toasts, API helper, count-up, ripple, reveal, modals, particles, password meter */
(() => {
  const root = document.documentElement;
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";

  /* ---------- theme ---------- */
  const setTheme = t => { root.dataset.theme = t; try { localStorage.setItem("theme", t); } catch (e) {}
    document.querySelectorAll("[data-theme-icon]").forEach(i => i.className = t === "dark" ? "bi bi-sun" : "bi bi-moon-stars");
    window.dispatchEvent(new Event("themechange")); };
  let saved = "dark"; try { saved = localStorage.getItem("theme") || "dark"; } catch (e) {}
  setTheme(saved);
  document.addEventListener("click", e => { if (e.target.closest("[data-toggle-theme]")) setTheme(root.dataset.theme === "dark" ? "light" : "dark"); });

  /* ---------- toasts ---------- */
  const icons = { success: "bi-check-circle-fill", danger: "bi-x-octagon-fill", warning: "bi-exclamation-triangle-fill", info: "bi-info-circle-fill" };
  const colors = { success: "var(--success)", danger: "var(--danger)", warning: "var(--warning)", info: "var(--info)" };
  window.toast = (msg, type = "info", ms = 3800) => {
    let box = document.querySelector(".toasts");
    if (!box) { box = document.createElement("div"); box.className = "toasts"; document.body.appendChild(box); }
    const t = document.createElement("div");
    t.className = `toast ${type}`;
    t.innerHTML = `<i class="bi ${icons[type] || icons.info}" style="color:${colors[type] || colors.info};font-size:20px"></i><div class="small" style="flex:1"></div>`;
    t.querySelector("div").textContent = msg;
    box.appendChild(t);
    setTimeout(() => { t.classList.add("hide"); setTimeout(() => t.remove(), 400); }, ms);
  };
  document.querySelectorAll("[data-flash]").forEach((f, i) => setTimeout(() => toast(f.dataset.msg, f.dataset.flash), i * 250));

  /* ---------- API helper ---------- */
  window.api = async (url, opts = {}) => {
    const o = { method: opts.method || (opts.body ? "POST" : "GET"), headers: { "X-CSRF-Token": csrf } };
    if (opts.body instanceof FormData) o.body = opts.body;
    else if (opts.body) { o.body = JSON.stringify(opts.body); o.headers["Content-Type"] = "application/json"; }
    const r = await fetch(url, o);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) { toast(data.error || `Request failed (${r.status})`, "danger"); throw new Error(data.error || r.status); }
    return data;
  };

  /* ---------- count-up numbers ---------- */
  window.countUp = (el, to, opts = {}) => {
    const dec = opts.decimals ?? (String(to).includes(".") ? String(to).split(".")[1].length : 0);
    const pre = opts.prefix ?? el.dataset.prefix ?? "", suf = opts.suffix ?? el.dataset.suffix ?? "";
    const start = performance.now(), dur = opts.duration || 1300, from = 0;
    const step = now => {
      const p = Math.min(1, (now - start) / dur), e = 1 - Math.pow(1 - p, 4);
      el.textContent = pre + (from + (to - from) * e).toLocaleString("en-IN", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf;
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  const runCounts = scope => scope.querySelectorAll("[data-count]").forEach(el => countUp(el, parseFloat(el.dataset.count)));
  window.runCounts = runCounts;
  runCounts(document);

  /* ---------- progress bars ---------- */
  window.runBars = scope => setTimeout(() => (scope || document).querySelectorAll(".progress>span[data-w]").forEach(s => s.style.width = s.dataset.w + "%"), 150);
  runBars();

  /* ---------- ripple ---------- */
  document.addEventListener("click", e => {
    const b = e.target.closest(".btn"); if (!b) return;
    const r = document.createElement("span"), d = Math.max(b.clientWidth, b.clientHeight), rect = b.getBoundingClientRect();
    r.className = "ripple"; r.style.width = r.style.height = d + "px";
    r.style.left = e.clientX - rect.left - d / 2 + "px"; r.style.top = e.clientY - rect.top - d / 2 + "px";
    b.appendChild(r); setTimeout(() => r.remove(), 600);
  });

  /* ---------- reveal on scroll + stagger ---------- */
  document.querySelectorAll(".fade-up").forEach((el, i) => el.style.animationDelay = (el.dataset.delay || i * 70) + "ms");
  const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } }), { threshold: .12 });
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));

  /* ---------- sidebar, dropdowns, modals ---------- */
  document.addEventListener("click", e => {
    if (e.target.closest("[data-menu]")) document.querySelector(".sidebar")?.classList.toggle("open");
    const dd = e.target.closest(".dropdown");
    document.querySelectorAll(".dropdown.open").forEach(d => { if (d !== dd) d.classList.remove("open"); });
    if (e.target.closest("[data-dropdown]")) dd.classList.toggle("open");
    const m = e.target.closest("[data-modal]"); if (m) { document.getElementById(m.dataset.modal)?.classList.add("open"); }
    if (e.target.closest("[data-close]") || e.target.classList.contains("modal")) e.target.closest(".modal")?.classList.remove("open");
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") document.querySelectorAll(".modal.open").forEach(m => m.classList.remove("open"));
    if ((e.ctrlKey || e.metaKey) && e.key === "k") { const s = document.querySelector(".search input"); if (s) { e.preventDefault(); s.focus(); } }
  });

  /* ---------- password show/hide + strength ---------- */
  document.querySelectorAll(".toggle-pw").forEach(b => b.addEventListener("click", () => {
    const i = b.parentElement.querySelector("input"); const show = i.type === "password";
    i.type = show ? "text" : "password"; b.innerHTML = `<i class="bi ${show ? "bi-eye-slash" : "bi-eye"}"></i>`;
  }));
  document.querySelectorAll("[data-strength]").forEach(inp => {
    const bars = document.querySelectorAll(inp.dataset.strength + " span"), txt = document.querySelector(inp.dataset.strength + "-text");
    const lv = [["Too weak", "var(--danger)"], ["Weak", "var(--danger)"], ["Fair", "var(--warning)"], ["Good", "var(--info)"], ["Strong 💪", "var(--success)"]];
    inp.addEventListener("input", () => {
      const v = inp.value; let s = 0;
      if (v.length >= 8) s++; if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++; if (/\d/.test(v)) s++; if (/[^A-Za-z0-9]/.test(v) || v.length >= 14) s++;
      bars.forEach((b, i) => b.style.background = i < s ? lv[s][1] : "");
      if (txt) { txt.textContent = v ? lv[s][0] : ""; txt.style.color = lv[s][1]; }
    });
  });

  /* ---------- particle network (auth hero) ---------- */
  const cv = document.getElementById("particles");
  if (cv) {
    const ctx = cv.getContext("2d"); let W, H, pts = [], mouse = { x: -999, y: -999 };
    const resize = () => { W = cv.width = cv.offsetWidth; H = cv.height = cv.offsetHeight;
      pts = Array.from({ length: Math.min(90, Math.floor(W * H / 12000)) }, () => ({ x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .5, vy: (Math.random() - .5) * .5 })); };
    resize(); addEventListener("resize", resize);
    cv.parentElement.addEventListener("mousemove", e => { const r = cv.getBoundingClientRect(); mouse = { x: e.clientX - r.left, y: e.clientY - r.top }; });
    const accent = getComputedStyle(root).getPropertyValue("--a1").trim() || "#7F5AF0";
    const tick = () => {
      ctx.clearRect(0, 0, W, H);
      pts.forEach(p => { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1;
        const dm = Math.hypot(p.x - mouse.x, p.y - mouse.y); if (dm < 120) { p.x += (p.x - mouse.x) / dm; p.y += (p.y - mouse.y) / dm; }
        ctx.fillStyle = accent; ctx.globalAlpha = .8; ctx.beginPath(); ctx.arc(p.x, p.y, 2, 0, 7); ctx.fill(); });
      for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
        const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
        if (d < 120) { ctx.globalAlpha = (1 - d / 120) * .35; ctx.strokeStyle = accent; ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke(); }
      }
      ctx.globalAlpha = 1; requestAnimationFrame(tick);
    };
    tick();
  }

  /* ---------- Chart.js theme helper ---------- */
  window.chartColors = () => {
    const cs = getComputedStyle(root);
    return { a1: cs.getPropertyValue("--a1").trim(), a2: cs.getPropertyValue("--a2").trim(), text: cs.getPropertyValue("--muted").trim(),
      grid: cs.getPropertyValue("--border").trim(), palette: [cs.getPropertyValue("--a1").trim(), cs.getPropertyValue("--a2").trim(), "#FF5470", "#3DA9FC", "#F7B32B", "#E85D75", "#9B5DE5", "#00BBF9"] };
  };
  window.applyChartDefaults = () => {
    if (!window.Chart) return;
    const c = chartColors();
    Chart.defaults.color = c.text; Chart.defaults.borderColor = c.grid; Chart.defaults.font.family = "Poppins, system-ui, sans-serif";
    Chart.defaults.plugins.legend.labels.usePointStyle = true; Chart.defaults.animation.duration = 1200;
  };
  window.gradientFill = (ctx, color) => { const g = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height || 300);
    g.addColorStop(0, color + "88"); g.addColorStop(1, color + "00"); return g; };
  applyChartDefaults();

  /* ---------- relative time ---------- */
  window.timeAgo = s => { const d = (Date.now() - new Date(s.replace(" ", "T")).getTime()) / 1000;
    if (d < 60) return "just now"; if (d < 3600) return Math.floor(d / 60) + "m ago"; if (d < 86400) return Math.floor(d / 3600) + "h ago"; return Math.floor(d / 86400) + "d ago"; };
  window.esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
})();
