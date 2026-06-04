# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Django 6.0.6 web application — a travel-themed site ("Travel memories") with a Chinese-language UI. Currently in early scaffolding stages with a single homepage and an empty `login` app.

## Commands

```bash
# Activate virtual environment
source .venv/Scripts/activate

# Development server (default: http://127.0.0.1:8000/)
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test

# Shell / admin
python manage.py shell
python manage.py createsuperuser
```

## Architecture

- **Project package**: `the_root/` (created by `django-admin startproject`)
- **Apps**: `login/` — registered in `INSTALLED_APPS` but contains no models, views, or URL patterns yet
- **Database**: MySQL via `mysqlclient` driver, connection options read from `my.cnf` at the project root
- **Templates**: Stored in project-level `templates/` directory (not per-app). `'builtins':['django.templatetags.static']` means `{% static %}` is available in every template without `{% load static %}`.
- **Static files**: Served from `static/` directory. Libraries include Bootstrap 5, jQuery, highlight.js, and wangEditor (Chinese rich text editor).

## Key Settings Decisions

| Setting | Value | Implication |
|---|---|---|
| `USE_TZ = False` | Timezone support disabled | Datetimes stored naively; `Asia/Shanghai` is the display timezone |
| `LANGUAGE_CODE` | `zh-hans` | Simplified Chinese localization |
| `LOGIN_URL` | `/auth/login` | Redirect target for `@login_required` decorator |
| `DEBUG` | `True` | Dev mode; `ALLOWED_HOSTS = []` allows localhost only |

## Dependencies

No `requirements.txt`, `pyproject.toml`, or `Pipfile` exists. Dependencies are installed manually into `.venv/`:
- **Django 6.0.6** — web framework
- **mysqlclient 2.2.8** — MySQL database driver

When adding new packages, run `pip freeze > requirements.txt` to capture them.
