# BargainHunters — Project Design Document

**Team:** The Foreign Keys
**Course:** CS3200 (Spring 2026)

---

## Overview

BargainHunters is a web-based eBay price tracking and alert system. Users can watch eBay listings, items, and categories and receive notifications when prices drop by a specified amount or percentage. A data analyst role provides export and keyword analysis tooling. A system administrator role manages users and monitors system health.

---

## Tech Stack

| Layer | Technology | Port |
|---|---|---|
| Frontend | Streamlit (Python 3.11) | 8501 |
| Backend | Flask REST API (Python 3.11) | 4000 |
| Database | MySQL 9 | 3306 (host: 3200) |
| Infrastructure | Docker + Docker Compose | — |

All three services run as Docker containers orchestrated via `docker-compose.yaml`.

---

## System Architecture

```
┌─────────────────────┐         HTTP (port 4000)        ┌─────────────────────┐
│   Streamlit App     │  ──────────────────────────────► │   Flask REST API    │
│   (port 8501)       │ ◄──────────────────────────────  │   (port 4000)       │
└─────────────────────┘         JSON responses           └────────┬────────────┘
                                                                   │ MySQL connector
                                                                   │ (port 3306)
                                                         ┌─────────▼────────────┐
                                                         │   MySQL 9 Database   │
                                                         │   BargainHunters DB  │
                                                         └──────────────────────┘
```

**Request flow:**
1. User opens the Streamlit app and selects a role on `Home.py`.
2. Role is stored in `st.session_state['role']`.
3. The sidebar (`modules/nav.py`) renders role-appropriate navigation links.
4. Pages make HTTP requests to the Flask API on port 4000.
5. Flask queries MySQL via a request-scoped connection pool and returns JSON.
6. Streamlit renders the response.

> There is no real authentication — role selection is mocked for course purposes.

---

## Directory Structure

```
BargainHunters/
├── api/
│   ├── backend/
│   │   ├── db_connection/        # MySQL connection pool (request-scoped via Flask g)
│   │   ├── ml_models/            # ML model integration
│   │   ├── users/                # Blueprint: user routes
│   │   ├── alerts/               # Blueprint: alert routes
│   │   ├── watchlist/            # Blueprint: watchlist routes
│   │   ├── listings/             # Blueprint: listing routes
│   │   ├── items/                # Blueprint: item routes
│   │   ├── categories/           # Blueprint: category routes
│   │   ├── notifications/        # Blueprint: notification routes
│   │   ├── feedback/             # Blueprint: feedback routes
│   │   ├── errors/               # Blueprint: error routes
│   │   ├── ebay/                 # Blueprint: eBay API proxy routes
│   │   └── analyst/              # Blueprint: analyst export routes
│   ├── rest_entry.py             # Flask app factory + blueprint registration
│   ├── backend_app.py            # Entry point
│   └── requirements.txt
├── app/
│   └── src/
│       ├── Home.py               # Login / role selection page
│       ├── modules/nav.py        # Role-based sidebar navigation
│       └── pages/                # One .py file per page (numbered for ordering)
├── database-files/               # SQL init scripts (DDL + seed data)
├── datasets/                     # Data files
├── ml-src/                       # ML notebooks/scripts
├── docker-compose.yaml
└── DESIGN.md
```

---

---

## Frontend Pages

Page files live in `app/src/pages/`. The number prefix controls sidebar ordering — the first digit indicates the role group.

### Regular User (`0x` prefix)

| File | Page Name | Description |
|---|---|---|
| `00_User_Home.py` | User Home | Landing page for the user role |
| `01_My_Watchlist.py` | My Watchlist | View and manage watchlists |
| `02_My_Alerts.py` | My Alerts | Create, edit, and deactivate alerts |
| `03_My_Notifications.py` | My Notifications | View price drop notifications |
| `04_Submit_Feedback.py` | Submit Feedback | Submit feedback form |

---

## API Routes

All routes are registered as Flask Blueprints in `rest_entry.py`. All responses are JSON.

### Users — `/u`

| Method | Route | Description |
|---|---|---|
| GET | `/u/` | Get all users |
| GET | `/u/<user_id>` | Get one user by ID |
| POST | `/u/` | Create a new user |
| PUT | `/u/<user_id>` | Update user info |
| DELETE | `/u/<user_id>` | Deactivate user (sets `is_active = FALSE`) |

### Watchlist — `/watchlist`

