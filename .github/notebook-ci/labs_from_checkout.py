"""Serve labs downloads from the checkout while the notebook check runs.

A notebook downloads its data, helpers and recordings from the labs
repository on GitHub (raw.githubusercontent.com/.../main/...). In the
notebook check we must test the files of the commit, not the files on main:
a pull request adds files that are not on main yet, and it can change files
that are. This module, loaded at Python start by labs_from_checkout.pth,
answers each such request with the file of the same path in the checkout.

It acts only when LABS_CHECKOUT is set (the checkout's root folder).
A path that is not in the checkout goes to the network as before, and its URL
is written to the file LABS_CHECKOUT_MISSES (if set), so the workflow can show
a warning. Downloads from other sites are not changed.
"""

import os
import urllib.request
from pathlib import Path

PREFIX = "https://raw.githubusercontent.com/Nextia-Intelligence/nextia-learning-labs/main/"


def _install(root):
    original = urllib.request.urlopen

    def urlopen(url, *args, **kwargs):
        full = url.full_url if isinstance(url, urllib.request.Request) else str(url)
        if full.startswith(PREFIX):
            rel = full[len(PREFIX):].split("?", 1)[0].split("#", 1)[0]
            local = (root / urllib.request.url2pathname(rel)).resolve()
            if root in local.parents and local.is_file():
                return original(local.as_uri())
            misses = os.environ.get("LABS_CHECKOUT_MISSES")
            if misses:
                with open(misses, "a", encoding="utf-8") as f:
                    f.write(full + "\n")
        return original(url, *args, **kwargs)

    # urlretrieve and pandas look up urllib.request.urlopen when they run.
    urllib.request.urlopen = urlopen


if os.environ.get("LABS_CHECKOUT"):
    _install(Path(os.environ["LABS_CHECKOUT"]).resolve())
