# BargainHunters — Spring 2026 CS 3200

BargainHunters is a full-stack eBay price monitoring application built for Dr. Fontenot's Spring 2026 CS 3200 course project.

Users add eBay listings, products, or categories to a personal watchlist and receive notifications when prices drop below a configured threshold. Live pricing data is fetched in real time via the SerpAPI eBay integration.

**Team:** Seifer Mathias · Jason Jathanna · Ishaan Mody · Nicolas Aguiar

## Prerequisites

- A GitHub Account
- A terminal-based git client or GUI Git client such as GitHub Desktop or the Git plugin for VSCode.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running on your machine.
- A distribution of Python running on your laptop. The distribution supported by the course is [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install).
  - Create a new Python 3.11 environment in `conda` named `bargain-hunters` by running:
     ```bash
     conda create -n bargain-hunters python=3.11
     ```
  - Install the Python dependencies listed in `api/requirements.txt` and `app/src/requirements.txt` into your local Python environment:
     ```bash
     cd api
     pip install -r requirements.txt
     cd ../app/src
     pip install -r requirements.txt
     ```
     > **Why install locally if everything runs in Docker?** Installing the packages locally lets your IDE (VSCode) provide autocompletion, linting, and error highlighting as you write code. The app itself always runs inside the Docker containers — the local install is just for editor support.
- A [SerpAPI](https://serpapi.com) account and API key — required for live eBay price lookups.
- VSCode with the Python Plugin installed.


## Structure of the Repo

- This repository is organized into four main directories:
  - `./app` - the Streamlit frontend app
  - `./api` - the Flask REST API (runs on port 4000)
  - `./database-files` - SQL scripts to initialize the MySQL database (`BargainHuntersDDL.sql`)
  - `./docs` - additional project documentation

- The repo also contains a `docker-compose.yaml` file that orchestrates three containers: the Streamlit frontend, the Flask API, and the MySQL database.

## Suggestion for Learning the Project Code Base

If you are not familiar with web app development, here are some suggestions for learning the code base:

1. Start by exploring the `./app` directory. `app/src/Home.py` is the entry point — it handles persona-based login and routes users to their role's home page.
1. Next, explore `app/src/modules/`. This contains two key modules:
   - `nav.py` — builds the sidebar navigation based on the logged-in user's role (RBAC).
   - `api.py` — the API helper layer. Every call to the Flask backend is defined here as a plain Python function. Pages import from this module and never call `requests` directly.
1. Then explore the `./api` directory. `api/backend/rest_entry.py` is the Flask app factory that registers all blueprints. `api/backend/ebay_client.py` handles all live eBay data fetching via SerpAPI.
1. Finally, explore `./database-files` to see the schema for the `BargainHunters` MySQL database.

## Setting Up the Repo

<details>
<summary>Setting Up a Personal Sandbox Repo (Optional)</summary>

### Setting Up a Personal Sandbox Repo (Optional)

**Before you start**: You need to have a GitHub account and a terminal-based git client or GUI Git client such as GitHub Desktop or the Git plugin for VSCode.

1. Clone this repo to your local machine.
   1. Click the green "Code" button on the top right of the repo page and copy the URL. Then run `git clone <URL>` in your terminal.
   1. Or use the GitHub Desktop app to clone the repo.
1. Open the repository folder in VSCode.
1. Set up the `.env` file in the `api` folder based on the `.env.template` file.
   1. Make a copy of `.env.template` and name it `.env`.
   1. Fill in all values — DB credentials, a secret key, and your `SERPAPI_KEY`.
1. For running the testing containers (for your personal repo), use `sandbox.yaml`:
   1. `docker compose -f sandbox.yaml up -d` to start all the containers in the background
   1. `docker compose -f sandbox.yaml down` to shutdown and delete the containers
   1. `docker compose -f sandbox.yaml up db -d` to only start the database container
   1. `docker compose -f sandbox.yaml stop` to "turn off" the containers but not delete them.
</details>

### Setting Up Your Team's Repo

**Before you start**: One person needs to assume the role of _Team Project Repo Owner_.

1. Clone the team repo to your local machine.
1. Set up the `.env` file in the `api` folder based on `.env.template`:
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
1. For running the team containers:
   1. `docker compose up -d` to start all the containers in the background
   1. `docker compose down` to shutdown and delete the containers
   1. `docker compose up db -d` to only start the database container
   1. `docker compose stop` to "turn off" the containers but not delete them.

Once running, the app is available at **http://localhost:8501**.

**Note:** You can also use the Docker Desktop GUI to start and stop the containers after the first initial run.

## Important Tips

1. In general, any changes you make to the API code base (REST API) or the Streamlit app code should be *hot reloaded* when files are saved.
   1. Don't forget to click the **Always Rerun** button in the browser tab of the Streamlit app for it to reload with changes.
   1. Sometimes, a bug in the code will shut the containers down. Fix the bug, then restart the container in Docker Desktop or run `docker compose restart`.
1. The MySQL Container is different.
   1. When the MySQL container is ***created*** the first time, it will execute `BargainHuntersDDL.sql` from the `./database-files` folder automatically.
   1. The MySQL Container's log files are your friend! Access them in Docker Desktop by going to the MySQL container and clicking the `Logs` tab. Search for `Error` to find issues quickly.
   1. If you need to update anything in your SQL files, you **MUST** recreate the MySQL container:
      ```bash
      docker compose down db -v && docker compose up db -d
      ```
      1. `docker compose down db -v` stops and deletes the MySQL container and its volume.
      1. `docker compose up db -d` creates a new db container and re-runs the SQL files.

## Handling User Role Access and Control

BargainHunters uses a simple Role-Based Access Control (RBAC) system in Streamlit. When a user selects a persona on the login page, their role is stored in `session_state` and controls which sidebar links and pages they can access.

### How RBAC Works in This Project

1. The standard Streamlit sidebar navigation is turned off via `app/src/.streamlit/config.toml` so we can control it manually.
1. `app/src/modules/nav.py` defines a `SideBarLinks()` function that reads the role from `session_state` and renders only the relevant page links for that role.
1. `app/src/Home.py` presents persona-selection buttons. Clicking one sets `session_state["role"]`, `session_state["authenticated"]`, and `session_state["user_id"]`, then redirects to that role's home page.
1. Every page calls `SideBarLinks()` near the top to enforce consistent navigation across the app.
1. Pages are numbered by role: `0x_` pages are for the BargainHunter role, and higher-numbered pages are for admin or other roles.

## API Helper Layer (`modules/api.py`)

All communication between the Streamlit frontend and the Flask backend is centralized in `app/src/modules/api.py`. Pages import named functions from this module and receive plain Python dicts or lists — no `requests` logic lives in any page file.

```python
from modules.api import get_alerts_for_user, create_alert_from_url

# Get all alerts for the logged-in user
alerts = get_alerts_for_user(st.session_state["user_id"])

# Create an alert from an eBay URL
result = create_alert_from_url(
    ebay_url="https://www.ebay.com/itm/123456789",
    watch_type="listing",
    user_id=st.session_state["user_id"],
    drop_percent=10.0,
)
```

Functions return `None` or `[]` on failure so pages can handle errors gracefully with a simple `if result:` check.