| Method | Route | Description |
|---|---|---|
| GET | `/watchlist/<user_id>` | Get all watchlist alerts for a user |
| POST | `/watchlist/` | Add an alert to a user's watchlist |
| DELETE | `/watchlist/<user_id>/alerts/<alert_id>` | Remove a specific alert from a user's watchlist |

**`DELETE /watchlist/<user_id>/alerts/<alert_id>` — server-side logic:**
Remove the user/alert watchlist row and deactivate the alert for that user.
1. Verify the watchlist row exists for the given `user_id` and `alert_id` — return `404` if not found.
2. Delete the watchlist row.
3. Set `is_active = FALSE` on the alert.

### Alerts — `/alerts`

| Method | Route | Description |
|---|---|---|
| GET | `/alerts/watchlist/<user_id>` | Get all alerts for a user's watchlist |
| GET | `/alerts/<alert_id>` | Get one alert by ID |
| POST | `/alerts/` | Create a new alert |
| POST | `/alerts/from-url` | Create an alert from an eBay URL (see below) |
| PUT | `/alerts/<alert_id>` | Update alert (thresholds, is_active) |
| DELETE | `/alerts/<alert_id>` | Deactivate alert (sets `is_active = FALSE`) |

#### `POST /alerts/from-url`

Accepts an eBay URL and alert configuration, fetches entity data from the eBay Browse API, upserts the entity into the local DB, and creates the alert in one transaction.

**Request body:**
```json
{
  "ebay_url":   "https://www.ebay.com/itm/123456789",
  "watch_type": "listing",
  "user_id":    4,
  "drop_amt":   10.00,
  "drop_percent": null
}
```

**Server-side logic:**
1. Parse the eBay entity ID from `ebay_url` based on `watch_type`:
   - `listing` → extract ID from `/itm/<id>`
   - `item` → extract ID from `/b/<name>/<id>`
   - `category` → extract category ID from URL query params
2. Call the eBay Browse API with the extracted ID to fetch name, current price, and URL.
3. Upsert the entity into `listings`, `items`, or `categories` via `INSERT ... ON DUPLICATE KEY UPDATE`.
4. Store the fetched current price as `original_price` on the alert (baseline for future comparisons).
5. Insert the alert row into `alerts` with the appropriate FK (`item_id`, `cat_id`, or `listing_id`) and nulls for the other two.
6. Insert a watchlist row for (`user_id`, `alert_id`).

**Response (201):**
```json
{
  "alert_id":      12,
  "watch_type":    "listing",
  "target_name":   "Apple AirPods Pro 2nd Gen",
  "original_price": 189.99,
  "drop_amt":      10.00,
  "drop_percent":  null,
  "date_started":  "2026-04-06T14:00:00"
}
```

**Error responses:**
- `400` — missing required fields or unparseable URL
- `404` — eBay API returned no entity for the extracted ID
- `502` — eBay API unreachable

### Notifications — `/notifications`

| Method | Route | Description |
|---|---|---|
| GET | `/notifications/<user_id>` | Get all notifications for a user |
| POST | `/notifications/` | Create a notification (internal use) |

### Listings — `/listings`

| Method | Route | Description |
|---|---|---|
| GET | `/listings/` | Get all listings |
| GET | `/listings/<listing_id>` | Get one listing by ID |
| POST | `/listings/` | Upsert a listing from eBay API |

### Items — `/items`

| Method | Route | Description |
|---|---|---|
| GET | `/items/` | Get all items |
| GET | `/items/<item_id>` | Get one item by ID |
| POST | `/items/` | Upsert an item from eBay API |

### Categories — `/categories`

| Method | Route | Description |
|---|---|---|
| GET | `/categories/` | Get all categories |
| GET | `/categories/<cat_id>` | Get one category by ID |
| POST | `/categories/` | Upsert a category from eBay API |

### Feedback — `/feedback`

| Method | Route | Description |
|---|---|---|
| GET | `/feedback/` | Get all feedback (analyst) |
| POST | `/feedback/` | Submit new feedback (user) |

### Errors — `/errors`

| Method | Route | Description |
|---|---|---|
| GET | `/errors/` | Get all errors (admin) |
| GET | `/errors/user/<user_id>` | Get errors for a specific user |
| POST | `/errors/` | Log a new error |

### eBay — `/ebay`

Thin proxy to `ebay_client.py` (SerpAPI wrapper). Returns live eBay data without writing to the database. Useful for looking up entity details before creating an alert.

| Method | Route | Query Param | Description |
|---|---|---|---|
| GET | `/ebay/listing` | `listing_id=<int>` | Fetch a single eBay listing by legacy item number |
| GET | `/ebay/item` | `item_id=<int>` | Fetch eBay product listings by EPID (lowest-priced result) |
| GET | `/ebay/category` | `cat_id=<int>` | Fetch the cheapest listing in a given eBay category |

