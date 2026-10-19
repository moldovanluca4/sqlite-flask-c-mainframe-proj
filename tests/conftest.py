import re
import secrets

import pytest

from cvt_dashboard import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": secrets.token_hex(32),
            "DATABASE": tmp_path / "snapshots.sqlite",
            "BUILD_DIR": tmp_path / "build",
        }
    )


@pytest.fixture
def post_form():
    def submit(client, path="/import", data=None):
        response = client.get("/")
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        assert match is not None
        return client.post(
            path, data={**(data or {}), "csrf_token": match.group(1)}, follow_redirects=True
        )

    return submit
