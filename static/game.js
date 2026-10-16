/* Shared rendering helpers for host & player screens */
window.SHAPES = ["▲", "◆", "●", "■"];
window.Game = {
  answers(q, opts = {}) {
    return `<div class="answers">${q.options.map((o, i) => {
      const cls = [`ans a${i}`];
      if (q.answer !== undefined) cls.push(i === q.answer ? "correct" : "dim");
      if (opts.picked === i) cls.push("picked");
      const cnt = opts.dist ? `<span class="cnt">${opts.dist[i]}</span>` : "";
      return `<button class="${cls.join(" ")}" data-i="${i}" ${opts.disabled ? "disabled" : ""}><span class="shape">${SHAPES[i]}</span>${esc(o)}${cnt}</button>`;
    }).join("")}</div>`;
  },
  timer(rem, total) {
    const C = 2 * Math.PI * 40, off = C * (1 - rem / total);
    return `<div class="timer-ring ${rem <= 5 ? "low" : ""}"><svg width="96" height="96"><circle cx="48" cy="48" r="40" stroke="var(--input)"/>
      <circle cx="48" cy="48" r="40" stroke="url(#tg)" stroke-dasharray="${C}" stroke-dashoffset="${off}" style="transition:stroke-dashoffset .9s linear"/>
      <defs><linearGradient id="tg"><stop offset="0" stop-color="var(--a1)"/><stop offset="1" stop-color="var(--a2)"/></linearGradient></defs></svg>
      <div class="t">${Math.ceil(rem)}</div></div>`;
  },
  leaderboard(ps, meId, n = 8) {
    return ps.slice(0, n).map((p, i) => `<div class="lb-row pop" style="animation-delay:${i * 70}ms;${p.user_id === meId ? "border-color:var(--a1)" : ""}">
      <span class="rk">${i + 1}</span><span style="font-size:24px">${p.avatar || "🙂"}</span><b>${esc(p.nickname)}</b>
      ${p.streak >= 2 ? `<span class="badge warning">🔥 ${p.streak}</span>` : ""}<span class="sc">${p.score.toLocaleString()}</span></div>`).join("") || '<div class="empty">No players yet</div>';
  },
  podium(ps) {
    const order = [ps[1], ps[0], ps[2]], h = [200, 270, 150], col = ["linear-gradient(#c0c0c0,#8e9399)", "linear-gradient(#FFD700,#F7B32B)", "linear-gradient(#cd7f32,#8b4513)"], place = [2, 1, 3];
    return `<div class="podium">${order.map((p, i) => p ? `<div class="pod"><div class="who">${p.avatar || "🙂"}</div><div class="nm">${esc(p.nickname)}</div>
      <div class="muted small">${p.score.toLocaleString()} pts</div><div class="bar" style="height:${h[i]}px;background:${col[i]};animation-delay:${[.4, .8, 0][i]}s">${place[i]}</div></div>` : "").join("")}</div>`;
  },
};
