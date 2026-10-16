<div align="center">

# ⚡ QuizArena Live — Real-time Multiplayer Quiz

**Kahoot-style live quiz battles: host a game, players join with a PIN, answer against the clock and race up a live leaderboard.**

![Python-3.10%2B](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Flask-3.x](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white) ![SQLite-Database](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white) ![Chart.js-Charts](https://img.shields.io/badge/Chart.js-Charts-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white) ![Real--time-Multiplayer](https://img.shields.io/badge/Real--time-Multiplayer-FF006E?style=for-the-badge&logo=socketdotio&logoColor=white)

`Real-time Web · EdTech` · `Full-stack web app` · `Register / Login` · `Dark & light themes`

</div>

---

![QUIZARENA-LIVE-MULTIPLAYER](assets/lobby.png)

## ✨ Features

- **Live game rooms** with 6-digit PINs — host screen + player screens stay in sync every second
- **Speed-based scoring** (up to 1,000 pts) + 🔥 streak bonuses
- Animated timer ring, colourful shape answer buttons, answer distribution after each question
- **Live leaderboard** and animated **podium** with confetti
- **Quiz builder** with live player preview, 2–4 options, per-question timer, public/private
- **Practice bots** so you can try a full game solo

## 🎨 UI / UX highlights

- **Glassmorphism design system** with animated gradient blobs, grid overlay and per-project colour theme
- **Dark / light mode** toggle (remembered per browser) — every chart re-themes instantly
- **Split-screen auth pages** with an interactive particle network, floating cards and a typing "Try demo" button
- **Motion everywhere**: staggered fade-ups, count-up numbers, animated progress bars, ripple buttons, toast notifications, modals
- **Fully responsive** — collapsible sidebar on mobile, Ctrl + K search shortcut
- Works **offline**: Chart.js, Bootstrap Icons and Poppins font are bundled in `static/`

## 🔐 Authentication & security

- **Register / Login / Logout** with salted password hashing (Werkzeug PBKDF2)
- Live **password-strength meter**, show/hide password, "remember me" sessions (14 days)
- **CSRF protection** on every form and API call, brute-force lockout after 5 failed logins
- HttpOnly + SameSite cookies, security headers, per-user data isolation
- **Profile & settings**: edit name, avatar colour, change password, delete account

## 🖼️ Screenshots

| Sign in | Register |
|---|---|
| ![login](assets/login.png) | ![register](assets/register.png) |

| | |
|---|---|
| ![player_question](assets/player_question.png) | ![host_reveal](assets/host_reveal.png) |
| ![podium](assets/podium.png) | ![quizzes](assets/quizzes.png) |
| ![builder](assets/builder.png) |  |

## 🏗️ How it works

```mermaid
flowchart LR
    S0["Host creates game"] --> S1
    S1["players join with PIN"] --> S2
    S2["questions & timer"] --> S3
    S3["answers scored"] --> S4
    S4["leaderboard"] --> S5
    S5["podium"]
```

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, SQLite |
| Frontend | HTML5, CSS3 (custom glassmorphism design system), vanilla JavaScript |
| Charts & icons | Chart.js 4, Bootstrap Icons, Poppins (bundled locally) |
| Security | Werkzeug password hashing, CSRF tokens, secure sessions |

## 📁 Project structure

```
QUIZARENA-LIVE-MULTIPLAYER/
├── app.py                 # Flask app: routes, business logic & JSON API
├── core.py                # Shared core: app factory, SQLite, auth, CSRF, profile
├── app.py                 # Game engine, state machine, REST API
├── static/game.js         # Shared host/player rendering
├── static/game.css        # Game-show styles
├── templates/             # Jinja2 pages (auth, base layout, feature pages)
├── static/                # style.css, main.js + bundled Chart.js, icons & fonts
├── assets/                # README screenshots
├── requirements.txt
└── LICENSE
```

## 🚀 Run it locally

```bash
git clone https://github.com/PreciousBharath/QUIZARENA-LIVE-MULTIPLAYER.git
cd QUIZARENA-LIVE-MULTIPLAYER
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** → click **"Try the demo account"** (`demo@example.com` / `Demo@1234`) or register your own account.
The SQLite database is created automatically in `instance/` and seeded with realistic demo data.

Open a second browser (or incognito window), register another account and join with the PIN to play live against yourself.

## ⚙️ Production tips

- Set a strong `SECRET_KEY` environment variable and run behind **gunicorn** / **waitress** with HTTPS
- `DATABASE=/path/to/app.db` overrides the database location

## 👨‍💻 Author

**Bharath** — Software Developer · Project Engineer · Technical Trainer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-connectbharath-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/connectbharath)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://itsbharathportfolio.netlify.app)
[![GitHub](https://img.shields.io/badge/GitHub-PreciousBharath-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/PreciousBharath)

⭐ If you like this project, please give it a star!

## 📄 License

Released under the [MIT License](LICENSE).
