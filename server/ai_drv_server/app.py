"""Flask web server for AI derivation handling."""

import base64
import hashlib
from threading import RLock

from flask import Flask, request

from .llm import query_openai_responses_api

# The following are used for shared state, instead of writing to a database.  One big
# downside is that these are just in memory, so they will be lost when
# restarting.
#
# TODO: Use a database or something.

# Mapping from the user's prompt to the hash of the derivation.
req_to_hash_dict: dict[str, str] = {}

# Mapping from the hash of the derivation to the derivation text.
hash_to_drv_dict: dict[str, str] = {}

# A lock to prevent concurrent access to the above dictionaries.
_state_lock = RLock()  # one lock for both dicts


app = Flask(__name__)


@app.route("/hash", methods=["GET"])
def get_hash() -> str:
    """Get the hash of the derivation for the given prompt."""
    with _state_lock:
        req_param = request.args.get("req", "")

        # If the prompt is already in the dictionary, just return the hash.
        if req_param in req_to_hash_dict:
            sha256_hash = req_to_hash_dict[req_param]
        # If the prompt is not in the dictionary, query the OpenAI API and
        # store the result.
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
    """Get the derivation text for the given hash."""
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
