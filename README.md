# myst-preview

Preview a single Markdown or Jupyter notebook file rendered with [MyST MD](https://mystmd.org) — no `myst.yml` or project setup needed.

## Install

```bash
# From GitHub
uv tool install git+https://github.com/ianhi/myst-preview

# Or from a local checkout
uv tool install /path/to/myst-preview
```

### Prerequisites

- [Node.js](https://nodejs.org) (v18+)
- [mystmd](https://mystmd.org/guide/quickstart) — `npm install -g mystmd`
  (if not installed, `myst-preview` falls back to `npx`)

## Usage

```bash
# Live preview with hot reload
myst-preview myfile.md

# Jupyter notebooks
myst-preview notebook.ipynb

# Custom port or theme
myst-preview myfile.md --port 8080
myst-preview myfile.md --theme article-theme

# Execute notebook cells
myst-preview notebook.ipynb --execute

# Open browser automatically
myst-preview myfile.md --open

# Build static HTML instead of live server
myst-preview myfile.md --build
myst-preview myfile.md --build -o ./output
```

## How it works

1. Creates a temporary directory
2. Symlinks the source file's directory contents (so relative image/asset paths work)
3. Writes a minimal `myst.yml` pointing at the target file
4. Runs `myst start` (live server) or `myst build --html` (static output)
5. Cleans up the temp directory on exit

## Supported file types

- `.md` — Markdown (MyST flavored)
- `.ipynb` — Jupyter notebooks
- `.rst` — reStructuredText
- `.tex` — LaTeX

## Why?

MyST MD currently requires a `myst.yml` config file and project structure to preview content.
**This tool is a stopgap** until native single-file support lands in mystmd itself.
If you're interested in contributing upstream, the relevant issues are listed below — help is welcome!

### Related mystmd issues

Single-file build/preview (the core gap this tool fills):

- [#2689](https://github.com/jupyter-book/mystmd/issues/2689) — Build single notebooks and markdown files without requiring a `myst.yml` file
- [#2526](https://github.com/jupyter-book/mystmd/issues/2526) — Support building a single HTML output without a project file
- [#1832](https://github.com/jupyter-book/mystmd/issues/1832) — Allow single-file builds for ipynb/md sources with no `myst.yml` file, without any warnings
- [#1967](https://github.com/jupyter-book/mystmd/issues/1967) — Ability to build only one file without considering other .md files + no warning about missing myst.yml
- [#1816](https://github.com/jupyter-book/mystmd/issues/1816) — Support setting at least the template, possibly other options, from the CLI
- [#1947](https://github.com/jupyter-book/mystmd/issues/1947) — Support calling from outside of the book directory (argument PATH_SOURCE)

Preview subcommand proposals:

- [#2017](https://github.com/jupyter-book/mystmd/issues/2017) — Add a `myst preview` subcommand
- [#2163](https://github.com/jupyter-book/mystmd/issues/2163) — Add new `myst templates start` command to start site templates

Live preview improvements:

- [#302](https://github.com/jupyter-book/mystmd/issues/302) — Support running MyST previews / running a myst server on JupyterHub
- [#2502](https://github.com/jupyter-book/mystmd/issues/2502) — `myst start` server triggers too many refreshes on code change
