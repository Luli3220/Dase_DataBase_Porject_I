"""Idempotent schema/index upgrade: hashes prove the four original collections unchanged."""
import hashlib
import json
from bson.json_util import dumps, CANONICAL_JSON_OPTIONS
from app.core.config import Settings
from app.db.mongo import client_for, initialize


def fingerprint(db):
    result = {}
    for name in ('users', 'surveys', 'survey_versions', 'submissions'):
        digest, count = hashlib.sha256(), 0
        for doc in db[name].find().sort('_id', 1):
            digest.update(dumps(doc, json_options=CANONICAL_JSON_OPTIONS, sort_keys=True).encode())
            count += 1
        result[name] = {'count': count, 'sha256': digest.hexdigest()}
    return result


def migrate(db):
    before = fingerprint(db)
    initialize(db)
    after = fingerprint(db)
    if before != after:
        raise RuntimeError('Old document fingerprint changed; investigate concurrent writes before retrying')
    return {'database': db.name, 'oldDocumentsUnchanged': True, 'before': before, 'after': after,
            'collections': sorted(db.list_collection_names())}


if __name__ == '__main__':
    cfg = Settings()
    with client_for(cfg.mongo_uri) as client:
        print(json.dumps(migrate(client[cfg.mongo_db]), indent=2))
