"""One door for every request that leaves the machine: https only, and a redirect cannot change that.

urllib follows a redirect from https to http or ftp on its own, so an https-only download could be turned
into a plaintext one by whichever server answers first. Every module that talks to a remote host opens its
URLs here. The two exceptions are judges/_local.py, which only ever talks to loopback, and agentloop, which
runs inside the no-network box.
"""

from __future__ import annotations

import urllib.error
import urllib.request


def _refuse(url: str) -> None:
    raise urllib.error.URLError(f"only https is allowed, refusing {url}")


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.lower().startswith("https://"):
            _refuse(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_HttpsOnly)


def urlopen(url_or_request, timeout: float):
    """Open an https URL or Request. Anything else, before or after a redirect, raises URLError."""
    url = url_or_request if isinstance(url_or_request, str) else url_or_request.full_url
    if not url.lower().startswith("https://"):
        _refuse(url)
    return _OPENER.open(url_or_request, timeout=timeout)  # noqa: S310 - https only, checked above and on every redirect