**Response (200):**
```json
{
  "id": 123456789,
  "name": "Apple AirPods Pro 2nd Gen",
  "url": "https://www.ebay.com/itm/123456789",
  "current_price": 189.99,
  "in_stock": true
}
```

**Error responses:**
- `400` — missing required query parameter
- `502` — SerpAPI / eBay API unreachable

---

## Frontend Design (Streamlit)

The frontend is a multi-page Streamlit app. Each page is a `.py` file in `app/src/pages/` and communicates exclusively with the Flask API — it never queries MySQL directly.

### User Selection (No Auth)

Since there is no authentication, the user is identified by selecting themselves from a dropdown on `Home.py`. The selected `user_id` is stored in `st.session_state['user_id']` and used by every subsequent page to scope API requests. See Key Design Decisions for more detail.

### General Page Pattern

Every page follows this structure:
1. Read `st.session_state['user_id']` — redirect to `Home.py` if not set.
2. Make HTTP requests to the Flask API using the `requests` library.
3. Render the JSON response using Streamlit components (`st.dataframe`, `st.table`, `st.metric`, form inputs, etc.).

### Pages

#### `Home.py` — Landing / User Selection
- A dropdown is populated from `GET /u/` showing all active users.
- On selection, `user_id` is stored in `st.session_state`.
- Navigates to `00_My_Alerts.py`.

#### `00_My_Alerts.py` — My Alerts
The main page. Acts as the user's watchlist view by listing all alerts tied to their `user_id`.

- Fetches all alerts via `GET /alerts/watchlist/<user_id>`.
- Displays each alert in a table showing: target name, watch type, threshold (`drop_amt` or `drop_percent`), original price, date started, and active status.
- User can deactivate or reactivate any alert via `PUT /alerts/<alert_id>`.
- User can delete an alert via `DELETE /watchlist/<user_id>/alerts/<alert_id>`, which removes the watchlist row and sets `is_active = FALSE` on the alert.
- Link/button to navigate to the Add Alert page.

#### `01_Add_Alert.py` — Add Alert
Form page for creating a new alert from an eBay URL.

- Text input for the eBay URL.
- Selectbox for `watch_type` (`listing`, `item`, `category`).
- Radio button to select alert type:
  - **Watch for price drop ($)** → shows a number input for `drop_amt`, sets `drop_percent` to NULL.
  - **Watch for price drop (%)** → shows a number input for `drop_percent`, sets `drop_amt` to NULL.
  - **Watch for back in stock** → both `drop_amt` and `drop_percent` sent as NULL.
- On submit, calls `POST /alerts/from-url`.
- On success, displays the resolved target name and original price as confirmation before redirecting back to My Alerts.
- On error (bad URL, eBay API failure), displays an appropriate error message.

#### `02_Submit_Feedback.py` — Submit Feedback
- Single `st.text_area` for feedback content.
- On submit, calls `POST /feedback/` with `user_id` and `content`.
- Displays a success confirmation on submit.

### Page File Summary

| File | Page Name | Key API Calls |
|---|---|---|
| `Home.py` | Home / User Select | `GET /u/` |
| `00_My_Alerts.py` | My Alerts | `GET /alerts/watchlist/<user_id>`, `PUT /alerts/<alert_id>` |
| `01_Add_Alert.py` | Add Alert | `POST /alerts/from-url` |
| `02_Submit_Feedback.py` | Submit Feedback | `POST /feedback/` |

---

## Notification Service

The notification service is a **fourth Docker container** that runs independently of the Flask API. It checks all active alerts every hour and sends an email if a price drop condition is met.

### Container

```
notifier/
├── notifier.py        # Main scheduler + check logic
├── requirements.txt   # APScheduler, mysql-connector-python, smtplib (stdlib)
└── Dockerfile
```

Added to `docker-compose.yaml` alongside the existing three services. The container connects directly to MySQL on port 3306 — it does not go through the Flask API.

### Schedule

Uses **APScheduler** (`BlockingScheduler`) to trigger the check job every hour:

```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(check_alerts, 'interval', hours=1)
scheduler.start()
```

### Alert Check Logic

Each run of `check_alerts()`:

1. Query all alerts where `is_active = TRUE` and `date_ended IS NULL`.
2. For each alert, fetch the current eBay price via the eBay API using the alert's target (`item_id`, `listing_id`, or `cat_id`).
3. Compare current price against the alert threshold:
   - If `drop_amt` is set: trigger if `current_price <= original_price - drop_amt`
   - If `drop_percent` is set: trigger if `current_price <= original_price * (1 - drop_percent / 100)`
