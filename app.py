"""QuizArena Live — real-time multiplayer quiz game (Kahoot-style): host a game, players join with a PIN,
answer against the clock, speed-based scoring, streak bonuses, live leaderboard and podium.
Run:  python app.py   →  http://127.0.0.1:5000   (demo: demo@example.com / Demo@1234)
Open a second browser / incognito window, register another account and join with the PIN to play live.
"""
import json
import random
import time

from flask import abort, flash, g, jsonify, redirect, render_template, request, url_for

from core import create_app, execute, login_required, query

UI = dict(
    name="QuizArena Live", short="Real-time Multiplayer Quiz", icon="⚡", accent1="#FF006E", accent2="#8338EC", home="quizzes",
    tagline="Create quizzes, host live games and battle friends in real time. Speed matters — streaks multiply your points.",
    hero='Learning becomes <span class="gradient-text">a live game show.</span>', badge="Real-time multiplayer",
    features=[("bi-broadcast-pin", "Live game rooms", "Players join with a 6-digit PIN from any device"),
              ("bi-lightning-charge", "Speed scoring", "Faster correct answers & streaks earn more points"),
              ("bi-trophy", "Leaderboard & podium", "Animated rankings after every question")],
    float=['🏆 <b>Priya</b> takes the lead · 2,840 pts', '⚡ PIN <b class="gradient-text">482 913</b> · 24 players'],
    nav=[("My Quizzes", "quizzes", "bi-grid"), ("Create Quiz", "builder", "bi-plus-square"), ("Join Game", "join_page", "bi-joystick")],
    search_hint="Search quizzes…", promo_title="Solo? No problem", promo="Add practice bots in the lobby to try a full game on your own.",
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL, description TEXT, emoji TEXT DEFAULT '🧠', questions TEXT NOT NULL, is_public INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    host_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, pin TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'lobby', q_index INTEGER DEFAULT -1, q_started REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS players (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE, user_id INTEGER NOT NULL, nickname TEXT NOT NULL,
    avatar TEXT, score INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, is_bot INTEGER DEFAULT 0, joined REAL, PRIMARY KEY(game_id, user_id));
CREATE TABLE IF NOT EXISTS answers (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE, q_index INTEGER NOT NULL, user_id INTEGER NOT NULL,
    choice INTEGER NOT NULL, correct INTEGER NOT NULL, points INTEGER NOT NULL, ms INTEGER NOT NULL, PRIMARY KEY(game_id, q_index, user_id));
"""
AVATARS = ["🦊", "🐼", "🐯", "🦁", "🐸", "🐵", "🦄", "🐙", "🐧", "🐨", "🦉", "🐲"]
BOTS = [("NeuralNinja 🤖", .8), ("ByteBuddy 🤖", .6), ("QuantumQuokka 🤖", .5), ("PixelPanda 🤖", .7), ("CodeCobra 🤖", .4)]

SAMPLE_QUIZZES = [
    ("AI & Machine Learning Fundamentals", "Test your ML basics", "🤖", [
        ("Which algorithm is used for classification AND regression?", ["K-Means", "Decision Tree", "PCA", "Apriori"], 1, 20),
        ("What does 'overfitting' mean?", ["Model too simple", "Model memorises training data", "Too little data", "Fast training"], 1, 20),
        ("Which activation outputs values between 0 and 1?", ["ReLU", "Tanh", "Sigmoid", "Linear"], 2, 15),
        ("What is the main purpose of a validation set?", ["Train the model", "Tune & select models", "Deploy", "Label data"], 1, 20),
        ("Which library is best known for deep learning?", ["Pandas", "Matplotlib", "PyTorch", "Seaborn"], 2, 15),
        ("Gradient descent minimises the…", ["Accuracy", "Loss function", "Learning rate", "Dataset"], 1, 15),
        ("RAG stands for…", ["Random Access Graph", "Retrieval-Augmented Generation", "Recurrent Attention Gate", "Rapid AI Generation"], 1, 20),
        ("K in K-Means represents…", ["Kernels", "Number of clusters", "Key features", "Knowledge"], 1, 15)]),
    ("Cybersecurity Basics", "Stay safe online", "🛡️", [
        ("Which is the strongest password?", ["password123", "Rahul@1990", "correct-horse-battery-staple-42", "qwerty!"], 2, 20),
        ("What does MFA add?", ["Faster login", "An extra verification factor", "Encryption", "A firewall"], 1, 15),
        ("Phishing is mainly a form of…", ["Hardware failure", "Social engineering", "Data compression", "Cloud backup"], 1, 15),
        ("HTTPS protects data by…", ["Compressing it", "Encrypting it in transit", "Deleting cookies", "Blocking ads"], 1, 15),
        ("SQL injection is prevented by…", ["Parameterized queries", "Bigger servers", "More RAM", "CSS"], 0, 20),
        ("Which port does HTTPS use by default?", ["21", "80", "443", "8080"], 2, 15)]),
    ("Python Quick Fire", "Speed round for Pythonistas", "🐍", [
        ("Output of len('Hello')?", ["4", "5", "6", "Error"], 1, 10),
        ("Which is immutable?", ["list", "dict", "set", "tuple"], 3, 10),
        ("Keyword to define a function?", ["func", "def", "function", "lambda"], 1, 10),
        ("What does // do?", ["Comment", "Floor division", "Power", "Modulo"], 1, 10),
        ("Which creates a generator?", ["return", "yield", "async", "with"], 1, 15)]),
]


def qjson(qs):
    return json.dumps([dict(q=q, options=o, answer=a, time=t) for q, o, a, t in qs])


def seed_demo(uid):
    for title, desc, emo, qs in SAMPLE_QUIZZES:
        execute("INSERT INTO quizzes(owner_id,title,description,emoji,questions) VALUES(?,?,?,?,?)", (uid, title, desc, emo, qjson(qs)))


app = create_app(__name__, UI, SCHEMA, seed_demo=seed_demo)


# ---------------------------------------------------------------- game engine
def game_or_404(pin):
    gm = query("SELECT g.*, q.title, q.emoji, q.questions FROM games g JOIN quizzes q ON q.id=g.quiz_id WHERE g.pin=?", (pin,), one=True)
    if not gm:
        abort(404)
    gm["qs"] = json.loads(gm["questions"])
    return gm


def players(gid):
    return query("SELECT user_id, nickname, avatar, score, streak, is_bot FROM players WHERE game_id=? ORDER BY score DESC, joined", (gid,))


def award(gm, uid, choice, ms):
    q = gm["qs"][gm["q_index"]]
    p = query("SELECT streak FROM players WHERE game_id=? AND user_id=?", (gm["id"], uid), one=True)
    correct = int(choice == q["answer"])
    streak = (p["streak"] + 1) if correct else 0
    pts = int(500 + 500 * max(0, 1 - ms / (q["time"] * 1000)) + 100 * min(streak - 1, 3)) if correct else 0
    execute("INSERT OR IGNORE INTO answers VALUES(?,?,?,?,?,?,?)", (gm["id"], gm["q_index"], uid, choice, correct, pts, ms))
    execute("UPDATE players SET score=score+?, streak=? WHERE game_id=? AND user_id=?", (pts, streak, gm["id"], uid))
    return correct, pts, streak


def tick(gm):
    """Advance time-based state: bots answer, auto-reveal when time is up or everyone answered."""
    if gm["status"] != "question":
        return gm
    q = gm["qs"][gm["q_index"]]
    elapsed = time.time() - gm["q_started"]
    answered = {a["user_id"] for a in query("SELECT user_id FROM answers WHERE game_id=? AND q_index=?", (gm["id"], gm["q_index"]))}
    for b in query("SELECT user_id FROM players WHERE game_id=? AND is_bot=1", (gm["id"],)):
        if b["user_id"] in answered:
            continue
        rng = random.Random(f"{gm['id']}-{gm['q_index']}-{b['user_id']}")
        skill = BOTS[(-b["user_id"] - 1) % len(BOTS)][1]
        when = rng.uniform(1.5, q["time"] * .8)
        if elapsed >= when:
            choice = q["answer"] if rng.random() < skill else rng.choice([i for i in range(len(q["options"])) if i != q["answer"]])
            award(gm, b["user_id"], choice, int(when * 1000))
            answered.add(b["user_id"])
    total = query("SELECT COUNT(*) n FROM players WHERE game_id=?", (gm["id"],), one=True)["n"]
    if elapsed >= q["time"] or (total and len(answered) >= total):
        execute("UPDATE games SET status='reveal' WHERE id=? AND status='question'", (gm["id"],))
        gm["status"] = "reveal"
    return gm


def state(gm, uid):
    gm = tick(gm)
    ps = players(gm["id"])
    s = dict(status=gm["status"], pin=gm["pin"], title=gm["title"], q_index=gm["q_index"], total_q=len(gm["qs"]),
             players=ps, is_host=gm["host_id"] == uid, server_time=time.time())
    me = next((p for p in ps if p["user_id"] == uid), None)
    if me:
        s["me"] = dict(me, rank=ps.index(me) + 1)
    if gm["status"] in ("question", "reveal") and gm["q_index"] >= 0:
        q = gm["qs"][gm["q_index"]]
        s["question"] = dict(q=q["q"], options=q["options"], time=q["time"],
                             remaining=max(0, q["time"] - (time.time() - gm["q_started"])))
        ans = query("SELECT user_id, choice, correct, points FROM answers WHERE game_id=? AND q_index=?", (gm["id"], gm["q_index"]))
        s["answered"] = len(ans)
        mine = next((a for a in ans if a["user_id"] == uid), None)
        s["my_answer"] = mine
        if gm["status"] == "reveal":
            s["question"]["answer"] = q["answer"]
            s["distribution"] = [sum(a["choice"] == i for a in ans) for i in range(len(q["options"]))]
    return s


# ---------------------------------------------------------------- pages
@app.route("/quizzes")
@login_required
def quizzes():
    rows = query("SELECT q.*, u.name owner FROM quizzes q JOIN users u ON u.id=q.owner_id WHERE q.is_public=1 OR q.owner_id=? ORDER BY q.owner_id=? DESC, q.id DESC",
                 (g.user["id"], g.user["id"]))
    for r in rows:
        r["n"] = len(json.loads(r["questions"]))
    games = query("SELECT g.pin, g.status, g.created_at, q.title, q.emoji, (SELECT COUNT(*) FROM players p WHERE p.game_id=g.id) np, "
                  "(SELECT nickname FROM players p WHERE p.game_id=g.id ORDER BY score DESC LIMIT 1) winner FROM games g JOIN quizzes q ON q.id=g.quiz_id "
                  "WHERE g.host_id=? OR g.id IN (SELECT game_id FROM players WHERE user_id=?) ORDER BY g.id DESC LIMIT 6", (g.user["id"], g.user["id"]))
    return render_template("quizzes.html", rows=rows, games=games, page_title="My Quizzes")


@app.route("/builder", methods=["GET", "POST"])
@login_required
def builder():
    if request.method == "POST":
        d = request.get_json(force=True)
        title = str(d.get("title", "")).strip()[:120]
        qs = []
        for q in d.get("questions", [])[:50]:
            opts = [str(o).strip()[:100] for o in q.get("options", []) if str(o).strip()]
            if str(q.get("q", "")).strip() and 2 <= len(opts) <= 4 and 0 <= int(q.get("answer", -1)) < len(opts):
                qs.append(dict(q=str(q["q"]).strip()[:250], options=opts, answer=int(q["answer"]), time=max(5, min(60, int(q.get("time", 20))))))
        if len(title) < 3 or not qs:
            return jsonify(error="Add a title and at least one complete question (2–4 options, correct answer selected)"), 400
        qid = execute("INSERT INTO quizzes(owner_id,title,description,emoji,questions,is_public) VALUES(?,?,?,?,?,?)",
                      (g.user["id"], title, str(d.get("description", ""))[:300], str(d.get("emoji", "🧠"))[:4], json.dumps(qs), int(bool(d.get("public", True)))))
        return jsonify(ok=True, id=qid)
    return render_template("builder.html", page_title="Create Quiz")


@app.post("/host/<int:quiz_id>")
@login_required
def host_new(quiz_id):
    if not query("SELECT 1 FROM quizzes WHERE id=? AND (is_public=1 OR owner_id=?)", (quiz_id, g.user["id"]), one=True):
        abort(404)
    while True:
        pin = str(random.randint(100000, 999999))
        if not query("SELECT 1 FROM games WHERE pin=?", (pin,), one=True):
            break
    execute("INSERT INTO games(quiz_id,host_id,pin) VALUES(?,?,?)", (quiz_id, g.user["id"], pin))
    return redirect(url_for("host", pin=pin))


@app.route("/host/<pin>")
@login_required
def host(pin):
    gm = game_or_404(pin)
    if gm["host_id"] != g.user["id"]:
        return redirect(url_for("play", pin=pin))
    return render_template("host.html", gm=gm, page_title="Hosting live")


@app.route("/join", methods=["GET", "POST"])
@login_required
def join_page():
    if request.method == "POST":
        pin = request.form.get("pin", "").replace(" ", "")
        gm = query("SELECT * FROM games WHERE pin=?", (pin,), one=True)
        if not gm or gm["status"] == "ended":
            flash("Game not found or already finished.", "danger")
            return redirect(url_for("join_page"))
        nick = request.form.get("nickname", "").strip()[:20] or g.user["name"].split()[0]
        execute("INSERT OR IGNORE INTO players(game_id,user_id,nickname,avatar,joined) VALUES(?,?,?,?,?)",
                (gm["id"], g.user["id"], nick, request.form.get("avatar") or random.choice(AVATARS), time.time()))
        return redirect(url_for("play", pin=pin))
    return render_template("join.html", AVATARS=AVATARS, page_title="Join Game")


@app.route("/play/<pin>")
@login_required
def play(pin):
    gm = game_or_404(pin)
    if not query("SELECT 1 FROM players WHERE game_id=? AND user_id=?", (gm["id"], g.user["id"]), one=True):
        return redirect(url_for("join_page"))
    return render_template("play.html", gm=gm, page_title="Playing live")


# ---------------------------------------------------------------- API
@app.get("/api/game/<pin>")
@login_required
def api_state(pin):
    return jsonify(state(game_or_404(pin), g.user["id"]))


@app.post("/api/game/<pin>/<action>")
@login_required
def api_action(pin, action):
    gm = game_or_404(pin)
    uid = g.user["id"]
    if action == "answer":
        gm = tick(gm)
        if gm["status"] != "question":
            return jsonify(error="Time is up!"), 400
        if not query("SELECT 1 FROM players WHERE game_id=? AND user_id=?", (gm["id"], uid), one=True):
            return jsonify(error="Join the game first"), 403
        if query("SELECT 1 FROM answers WHERE game_id=? AND q_index=? AND user_id=?", (gm["id"], gm["q_index"], uid), one=True):
            return jsonify(error="Already answered"), 409
        choice = int(request.get_json(force=True).get("choice", -1))
        correct, pts, streak = award(gm, uid, choice, int((time.time() - gm["q_started"]) * 1000))
        return jsonify(ok=True, correct=bool(correct), points=pts, streak=streak)
    if gm["host_id"] != uid:
        return jsonify(error="Only the host can control the game"), 403
    if action == "bots" and gm["status"] == "lobby":
        for i, (name, _) in enumerate(BOTS):
            execute("INSERT OR IGNORE INTO players(game_id,user_id,nickname,avatar,is_bot,joined) VALUES(?,?,?,?,1,?)",
                    (gm["id"], -(i + 1), name, AVATARS[i + 3], time.time() + i))
    elif action == "kick":
        execute("DELETE FROM players WHERE game_id=? AND user_id=?", (gm["id"], int(request.get_json(force=True).get("user_id"))))
    elif action == "next":
        if gm["q_index"] + 1 >= len(gm["qs"]):
            execute("UPDATE games SET status='ended' WHERE id=?", (gm["id"],))
        else:
            execute("UPDATE games SET status='question', q_index=q_index+1, q_started=? WHERE id=?", (time.time() + 0.5, gm["id"]))
    elif action == "reveal":
        execute("UPDATE games SET status='reveal' WHERE id=?", (gm["id"],))
    elif action == "end":
        execute("UPDATE games SET status='ended' WHERE id=?", (gm["id"],))
    return jsonify(state(game_or_404(pin), uid))


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
