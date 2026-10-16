import os
from uuid import uuid4
import pytest
from app.db.mongo import client_for, initialize


@pytest.fixture
def db():
    # Only ever remove a newly allocated, per-test namespace; never the configured dev DB.
    name = "survey_test_" + uuid4().hex
    client = client_for(os.getenv("TEST_MONGO_URI", "mongodb://127.0.0.1:27018/?replicaSet=rs0"))
    client.admin.command("ping")  # A missing Mongo is a failure, not a silent skip.
    database = client[name]
    initialize(database)
    yield database
    assert name.startswith("survey_test_") and len(name) == 44
    client.drop_database(name)
    client.close()
