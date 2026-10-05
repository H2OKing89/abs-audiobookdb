#!/usr/bin/env python3
"""Bounded, read-only SPIKE-001/002 probes; never save raw API responses."""

import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import signal
import shlex
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USER_AGENT = "abs-audiobookdb-spikes/0.1 (personal development by Quentin)"
RATE_HEADERS = (
    "RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset",
    "X-RateLimit-Budget", "X-RateLimit-Period", "Retry-After",
)


class StopProbe(Exception):
    pass


def deadline_expired(signum, frame):
    raise TimeoutError("request_deadline")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def load_config():
    config = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        key, sep, value = line.partition("=")
        if not sep:
            raise StopProbe("dotenv_invalid_assignment")
        parts = shlex.split(value, comments=True)
        if len(parts) > 1:
            raise StopProbe("dotenv_ambiguous_value")
        config[key.strip()] = parts[0] if parts else ""
    return config


def key_file(config, name, fallback):
    configured = config.get(name, "")
    path = Path(configured) if configured else ROOT / "secrets" / fallback
    if not path.is_absolute():
        path = ROOT / path
    key = path.read_text().strip()
    if not key or any(c.isspace() for c in key):
        raise StopProbe("credential_file_empty_or_invalid")
    return key, "configured_file" if configured else "existing_secrets_fallback"


def https_base(value):
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise StopProbe("host_requires_https_without_embedded_credentials")
    return value.rstrip("/")


def shape(value, depth=0):
    """Retain JSON field names/types only, never string or numeric values."""
    if depth >= 5:
        return type(value).__name__
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in sorted(value.items())}
    if isinstance(value, list):
        variants = []
        for item in value[:10]:
            item_shape = shape(item, depth + 1)
            if item_shape not in variants:
                variants.append(item_shape)
        return {"type": "array", "length": len(value), "sample_shapes": variants}
    return "null" if value is None else type(value).__name__


def safe_json(value, private_values):
    encoded = json.dumps(value, indent=2, sort_keys=True)
    for secret in sorted(set(private_values), key=len, reverse=True):
        if secret:
            escaped = json.dumps(secret)[1:-1]
            encoded = encoded.replace(escaped, "[REDACTED]")
    return encoded + "\n"


