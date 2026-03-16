import json
import urllib.request

from .config import BACKEND_PORT, BRIDGE_PORT, FRONTEND_PORT


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.read().decode("utf-8")


def main() -> None:
    results = {}
    results["bridge_health"] = json.loads(_get(f"http://127.0.0.1:{BRIDGE_PORT}/health"))
    results["backend_health"] = json.loads(_get(f"http://127.0.0.1:{BACKEND_PORT}/health"))
    results["backend_ping"] = json.loads(_get(f"http://127.0.0.1:{BACKEND_PORT}/ping"))
    results["frontend"] = _get(f"http://127.0.0.1:{FRONTEND_PORT}/")[:200]
    print(json.dumps(results, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
