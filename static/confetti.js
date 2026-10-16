/* Lightweight canvas confetti burst */
window.confettiBurst = (n = 160) => {
  const cv = document.getElementById("confetti"); if (!cv) return;
  const ctx = cv.getContext("2d"); cv.width = innerWidth; cv.height = innerHeight;
  const cols = ["#FF6B6B", "#845EF7", "#2CB67D", "#F7B32B", "#3DA9FC", "#FF4FA3"];
  const ps = Array.from({ length: n }, () => ({ x: innerWidth / 2, y: innerHeight / 2.4, vx: (Math.random() - .5) * 18, vy: Math.random() * -16 - 4,
    s: Math.random() * 8 + 4, c: cols[Math.floor(Math.random() * cols.length)], r: Math.random() * 6, vr: (Math.random() - .5) * .3, life: 0 }));
  const tick = () => {
    ctx.clearRect(0, 0, cv.width, cv.height); let alive = 0;
    ps.forEach(p => { p.vy += .45; p.vx *= .99; p.x += p.vx; p.y += p.vy; p.r += p.vr; p.life++;
      if (p.y < cv.height + 20 && p.life < 220) { alive++; ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c;
        ctx.globalAlpha = Math.max(0, 1 - p.life / 220); ctx.fillRect(-p.s / 2, -p.s / 4, p.s, p.s / 2); ctx.restore(); } });
    if (alive) requestAnimationFrame(tick); else ctx.clearRect(0, 0, cv.width, cv.height);
  };
  tick();
};
