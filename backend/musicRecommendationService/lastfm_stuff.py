import hashlib, requests
from django.conf import settings

API_ROOT = "https://ws.audioscrobbler.com/2.0/"

# Creates the signature for last.fm api calls. Proves its from a legit source/our app
# https://www.last.fm/api/webauth for more details.
def _sign(params: dict) -> str:
    base = "".join(f"{k}{params[k]}" for k in sorted(params)) + settings.LASTFM_API_SHARED_SECRET
    return hashlib.md5(base.encode("utf-8")).hexdigest()

# Exchanges a temporary token given by last.fm for a session key to keep
# So we can keep making requests on behalf of the user
def get_session(token: str) -> dict:
    params = {"method": "auth.getSession", "api_key": settings.LASTFM_API_KEY, "token": token}
    params["api_sig"] = _sign(params)
    params["format"] = "json"
    request = requests.get(API_ROOT, params=params, timeout=15)
    request.raise_for_status()
    data = request.json()

    return data["session"]