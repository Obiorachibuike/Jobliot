import os, sys, tempfile
os.environ["CAREERPILOT_DATA_DIR"]=tempfile.mkdtemp()
sys.path.insert(0, os.path.join(os.path.dirname(__file__),".."))
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_api_token
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        c.headers.update({"x-careerpilot-token":get_api_token()}); yield c
