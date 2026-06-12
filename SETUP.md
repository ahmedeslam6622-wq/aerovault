# AeroVault — Setup Guide

## What you need installed first
- **Python 3.10+** — https://python.org/downloads
- **Node.js 18+** — https://nodejs.org

That's it. No database to install. No docker. No config files to edit.

---

## Step 1 — Start the backend

Open a terminal, navigate to the `backend` folder, and run:

```
cd aerovault/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

You'll see output like this:

```
✅  Database tables ready.
════════════════════════════════════════════════════
  SUPERUSER CREDENTIALS
════════════════════════════════════════════════════
  Username : superuser
  Password : AeroVault@2024!
  TOTP URI : otpauth://totp/...
  Current TOTP code: 481920  (valid ~30s)

  ➜  Scan the QR code with Google Authenticator
     (QR saved to: backend/superuser_totp_qr.png)
════════════════════════════════════════════════════

✅  Seed complete. System ready.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**For superuser login:** Open `backend/superuser_totp_qr.png` and scan it
with Google Authenticator on your phone. Done — you'll always have a code.

---

## Step 2 — Start the frontend

Open a **second terminal** and run:

```
cd aerovault/frontend
npm install
npm run dev
```

You'll see:

```
  VITE v5.x.x  ready in 300ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

---

## Step 3 — Open in browser

Go to: **http://localhost:5173**

The login page will appear.

---

## Access from other devices (phone, tablet, other PC)

Your computer and the device must be on the same Wi-Fi network.

Look at the `Network:` line in the frontend terminal output — it shows your
computer's local IP address, e.g. `http://192.168.1.45:5173`

Type that address into any browser on any device on your network.
Works on iPhone, Android, iPad, any browser — no installation needed.

---

## Accounts

| Username         | Password        | Role              |
|------------------|-----------------|-------------------|
| superuser        | AeroVault@2024! | Superuser (+ TOTP)|
| ahmed.hassan     | Admin#Cairo1    | Admin             |
| sara.ibrahim     | Admin#Cairo2    | Admin             |
| omar.nasser      | Flight@Ops1     | Flight Manager    |
| layla.khalil     | Flight@Ops2     | Flight Manager    |
| mahmoud.sayed    | Maint#Chief1    | Maint. Chief      |
| hana.mostafa     | Maint#Chief2    | Maint. Chief      |
| karim.ali        | Worker@Cairo1   | Viewer            |
| nour.ramadan     | Worker@Cairo2   | Viewer            |
| youssef.mansour  | Worker@Cairo3   | Viewer            |

---

## Role permissions

| Role              | Can do                                                         |
|-------------------|----------------------------------------------------------------|
| Viewer            | View all flights, crew, maintenance                            |
| Flight Manager    | + Edit flight status, gate, delay, assign crew                 |
| Maintenance Chief | + Update maintenance tasks, sign off work                      |
| Admin             | + Manage users, change roles, view system stats                |
| Superuser         | Everything, including assigning superuser role                 |

---

## Data loaded (realistic Cairo operations)

**Flights:** MS986 (CAI→LHR departed), MS777 (CAI→JFK en route), MS200
(CAI→DXB boarding), MS760 (CAI→CDG delayed 55min), MS399 (CANCELLED — AOG),
EK927 (DXB→CAI landed), TK590 (IST→CAI approaching), LH586 (FRA→CAI on
ground), and more.

**Fleet:** 9 aircraft — EgyptAir B737-800 ×2, A320 ×2, B777-300ER ×2,
A330-343; plus Emirates B777 and Turkish B737 on visit. SU-GED is AOG
(hydraulic fault, AOG-2024-0089).

**Crew:** 16 staff — 3 captains, 3 FOs, 1 second officer, 2 pursers, 4
cabin crew, 1 dispatcher, 2 ground agents. All with type ratings, hours,
licenses.

**Maintenance:** A-check scheduled, engine borescope in progress, AOG
hydraulic repair, C3-check upcoming, AD compliance completed. 3 open MEL
items. 1 active AOG record.

---

## Stopping the servers

Press `Ctrl+C` in each terminal window.

The database is saved as `backend/aerovault.db`. Delete it to reset
everything back to the seed data on next run.
