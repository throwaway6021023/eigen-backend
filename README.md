# Fito's Take Home - Backend

This repository contains the backend for the Fito's Take Home project.
It's a simple FastAPI application.

## Requirements

- Python 3.12
- Poetry 1.8

## Installation

```bash
$ poetry install
```

Then, copy the `.env-example` file to `.env` and set the `OPENROUTER_API_KEY` environment variable.

## Running the application

First, run the following command to start the database:

```bash
$ docker compose up
```

Then, run the following command to start the FastAPI server:

```bash
# For dev mode
$ poetry run fastapi dev backend/main.py

# For prod mode
$ poetry run fastapi run backend/main.py
```