class Probe:
    def __init__(self, name, user_agent=USER_AGENT):
        self.name = name
        self.user_agent = user_agent
        self.private_values = []
        self.records = []
        self.calls = 0
        self.cost = 0
        self.last_request = 0.0
        self.authenticated_responses = 0
        self.transport_ok = False
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )

    def request(self, label, url, headers=None, body=None, expected=(200,), cost=0,
                limit=1048576, allow_method=None):
        method = "POST" if body is not None else "GET"
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise StopProbe("unsafe_url")
        if method == "POST" and (parsed.hostname != "audiobookdb.org"
                                  or parsed.path != "/api/search"
                                  or allow_method != "search"):
            raise StopProbe("mutation_rejected")
        maximum = 2 if self.name == "abs" else 11  # ten API calls + public spec
        if self.calls >= maximum or self.cost + cost > 20:
            raise StopProbe("request_budget_exhausted")
        delay = max(0, 0.25 - (time.monotonic() - self.last_request))
        if delay:
            time.sleep(delay)
        self.calls += 1
        self.cost += cost
        self.last_request = time.monotonic()
        request_headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        request_headers.update(headers or {})
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, headers=request_headers,
                                     data=json.dumps(body).encode() if body is not None else None)
        record = {"label": label, "method": method, "documented_cost_cap": cost}
        self.records.append(record)
        started = time.monotonic()
        previous_alarm = signal.signal(signal.SIGALRM, deadline_expired)
        signal.setitimer(signal.ITIMER_REAL, 10)
        try:
            try:
                response = self.opener.open(req, timeout=10)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                raw = response.read(limit + 1)
                record["http_status"] = response.code
                record["rate_header_names"] = [h for h in RATE_HEADERS if h in response.headers]
                self.transport_ok = True
                if response.code in (401, 403, 429) or response.code not in expected:
                    raise StopProbe("unexpected_http_status")
                if len(raw) > limit:
                    raise StopProbe("response_size_limit")
                record["response_bytes"] = len(raw)
                data = json.loads(raw)
                record["response_shape"] = shape(data)
                if headers:
                    self.authenticated_responses += 1
                return data, raw
        except urllib.error.URLError as error:
            reason = error.reason
            if isinstance(reason, socket.gaierror):
                record["failure"] = "dns_resolution_failed"
            elif isinstance(reason, ssl.SSLError):
                record["failure"] = "tls_failed"
            else:
                record["failure"] = "transport_failed"
            raise StopProbe(record["failure"]) from None
        except (TimeoutError, OSError):
            record["failure"] = "transport_failed"
            raise StopProbe(record["failure"]) from None
        except (ValueError, UnicodeError):
            record["failure"] = "invalid_json"
            raise StopProbe(record["failure"]) from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_alarm)
            record["elapsed_ms"] = round((time.monotonic() - started) * 1000)

    def run_abs(self, config):
        host = https_base(config.get("AUDIOBOOKSHELF_HOST", ""))
        key, source = key_file(config, "AUDIOBOOKSHELF_API_FILE", "audiobookshelf_api_key")
        self.private_values.extend([key, host, urllib.parse.urlsplit(host).hostname])
        self.credential_source = source
        data, _ = self.request("abs_status", host + "/status")
        version = data.get("serverVersion", data.get("version")) if isinstance(data, dict) else None
        if isinstance(version, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}(?:[-+][\w.-]+)?", version):
            self.records[-1]["installed_abs_version"] = version
        self.request("abs_authenticated_libraries", host + "/api/libraries",
                     headers={"Authorization": "Bearer " + key})

    def run_audiobookdb(self, config):
        key, source = key_file(config, "AUDIOBOOKDB_API_FILE", "audiobookdb_api_key")
        self.private_values.append(key)
        self.credential_source = source
        spec, raw = self.request("public_openapi", "https://audiobookdb.org/openapi-public.json",
                                 limit=2097152)
        # Persist provenance/contract facts, not the full schema summary.
        self.records[-1].pop("response_shape", None)
        self.records[-1]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.records[-1]["schema_version"] = spec.get("info", {}).get("version")
        paths = spec.get("paths", {})
        headers = {"X-API-Key": key}

        def api(label, path, body=None, expected=(200,), cost=1):
            route = re.sub(r"/(?:books|releases)/[^/?]+", lambda m: m.group().rsplit("/", 1)[0] + "/{id}", path.split("?")[0])
            if path.startswith("/audiobooks/external/"):
                route = "/audiobooks/external/{category}/{itemId}"
            method = "post" if body is not None else "get"
            if method not in paths.get(route, {}):
                self.records.append({"label": label, "not_run": "route_absent_from_public_spec"})
                return None
            data, _ = self.request(label, "https://audiobookdb.org/api" + path,
                                   headers=headers, body=body, expected=expected,
                                   cost=cost, allow_method="search" if body else None)
            return data

        hits = api("book_search", "/search", {"q": "the martian", "type": "books"}, cost=3)
        if not isinstance(hits, list) or not 1 <= len(hits) <= 10:
            raise StopProbe("search_shape_or_fixture_mismatch")
        book_id = hits[0].get("id") if isinstance(hits[0], dict) else None
        if not isinstance(book_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", book_id):
            raise StopProbe("book_id_not_available")
        book = api("book_detail", "/books/" + book_id)
        if not isinstance(book, dict):
            raise StopProbe("book_detail_shape_mismatch")
        releases = book.get("releases", [])
        self.records[-1]["release_count"] = len(releases) if isinstance(releases, list) else None
        authors = [edge.get("person", {}).get("name") for edge in book.get("people", [])
                   if isinstance(edge, dict) and isinstance(edge.get("role"), dict)
                   and edge["role"].get("name") == "Author"
                   and isinstance(edge.get("person"), dict)
                   and isinstance(edge["person"].get("name"), str)]
        if authors:
            filtered = api("author_filter", "/search",
                           {"q": "the martian", "type": "books",
                            "filters": {"person": authors[0], "role": "Author"}}, cost=3)
            if not isinstance(filtered, list) or not 1 <= len(filtered) <= 10:
                raise StopProbe("author_filtered_search_shape_or_fixture_mismatch")
            self.records[-1]["includes_original_book"] = any(
                isinstance(hit, dict) and hit.get("id") == book_id for hit in filtered)
            if not self.records[-1]["includes_original_book"]:
                raise StopProbe("author_filter_omitted_original_book")
        else:
            self.records.append({"label": "author_filter", "not_run": "author_relationship_unavailable"})
        for number, release in enumerate(releases[:2] if isinstance(releases, list) else []):
            release_id = release.get("id") if isinstance(release, dict) else None
            if isinstance(release_id, str) and re.fullmatch(r"[A-Za-z0-9_-]+", release_id):
                detail = api("release_detail_" + str(number + 1), "/releases/" + release_id)
                if isinstance(detail, dict):
                    ms, sec = detail.get("runtimeLengthMs"), detail.get("runtimeLengthSec")
                    if isinstance(ms, int) and isinstance(sec, int):
                        self.records[-1]["runtime_units_consistent"] = 0 <= ms - sec * 1000 < 1000
        # Only public controlled role labels are retained, not person/account data.
        roles = api("roles", "/roles?take=100", cost=2)
        if isinstance(roles, list):
            self.records[-1]["observed_role_names"] = [r["name"] for r in roles
                if isinstance(r, dict) and r.get("name") in ("Author", "Narrator", "author", "narrator")]
        categories = api("external_categories", "/external-categories", cost=2)
        if isinstance(categories, list):
            self.records[-1]["isbn_category_observations"] = [
                {"title": category["title"],
                 "allowedOnBook": category.get("allowedOnBook"),
                 "allowedOnRelease": category.get("allowedOnRelease")}
                for category in categories if isinstance(category, dict)
                and isinstance(category.get("title"), str)
                and re.fullmatch(r"ISBN(?:[- ]?(?:10|13))?", category["title"], re.I)]
        api("known_asin", "/audiobooks/external/audible/B00B5HZGUG")
        api("unknown_asin", "/audiobooks/external/audible/B000000000", expected=(404,))

    def save(self, reason=None):
        number = "001" if self.name == "abs" else "002"
        folder = ROOT / "docs" / "evidence" / ("SPIKE-" + number)
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        outcome = "Blocked" if reason and not self.transport_ok else "Incomplete" if reason else "Partial"
        result = {
            "spike": "SPIKE-" + number, "captured_at_utc": timestamp,
            "python_version": platform.python_version(), "outcome": outcome,
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "execution_environment": "ssh_session" if os.environ.get("SSH_CONNECTION") else "workspace",
            "stop_reason": reason, "credential_source": getattr(self, "credential_source", "not_loaded"),
            "attempted_requests": self.calls, "authenticated_json_responses": self.authenticated_responses,
            "attempted_documented_cost_cap": self.cost, "records": self.records,
            "limitations": "Schema summaries only. No raw payloads, credential values, private host or account data. Partial probes do not pass full spike criteria.",
        }
        path = folder / ("probe-" + timestamp + ".json")
        with path.open("x") as output:
            output.write(safe_json(result, self.private_values))
        print(self.name + ": " + outcome + (" (" + reason + ")" if reason else ""))
        print("Evidence: " + str(path.relative_to(ROOT)))
        return reason is None


def self_check():
    sentinel = "SPIKE-SECRET-SENTINEL-DO-NOT-SAVE"
    summary = shape({"user": {"name": sentinel, "email": sentinel}, "key": sentinel,
                     "rows": [{"description": sentinel, "number": 123}]})
    encoded = safe_json({"shape": summary, "failure": sentinel, sentinel: True}, [sentinel])
    assert sentinel not in encoded and "123" not in encoded
    json.loads(encoded)
    assert https_base("https://example.invalid") == "https://example.invalid"
    for invalid in ("http://example.invalid", "https://user:pass@example.invalid", "https://example.invalid?key=x"):
        try:
            https_base(invalid)
        except StopProbe:
            pass
        else:
            raise AssertionError("unsafe host accepted")
    probe = Probe("audiobookdb")
    try:
        probe.request("forbidden", "https://audiobookdb.org/api/books", body={})
    except StopProbe as error:
        assert str(error) == "mutation_rejected" and probe.calls == 0
    else:
        raise AssertionError("mutation accepted")
    previous_alarm = signal.signal(signal.SIGALRM, deadline_expired)
    try:
        signal.setitimer(signal.ITIMER_REAL, 0.01)
        try:
            time.sleep(0.1)
        except TimeoutError:
            pass
        else:
            raise AssertionError("total deadline not enforced")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_alarm)
    print("Offline checks passed: payload-value exclusion, sentinel redaction, HTTPS validation, mutation rejection, total deadline.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=("abs", "audiobookdb", "all", "self-check"))
    parser.add_argument("--user-agent", default=USER_AGENT,
                        help="Application/version and actual contact for keyed upstream requests")
    args = parser.parse_args()
    if args.target == "self-check":
        self_check()
        return 0
    okay = True
    for target in ("abs", "audiobookdb") if args.target == "all" else (args.target,):
        probe = Probe(target, args.user_agent)
        reason = None
        try:
            config = load_config()
            getattr(probe, "run_" + target)(config)
        except StopProbe as error:
            reason = str(error)
        except (OSError, ValueError):
            reason = "local_configuration_unavailable_or_invalid"
        except Exception:
            # Exception text/tracebacks can include URLs or header values.
            reason = "unexpected_local_failure"
        okay = probe.save(reason) and okay
    return 0 if okay else 1


if __name__ == "__main__":
    raise SystemExit(main())
