from __future__ import annotations

from core.secrets import secrets

def mkdir_srv():
    import os

    srv_dir = secrets.PAGE_SRV_PATH
    os.makedirs(srv_dir, exist_ok=True)
