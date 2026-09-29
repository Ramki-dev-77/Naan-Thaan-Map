# 17 — Static Data and Admin Operations

## 1. Source Files
Campus data is maintained in the bundled JSON files under `app/data/`:
- `campuses.json`, `buildings.json`, `rooms.json`, `facilities.json`, and `categories.json` hold campus entities and map geometry.
- `svce_network.json` is the primary SVCE routing graph (`nodes` and `edges`).
- `demo_network.json` holds the separate demo campus graph.
- `admins.json` contains the admin credentials in password-hash form.

## 2. Validate Changes
Edit the JSON files directly, then run:

```bash
flask --app run.py validate-data
```

The Flask process loads static files into memory when it starts. The admin interface and admin API can mutate that in-memory state, but those mutations are not written to JSON and will be lost when the process restarts or a serverless instance is replaced. To make campus or route data changes durable, update the JSON files and redeploy.
