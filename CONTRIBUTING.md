# Contributing to git-archaeologist

## Setup

```bash
git clone https://github.com/git-archaeologist/git-archaeologist
cd git-archaeologist
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

## Linting and type checks

```bash
ruff check src tests
mypy src
```

## Submitting changes

1. Fork the repo and create a feature branch from `main`
2. Add tests for new behavior
3. Ensure `pytest`, `ruff check`, and `mypy src` all pass
4. Open a pull request with a clear description of what and why

## Design philosophy

- The LLM prompt is the product. Prompt changes should be evaluated against real repositories, not just unit tests.
- Prefer narrower scope over broad output. Users want insight about a *specific* function or file, not a summary of the whole repo.
- Output formats (rich, markdown, json) should be lossless — all the same information, different presentation.
- Minimize required dependencies. `openai`, `typer`, and `rich` are the only runtime deps.

## Reporting issues

Please include the git-archaeologist version (`git-arch --version`), the command you ran, and whether the problem is with history extraction or LLM output quality.
