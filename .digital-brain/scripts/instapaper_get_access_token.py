#!/usr/bin/env python3
"""Helper script to complete OAuth flow and get access tokens for Instapaper."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import requests
    from requests_oauthlib import OAuth1
except ImportError:
    print("Error: Required packages not installed.", file=sys.stderr)
    print("Install with: pip install requests requests-oauthlib", file=sys.stderr)
    sys.exit(1)


def get_access_token(username: str, password: str, consumer_key: str, consumer_secret: str) -> tuple[str, str]:
    """Get access token using xAuth (simplified OAuth for password-based apps).

    Instapaper supports xAuth which allows direct username/password exchange for tokens.
    """
    url = "https://www.instapaper.com/api/1/oauth/access_token"

    # Create OAuth1 session with consumer credentials
    auth = OAuth1(
        consumer_key,
        consumer_secret,
        signature_type='AUTH_HEADER'
    )

    # xAuth parameters
    data = {
        'x_auth_username': username,
        'x_auth_password': password,
        'x_auth_mode': 'client_auth'
    }

    response = requests.post(url, auth=auth, data=data)

    if response.status_code != 200:
        raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")

    # Parse response (format: oauth_token=...&oauth_token_secret=...)
    from urllib.parse import parse_qs
    tokens = parse_qs(response.text)

    access_token = tokens['oauth_token'][0]
    access_token_secret = tokens['oauth_token_secret'][0]

    return access_token, access_token_secret


def main() -> int:
    """Main entry point."""
    print("Instapaper OAuth Access Token Generator")
    print("=" * 50)
    print()

    # Load config to get consumer credentials
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / ".digital-brain" / "instapaper_config.json"

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        return 1

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    consumer_key = config["oauth"]["consumer_key"]
    consumer_secret = config["oauth"]["consumer_secret"]

    # Get username and password
    print("Enter your Instapaper credentials:")
    print("(These are used once to get access tokens, then not stored)")
    print()

    username = input("Email/Username: ").strip()

    import getpass
    password = getpass.getpass("Password: ")

    print()
    print("Getting access tokens...")

    try:
        access_token, access_token_secret = get_access_token(
            username, password, consumer_key, consumer_secret
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print("Success! Access tokens obtained.")
    print()

    # Update config file
    config["oauth"]["access_token"] = access_token
    config["oauth"]["access_token_secret"] = access_token_secret

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Configuration updated: {config_path}")
    print()
    print("You can now run the import script:")
    print("  .digital-brain/scripts/instapaper_import.py --dry-run --limit 5")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
