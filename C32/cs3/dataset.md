# Dataset card: Official MCP Registry entries, with Docker MCP catalog entries

Used by: the case study *Review public MCP servers for registration* (course *Governing AI Agents: Gateways, Registries and Controls*), project folder `mcp-intake` (`starter.zip`, `finished.zip`).

| Field | Value |
|---|---|
| Source | Official MCP Registry, REST API `GET /v0/servers?version=latest`: https://registry.modelcontextprotocol.io/ (documentation: https://modelcontextprotocol.io/registry/about) |
| Publisher / creator | The MCP Registry maintainers; each entry is published by its server's developer |
| Licence | **CC0 1.0 Universal** for Registry Data: the registry's Terms of Service, section 10 "License" (https://modelcontextprotocol.io/registry/terms-of-service, effective 2025-09-02) dedicate submitted server metadata to the public domain. https://creativecommons.org/publicdomain/zero/1.0/ |
| Second source | Docker MCP Registry, https://github.com/docker/mcp-registry, folder `servers/`, commit `49b643ce3fc73e6ee80bb962719b6e2990e3d397` (2026-09-16), **MIT** licence (copied as `data/catalog/LICENSE`) |
| Attribution text | "Server metadata from the Official MCP Registry (CC0 1.0). Catalog entries from the Docker MCP Registry, © 2025 Docker, MIT licence." CC0 needs no attribution; we give it anyway. Do not say or suggest that Nextia Learning is affiliated with the Official MCP Registry (Terms, section 6). |
| Version or access date | Registry: fetched 2026-10-23 02:16 UTC (`data/registry/FETCHED`). Docker catalog: the commit above. Vendor pages: read 2026-10-22. |
| File used | `data/registry/servers.jsonl.gz` (slim copy of every latest entry), `data/registry/entries/*.json` (5 full entries), `data/catalog/index.jsonl` (328 slim catalog entries), `data/catalog/servers/*/` (7 entries' `server.yaml` and `tools.json`), `data/vendor/*.yaml` (our notes). Kept in `data/`: yes (CC0 and MIT allow it) |
| SHA-256 | Every file in `data/SHA256SUMS`; `python -m intake verify` checks them. `servers.jsonl.gz`: see that file |
| Size | 48,606 registry entries (4.2 MB compressed), 328 catalog entries; about 4.3 MB in all |

## What one row means

One line of `servers.jsonl.gz` is the latest version of one MCP server in the official registry: its name (a namespace the publisher has proved it controls, such as `com.stripe` or `io.github.getsentry`), title, description, version, status, code repository, the packages to run it on your own machine (npm, PyPI, OCI and others, with environment variables marked secret or not), and the hosted addresses (remotes). There is no target: the case study asks which registration questions a row answers.

## Why this dataset

The official registry is the open, standard list of public MCP servers, with an explicit public-domain dedication of its data. Its entries say who publishes a server and how to run it, but not which tools it has or what data they return: exactly the gap that a registration review must find. The Docker catalog (MIT) is a second, independent catalog with tool lists for some servers, so the case study can compare what one, two and three sources answer. Alternatives compared (`reference/c32/m08/L03/DATASET-RESEARCH.md` in the site repository): the GitHub list awesome-mcp-servers (MIT, but a README of links with no structured fields) and the directories Glama (its own API data licence, with an API key: an account), Smithery and mcp.so (we found no licence for their listings).

## Changes we made

- Registry: only the latest version of each server (`version=latest`). The slim copy keeps the fields the case study reads: name, title, description, version, status, published and updated dates, repository and website URLs, packages (type, identifier, version, transport, environment variable names with their secret and required flags), remotes (type, URL, header names), and the number of tools in the publisher's own notes (`_meta`, when it is a list). Everything else is dropped. The five reviewed servers are also kept in full (`entries/`).
- Docker catalog: an index of all 328 entries (name, type, title, image, remote URL, source repository and commit, secret names, OAuth, allowed hosts, dynamic tools, whether a `tools.json` exists), and the `server.yaml` and `tools.json` of the seven entries that match, or share a name with, a reviewed server.
- Vendor notes (`data/vendor/*.yaml`): written by the course team from the vendors' own pages and source code, in our own words, with a link per answer. Tool names are extracted from the vendors' pages (Stripe, Notion) and from the Sentry server's source at tag 0.42.0; no text of those pages is copied.

## Limitations and cautions

- **A snapshot.** The registry is in preview: entries change every hour, and the maintainers say data resets may happen before general availability. `python -m intake fetch NAME` compares one entry with the live registry. Never register a server from this copy: review the live entry.
- **Published information only.** Nobody ran any server. A tool list from a catalog or a vendor page can differ from what the server returns to `tools/list`; in this copy, the Docker catalog's and the vendors' lists share 2 of 15 names (Stripe) and 0 of 65 (Notion).
- **Namespaces prove control, not quality.** The registry checks that a publisher controls the domain or GitHub account in the name. It does not scan code; it leaves that to the package registries and to downstream catalogs.
- **Personal data.** Entries can hold GitHub user names and domains of their publishers (Terms, section 11). The case study counts and reads entries; it does not profile publishers.
- **Vendor notes age.** They record what each page said when we read it; the pages change.
