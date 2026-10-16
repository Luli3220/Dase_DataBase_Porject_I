import argparse
import time
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError

def initialize_replica(port=27018, host=None):
    host = host or f"127.0.0.1:{port}"
    client = MongoClient(f"mongodb://127.0.0.1:{port}/?directConnection=true", serverSelectionTimeoutMS=1000)
    for attempt in range(40):
        try:
            client.admin.command("ping")
            break
        except PyMongoError:
            time.sleep(0.5)
    else: raise RuntimeError("MongoDB did not start")
    try:
        status = client.admin.command("replSetGetStatus")
        if status.get("set") != "rs0":
            raise RuntimeError("Existing replica set is not rs0; refusing to modify it")
    except OperationFailure as exc:
        if exc.code != 94: raise
        client.admin.command("replSetInitiate", {"_id": "rs0", "members": [{"_id": 0, "host": host}]})
    for attempt in range(60):
        if client.admin.command("hello").get("isWritablePrimary"):
            print(f"Replica set ready: {host}")
            client.close()
            return
        time.sleep(0.5)
    raise RuntimeError("Replica set has no writable primary")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=27018)
    parser.add_argument("--host")
    args = parser.parse_args()
    initialize_replica(args.port, args.host)
