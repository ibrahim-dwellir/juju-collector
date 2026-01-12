# juju-collector

Collects Juju controller/model data and writes it to a database (and logs to console). Designed to run from cron and process multiple controllers sequentially.

## Requirements
- Python 3.10+ (asyncio)
- A reachable Juju controller
- Database accessible via SQLAlchemy-compatible URL

## Install
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

### Environment (.env)
Loaded automatically via `python-dotenv`.

Required:
- `DB_URL` — database connection URL

Optional:
- `CONFIG_FILE` — path to config file (default: `config.yaml`)
- `RECORD_QUERIES` — set to any value to log SQL queries
- `PERMITTED_IP_SCOPES` — single scope string (default: `local-cloud`)
- `PERMITTED_IP_TYPES` — single type string (default: `ipv4`)
- `PREFERRED_IP_PREFIX` — default: `192.168`
- `BANNED_IP_PREFIX` — default: `172.17`

Example:
```
DB_URL=postgresql://user:pass@host:5432/dbname
CONFIG_FILE=config.yaml
```

### Controller config file (YAML)
Default path is `config.yaml` unless `CONFIG_FILE` is set.
If your file is `.config.yaml`, set `CONFIG_FILE=.config.yaml`.

```
controllers:
  - controller: my-controller
    username: admin
    password: secret
    owner_id: 1
    cacert: |
      -----BEGIN CERTIFICATE-----
      ...
      -----END CERTIFICATE-----
```

## Run
```
python3 main.py
```
Or:
```
./entrypoint.sh
```

## Notes
- If `DB_URL` is missing, the process logs an error and exits early.
- `owner_id` in the controller config is used when creating DB entries.
- Failures in one controller do not stop processing of other controllers.