4. If triggered:
   - Insert a row into `notifications` (content, `sent_date`, `user_id`, `alert_id`).
   - Send an email to the user via SMTP.

### Email Sending

Uses Python's built-in `smtplib` with `ssl` for a secure SMTP connection (e.g. Gmail on port 465).

```python
import smtplib, ssl
from email.mime.text import MIMEText

def send_email(to_address, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_address
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_address, msg.as_string())
```

SMTP credentials are passed in via environment variables in `docker-compose.yaml` — never hardcoded.

### Environment Variables

| Variable | Description |
|---|---|
| `SMTP_HOST` | SMTP server hostname (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (e.g. `465`) |
| `SMTP_USER` | Sender email address |
| `SMTP_PASSWORD` | Sender email password / app password |
| `DB_HOST` | MySQL host (Docker service name) |
| `DB_PORT` | MySQL port (3306) |
| `DB_USER` | MySQL user |
| `DB_PASSWORD` | MySQL password |
| `DB_NAME` | `BargainHunters` |

---

## External API Integration (eBay)

`item_id`, `listing_id`, and `cat_id` are sourced directly from the eBay API — they are **not auto-generated** by the database.

**Upsert strategy:** When a user adds a watch target, the app fetches the entity from eBay and writes it to the local DB using:

```sql
INSERT INTO items (item_id, item_name, url, current_price, is_active)
VALUES (%s, %s, %s, %s, TRUE)
ON DUPLICATE KEY UPDATE
    item_name     = VALUES(item_name),
    url           = VALUES(url),
    current_price = VALUES(current_price);
```

The same pattern applies to `listings` and `categories`.

**Data fetched from eBay per entity type:**

| Entity | Fields pulled | Price behavior |
|---|---|---|
| Listing | `listing_id`, `listing_name`, `url`, `current_price` | Fetched directly from the listing |
| Item | `item_id`, `item_name`, `url`, `current_price` | Set to the best (lowest) price across all listings for that item |
| Category | `cat_id`, `cat_name`, `url`, `current_price` | Set to the best (lowest) price across all listings in that category |

**`original_price` on alert creation:** When a user creates an alert via `POST /alerts/from-url`, the `current_price` fetched from eBay at that moment is stored as `original_price` on the alert row. This serves as the baseline for all future price drop comparisons by the notifier service.

---

## Notification System

Notifications are generated by the notifier service (a separate Docker container) which runs every hour independently of the Flask app. When a condition is met, the user receives an email and a row is inserted into the `notifications` table for record keeping.

### Trigger Conditions

For each active alert, the notifier evaluates conditions differently depending on `watch_type`:

- **`watch_type = 'listing'`** — checks the single listing's `current_price` directly against the alert threshold.
- **`watch_type = 'item'` or `watch_type = 'category'`** — searches **every listing** under that item or category via the eBay API. The condition is evaluated per listing:
  - **`drop_amt` is set** — trigger if any listing's `current_price <= original_price - drop_amt`
  - **`drop_percent` is set** — trigger if any listing's `current_price <= original_price * (1 - drop_percent / 100)`
  - **Both NULL (in-stock alert)** — trigger if any listing under the item/category comes back in stock

When a condition is met on an item or category alert, the email notification includes which specific listing(s) triggered it.

---

## Database Schema

### `users`
Stores registered users. Users are **never deleted**, only deactivated via `is_active`.

| Column | Type | Notes |
|---|---|---|
| user_id | INT PK AUTO_INCREMENT | |
| name | VARCHAR(100) | |
| email | VARCHAR(255) | UNIQUE |
| is_active | BOOLEAN | DEFAULT TRUE |
| date_joined | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### `errors`
Logs errors experienced by users.

| Column | Type | Notes |
|---|---|---|
| error_id | INT PK AUTO_INCREMENT | |
| error_desc | TEXT | |
| user_id | INT FK → users | ON DELETE CASCADE (safety net only) |

### `feedback`
Stores user-submitted feedback. Used for keyword analysis.

| Column | Type | Notes |
|---|---|---|
| feedback_id | INT PK AUTO_INCREMENT | |
| content | TEXT | |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| user_id | INT FK → users | ON DELETE CASCADE |

### `user_activity`
Event log of user actions in the app.

| Column | Type | Notes |
|---|---|---|
| event_id | INT PK AUTO_INCREMENT | |
| event_type | VARCHAR(100) | |
| event_timestamp | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| user_id | INT FK → users | ON DELETE CASCADE |

### `categories`
eBay categories. PKs sourced from eBay API — no AUTO_INCREMENT.

| Column | Type | Notes |
|---|---|---|
| cat_id | INT PK | Sourced from eBay API |
| cat_name | VARCHAR(255) | |
| url | VARCHAR(2048) | |
| is_active | BOOLEAN | DEFAULT TRUE |
| current_price | DECIMAL(10,2) UNSIGNED | Nullable — latest price fetched from eBay API |

### `items`
eBay items. PKs sourced from eBay API — no AUTO_INCREMENT.

| Column | Type | Notes |
|---|---|---|
| item_id | INT PK | Sourced from eBay API |
| item_name | VARCHAR(255) | |
| url | VARCHAR(2048) | |
| is_active | BOOLEAN | DEFAULT TRUE |
| current_price | DECIMAL(10,2) UNSIGNED | Nullable — latest price fetched from eBay API |

### `listings`
eBay listings. PKs sourced from eBay API — no AUTO_INCREMENT.

| Column | Type | Notes |
|---|---|---|
| listing_id | INT PK | Sourced from eBay API |
| listing_name | VARCHAR(255) | |
| url | VARCHAR(2048) | |
| is_active | BOOLEAN | DEFAULT TRUE |
| current_price | DECIMAL(10,2) UNSIGNED | Nullable — latest price fetched from eBay API |

### `watchlist`
A watchlist is a junction table between users and alerts. A user's watchlist is all rows with their `user_id`.

| Column | Type | Notes |
|---|---|---|
| last_checked | DATETIME | Nullable |
| user_id | INT FK → users | ON DELETE CASCADE |
| alert_id | INT FK → alerts | ON DELETE CASCADE |
| PRIMARY KEY | (`user_id`, `alert_id`) | Composite PK |

### `alerts`
Core table. Targets exactly one of: item, category, or listing.

| Column | Type | Notes |
|---|---|---|
| alert_id | INT PK AUTO_INCREMENT | |
| watch_type | ENUM('item','category','listing') | Discriminator |
| date_started | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| date_ended | DATETIME | Nullable |
| is_active | BOOLEAN | DEFAULT TRUE |
| drop_amt | DECIMAL(10,2) | Nullable — dollar threshold |
| drop_percent | DECIMAL(5,2) | Nullable — percent threshold |
| original_price | DECIMAL(10,2) | Nullable — price at time of alert creation; baseline for drop comparisons |
| item_id | INT FK → items | Nullable, ON DELETE SET NULL |
| cat_id | INT FK → categories | Nullable, ON DELETE SET NULL |
| listing_id | INT FK → listings | Nullable, ON DELETE SET NULL |

### `notifications`
Generated when a price drop condition is met.

| Column | Type | Notes |
|---|---|---|
| notification_id | INT PK AUTO_INCREMENT | |
| content | TEXT | |
| sent_date | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| user_id | INT FK → users | ON DELETE CASCADE |
| alert_id | INT FK → alerts | ON DELETE CASCADE |

---

## Analyst Export Queries

The six standard analyst queries run directly against the database and are exposed through the existing resource endpoints (activity, feedback, errors, listings, items, categories) rather than a dedicated analyst blueprint.

---

## Key Design Decisions & Constraints

- **Users are never hard-deleted.** Set `is_active = FALSE` to deactivate. `ON DELETE CASCADE` on FKs is a safety net only.
- **eBay API is the source of truth** for `item_id`, `listing_id`, and `cat_id`. Use `INSERT ... ON DUPLICATE KEY UPDATE` when syncing.
- **Watchlist is a junction table.** The primary key is (`user_id`, `alert_id`); a user's watchlist is the set of rows with that `user_id`.
- **Exclusive alert target:** An alert watches exactly one of: item, category, or listing. The unused two FK columns are NULL. Enforced at the app layer via the `watch_type` ENUM discriminator — no DB-level CHECK constraint.
- **Both `drop_amt` and `drop_percent` are nullable** on alerts. The app populates whichever the user configured. If **both are NULL**, the alert is an **in-stock alert** — the notifier triggers when the target item/listing/category comes back in stock rather than on a price drop.
- **Notifications are not a junction table.** A notification has a direct FK to both `users` and `alerts` — one notification maps to one alert trigger.
- **No real authentication.** The user is identified by selecting themselves from a dropdown on `Home.py`. `user_id` is stored in `st.session_state['user_id']` for the session.