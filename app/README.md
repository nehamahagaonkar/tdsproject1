# TDS Project — GitHub + LLM Integration

A small FastAPI-based project that demonstrates integration with GitHub and an LLM provider. It includes utilities for GitHub access, an LLM generator, notification helpers, and request signature utilities.

---

## Contents

- Quick links to key files:
  - [`.env`](.env)
  - [`test_github.py`](test_github.py)
  - [`requirements.txt`](requirements.txt)
  - [`runtime.txt`](runtime.txt)
  - [`app/main.py`](app/main.py) — FastAPI app (FastAPI instance: [`app.main:app`](app/main.py))
  - [`app/github_utils.py`](app/github_utils.py) — GitHub helper functions: [`app.github_utils`](app/github_utils.py)
  - [`app/llm_generator.py`](app/llm_generator.py) — LLM integration: [`app.llm_generator`](app/llm_generator.py)
  - [`app/notify.py`](app/notify.py) — notification helpers: [`app.notify`](app/notify.py)
  - [`app/signature.py`](app/signature.py) — signature / verification helpers: [`app.signature`](app/signature.py)
  - [`app/__init__.py`](app/__init__.py)

---

## Overview

This repository is designed to:
- Authenticate and interact with GitHub repositories (via utilities in [`app/github_utils.py`](app/github_utils.py)).
- Generate or process LLM responses using a pluggable LLM layer (see [`app/llm_generator.py`](app/llm_generator.py)).
- Expose HTTP endpoints via FastAPI (main entry: [`app/main.py`](app/main.py)).
- Provide a small test script to validate GitHub and OpenAI connectivity: [`test_github.py`](test_github.py).

---

## Prerequisites

- Python 3.11+ recommended.
- A virtual environment for isolation.
- API keys for services used (GitHub, OpenAI or other LLM provider).

The project dependencies are listed in [`requirements.txt`](requirements.txt).

---

## Environment variables

Create a `.env` file in the project root or export these variables in your shell. Do NOT commit real secrets to the repo.

Example `.env` template:

```env
GITHUB_TOKEN=<your_github_token>
GITHUB_USERNAME=<your_github_username>
USERCODE=<your_user_code_or_app_id>
USER_SECRET=<your_app_secret>
AIPIPE_API_BASE=<optional_llm_api_base>
AIPIPE_TOKEN=<your_llm_api_token>
OPENAI_API_KEY=<your_openai_api_key>