"""Run from project root: python -m scripts.init_db."""
from app.core.config import Settings
from app.db.mongo import client_for, initialize

if __name__ == "__main__":
    settings = Settings()
    with client_for(settings.mongo_uri) as client:
        hello = client.admin.command("hello")
        if not hello.get("setName"):
            raise SystemExit("MongoDB must be a replica set. See README or scripts/start-local.ps1.")
        initialize(client[settings.mongo_db])
        print(f"Initialized {settings.mongo_db}: validators and indexes; no data deleted.")
