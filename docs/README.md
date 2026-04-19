# BargainHunters

**CS 3200 — Spring 2026 | Northeastern University**

BargainHunters is a full-stack eBay price monitoring application. Users add eBay listings, products, or categories to a personal watchlist and receive notifications when prices drop below a configured threshold. Live pricing data is fetched in real time via the SerpAPI eBay integration.

---

## Team

| Name |
|---|---|
| Seifer Mathias |
| Jason Jathanna | 
| Ishaan Mody | 
| Nicolas Aguiar | 
---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Python · Streamlit |
| Backend API | Python · Flask (REST) |
| Database | SQLite |
| eBay Data | SerpAPI (eBay engine) |
| Containerization | Docker · Docker Compose |

---

## Repository Structure

```
TheForeignKeys/
├── app/                        Streamlit frontend
│   └── src/
│       ├── Home.py             Login / persona selection
│       ├── pages/              One file per app page
│       ├── modules/
│       │   ├── nav.py          Sidebar navigation & RBAC
│       │   └── api.py          All backend API calls (helper layer)
│       └── assets/             Static images
│
├── api/                        Flask REST API
│   ├── backend_app.py          Entry point (port 4000)
│   ├── .env.template           Environment variable template
│   └── backend/
│       ├── rest_entry.py       App factory & blueprint registration
│       ├── ebay_client.py      SerpAPI eBay wrapper
│       ├── db_connection/      Per-request MySQL connection
│       ├── alerts/             Alert routes  (/alerts)
│       ├── users/              User routes   (/u)
│       ├── watchlist/          Watchlist     (/watchlist)
│       ├── notifications/      Notifications (/notifications)
│       ├── listings/           Listings      (/listings)
│       ├── items/              Items         (/items)
│       ├── categories/         Categories    (/categories)
│       ├── feedback/           Feedback      (/feedback)
│       └── errors/             Error logging (/errors)
│
├── database-files/
│   └── BargainHuntersDDL.sql   Schema — auto-run when DB container is created
│
└── docker-compose.yaml         Orchestrates app, api, and db containers
```

---

## Setup Instructions

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install) for local Python (editor support only — the app runs in Docker)
- A [SerpAPI](https://serpapi.com) account and API key

---

Open `api/.env` and fill in every value:

```env
SECRET_KEY=<any-random-string>
DB_USER=root
DB_HOST=db
DB_PORT=3306
DB_NAME=BargainHunters
MYSQL_ROOT_PASSWORD=<choose-a-strong-password>
SERPAPI_KEY=<your-serpapi-key>
```

> `DB_HOST=db` must stay as `db` — that is the hostname Docker assigns to the MySQL container.

---


---

###  Start all containers

From the repo root:

```bash
docker compose up -d
```

This starts three containers:

| Container | Service | Host port |
|---|---|---|
| `web-app` | Streamlit frontend | http://localhost:8501 |
| `web-api` | Flask REST API | http://localhost:4000 |
| `mysql_db` | MySQL database | localhost:3200 |

The database schema in `database-files/BargainHuntersDDL.sql` is applied automatically the first time the `db` container is created.

---

### 5. Open the app

Navigate to **http://localhost:8501** in your browser.

---

### Common Docker commands

```bash
# Start all containers in the background
docker compose up -d

# Stop and remove containers (data is preserved in the mysql_data volume)
docker compose down

# Stop without removing containers
docker compose stop

# Restart a single container (e.g. after a code error)
docker compose restart api

# View logs for a container
docker compose logs api
docker compose logs app
docker compose logs db

# Rebuild containers after a Dockerfile or dependency change
docker compose up -d --build
```

---


---

## API Overview

The Flask API runs on **port 4000**. All routes return JSON.

| Prefix | Resource |
|---|---|
| `/u` | Users |
| `/alerts` | Price-drop alerts |
| `/watchlist` | User watchlists |
| `/notifications` | Notifications |
| `/listings` | eBay listings |
| `/items` | eBay items (by EPID) |
| `/categories` | eBay categories |
| `/feedback` | User feedback |
| `/errors` | Error logging |

### Key endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/u/` | Get all active users |
| POST | `/u/` | Create a user |
| GET | `/alerts/watchlist/<user_id>` | Get all alerts for a user's watchlist |
| POST | `/alerts/from-url` | Create alert from an eBay URL (fetches live price via SerpAPI) |
| PUT | `/alerts/<alert_id>` | Update alert thresholds |
| DELETE | `/alerts/<alert_id>` | Deactivate an alert |
| GET | `/watchlist/<user_id>` | Get a user's watchlist |
| DELETE | `/watchlist/<user_id>/alerts/<alert_id>` | Remove alert from watchlist |
| GET | `/notifications/<user_id>` | Get notifications for a user |
| POST | `/feedback/` | Submit feedback |

### Alert creation flow (`POST /alerts/from-url`)

1. Accepts an eBay URL, `watch_type`, and `user_id`
2. Parses the URL to extract the listing/item/category ID
3. Calls SerpAPI to fetch the current live price
4. Upserts the entity into the database
5. Creates the alert and links it to the user's watchlist
6. Returns `{ alert_id, watch_type, target_name, original_price }`

---

## Frontend Pages

| File | Purpose |
|---|---|
| `Home.py` | Login — select user persona |
| `01_alert_creation.py` | Create a price-drop alert from an eBay URL |
| `02_statistics.py` | Price history and watchlist analytics |
| `04_watchlist.py` | View and manage active alerts |
| `05_feedback.py` | Submit feedback |

---

## `modules/` Folder

| File | Purpose |
|---|---|
| `nav.py` | Sidebar navigation links and RBAC — controls which pages are visible per role |
| `api.py` | API helper layer — all HTTP calls to the Flask backend live here; pages import functions from this module and receive plain Python dicts/lists |

### Using `api.py` in a page

Pages never import `requests` or construct URLs directly — all of that is handled in `api.py`.

```python
from modules.api import get_alerts_for_user, create_alert_from_url, submit_feedback

# Fetch all alerts for the logged-in user
alerts = get_alerts_for_user(st.session_state["user_id"])

# Create an alert from an eBay URL
result = create_alert_from_url(
    ebay_url="https://www.ebay.com/itm/123456789",
    watch_type="listing",
    user_id=st.session_state["user_id"],
    drop_percent=10.0,
)
if result:
    st.success(f"Alert created for {result['target_name']} at ${result['original_price']}")

# Submit feedback
submit_feedback(content="Great app!", user_id=st.session_state["user_id"])
```

---

## Database Schema

The `BargainHunters` MySQL database contains the following tables:

| Table | Description |
|---|---|
| `users` | Registered users (`user_id`, `name`, `email`, `is_active`) |
| `alerts` | Price-drop alerts (`alert_id`, `watch_type`, `drop_amt`, `drop_percent`, `original_price`, `is_active`) |
| `watchlist` | Links users to alerts (`user_id`, `alert_id`) |
| `listings` | eBay listing records (`listing_id`, `listing_name`, `url`, `current_price`) |
| `items` | eBay product records by EPID (`item_id`, `item_name`, `url`, `current_price`) |
| `categories` | eBay category records (`cat_id`, `cat_name`, `url`, `current_price`) |
| `notifications` | Alerts sent to users (`notification_id`, `content`, `user_id`, `alert_id`, `sent_date`) |
| `feedback` | User-submitted feedback (`feedback_id`, `content`, `user_id`, `created_at`) |
| `errors` | Application error log (`error_id`, `error_desc`, `user_id`) |
