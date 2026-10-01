"""Arranque local: `python -m app`.

Puerto y host por APP_PORT y APP_HOST (por defecto 127.0.0.1:8765).
"""

import uvicorn

from app.config import get_settings


def main() -> None:
    s = get_settings()
    print(f"Control Tower en http://{s.app_host}:{s.app_port}")
    uvicorn.run("app.main:app", host=s.app_host, port=s.app_port)


if __name__ == "__main__":
    main()
