"""Flask web server for AI derivation handling."""

import base64
import hashlib
from threading import RLock

from flask import Flask, request

from .llm import query_openai_responses_api

# shared state
req_to_hash_dict: dict[str, str] = {}
hash_to_drv_dict: dict[str, str] = {}
_state_lock = RLock()  # one lock for both dicts

app = Flask(__name__)


@app.route("/hash", methods=["GET"])
def get_hash() -> str:
    with _state_lock:
        req_param = request.args.get("req", "")

        if req_param in req_to_hash_dict:
            sha256_hash = req_to_hash_dict[req_param]
        else:
            drv = query_openai_responses_api(req_param)
            # Compute sha256 hash in SRI format
            sha256_digest = hashlib.sha256(drv.encode("utf-8")).digest()
            sha256_hash = base64.b64encode(sha256_digest).decode("utf-8")

            req_to_hash_dict[req_param] = sha256_hash
            hash_to_drv_dict[sha256_hash] = drv

    return sha256_hash


@app.route("/drv", methods=["GET"])
def get_drv() -> str:
    with _state_lock:
        hash_param = request.args.get("hash", "")

        if hash_param not in hash_to_drv_dict:
            msg = f"Hash not found: {hash_param}"
            raise ValueError(msg)

    return hash_to_drv_dict[hash_param]


def main() -> None:
    app.run(host="127.0.0.1", port=5000, debug=True)  # noqa: S201


if __name__ == "__main__":
    main()
