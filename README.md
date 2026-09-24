# fast-lane-hack

Isolated hackathon project (fast-lane-hack). Nothing here touches the global toolchain.

## Toolchain

| Tool | Scope | Pinned by |
|---|---|---|
| Python 3.13.13 | project | `.python-version` (uv downloads it) |
| google-adk 2.9.2 | project | `pyproject.toml` / `uv.lock` |
| Node 22.22.3 | project | `.nvmrc` (`nvm use`) |
| npm deps | project | `package.json` → local `node_modules/` |
| Docker | machine | daemon is global; per-project via Dockerfile |
| gcloud | machine | per-project via a named configuration |

## Usage

Everything Python runs through `uv run` — never activate the venv, never `pip install`:

```sh
uv run adk --version
uv run adk web          # agent dev UI
uv add <package>        # add a dependency
```

Node:

```sh
nvm use                 # reads .nvmrc
npm install <pkg>       # lands in ./node_modules
```
