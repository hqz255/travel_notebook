# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Django 6.0.6 web application — a travel-themed social site ("Travel memories") with a Chinese-language UI. Users register, log in, write travel articles with images, explore others' posts, and interact.

## Commands

```bash
# Activate virtual environment
source .venv/Scripts/activate

# Development server (http://127.0.0.1:8000/)
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test

# Run a single test file / test case / test method
python manage.py test login.tests
python manage.py test login.tests.YourTestCase
python manage.py test login.tests.YourTestCase.test_method

# Shell / admin
python manage.py shell
python manage.py createsuperuser
```

## Architecture

### Apps and their roles

| App | Purpose | Has models? |
|---|---|---|
| `register` | Custom `User` model, registration view, email verification code | Yes — **the canonical User model** |
| `login` | Login view, login verification code (`login/` URLs, no models) | No — uses `register.User` |
| `record_memories` | Article CRUD — write/publish travel articles with image uploads (`wmmr/` URLs) | Yes — `Article`, `ArticleCategory` |
| `explore_world` | Browse all articles from all users (`explore/` URLs) | No |
| `interact` | Placeholder for social/interaction features (`interact/` URLs) | No |
| `travel_footprint` | Placeholder for travel map/footprint features (`footprint/` URLs) | No |

### Authentication system (custom, session-based)

This project does **not** use Django's built-in `auth` User model. Instead:
- **User model**: `register.models.User` — custom table (`user`) with `username`, `email`, `password` (hashed via `make_password`/`check_password`), `superuser`, `aactive`.
- **Login**: Sets `request.session['user_id']` on success. Supports "remember me" (7-day session) and `next` parameter redirects. Requires email + password + email verification code.
- **Login-required decorator**: `the_root.decorators.login_required` — checks `session['user_id']`, resolves the `User` object, attaches it as `request.user_obj`. Redirects to `settings.LOGIN_URL` (`/login/`) on failure.
- **Logout**: `request.session.flush()` in `the_root.views.logout_view`.
- **Verification codes**: Both login and registration send 6-digit codes via QQ SMTP. Codes stored in session (`login_verification_code`, `register_verification_code`).

**Always use `request.user_obj`** (not `request.user`) to get the current user in views protected by the custom decorator.

### URL routing

```
/                          → the_root.views.index (homepage with login form)
/home/                     → the_root.views.product_homepage (post-login landing)
/logout/                   → the_root.views.logout_view
/login/                    → login.views.login_view
/login/send-code/          → login.views.send_login_code (AJAX)
/register/                 → register.views.register_view
/register/send-code/       → register.views.send_verification_code (AJAX)
/wmmr/                     → record_memories.views.wmmr (write article)
/explore/                  → explore_world.views.explore_world
/interact/                 → interact.views.interact
/footprint/                → travel_footprint.views.travel_footprint
/admin/                    → Django admin
```

All app URLs use `app_name` namespacing (e.g., `login:login`, `register:register`, `record_memories:wmmr`, `explore_world:explore_world`).

### Templates

- Stored in project-level `templates/` directory.
- `templates/includes/` — shared partials: `navbar.html` (logged-out nav), `navbar_authenticated.html` (logged-in nav), `modals.html`, `footer.html`.
- `{% static %}` is available in all templates without `{% load static %}` (configured via `TEMPLATES[0]['OPTIONS']['builtins']`).
- The `index.html` template serves double duty: it's both the landing page and displays login form errors (rendered by `login.views.login_view`).
- Registration errors are rendered on `register.html` (not yet checked into templates — verify before working on registration).

### Static files & media

- **Static**: `static/` directory — Bootstrap 5, jQuery, highlight.js.
- **Media**: User-uploaded images go to `media/uploads/`. Served via `MEDIA_URL = '/media/'` in dev (`DEBUG=True` only).

### Database

- **MySQL** via `mysqlclient` driver.
- Connection options read from `my.cnf` at the project root (not baked into settings).
- `USE_TZ = False` — datetimes are naive; `TIME_ZONE = 'Asia/Shanghai'`.

## Dependencies

A `requirements.txt` exists at the project root:
- **Django 6.0.6** — web framework
- **mysqlclient 2.2.8** — MySQL driver
- **Pillow 12.2.0** — image processing (used by `record_memories` for upload validation)

When adding new packages, run `pip freeze > requirements.txt` to capture them.

## Key settings

| Setting | Value | Implication |
|---|---|---|
| `USE_TZ` | `False` | Datetimes stored naively; `Asia/Shanghai` is the display timezone |
| `LANGUAGE_CODE` | `zh-hans` | Simplified Chinese localization |
| `LOGIN_URL` | `/login/` | Redirect target for the custom `@login_required` decorator |
| `DEBUG` | `True` | Dev mode; `ALLOWED_HOSTS = []` allows localhost only |
| `EMAIL_HOST` | `smtp.qq.com:587` (TLS) | QQ SMTP for verification code emails |

## Code conventions observed

- Views are function-based (no class-based views used).
- `app_name` is set in every app's `urls.py` for URL namespacing.
- Form validation happens server-side in views; client-side JS provides supplementary UX (e.g., email format check, verification code countdown).
- Error messages are collected in a `errors` list, then passed to templates as `context['errors']`.
- Form data is preserved on error via `context['form_data']` (except passwords and verification codes).
- Image upload validation in `record_memories/views.py` is multi-layered: file size → extension whitelist → magic-byte detection → PIL/Pillow integrity check.
