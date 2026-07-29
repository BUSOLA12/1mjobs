# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response formatting

Do not use em dashes in any response. Replace what would be an em dash with a colon, a comma, or brackets, whichever fits the sentence best.

## Project layout note

The Django project root is **nested one level down**: the repo lives at `1mjobs/`, and `manage.py` plus all apps are inside `1mjobs/1mjobs/`. Run all `python manage.py` commands from `1mjobs/1mjobs/` (the directory containing `manage.py` and `db.sqlite3`). The Django settings package is `jobwebsite` (`jobwebsite/settings.py`), not `1mjobs`.

## Commands

All commands assume the virtualenv (`env/`) is active and you are in the project root (the dir with `manage.py`).

```powershell
# Activate the bundled virtualenv (Windows)
env\Scripts\Activate.ps1

# Run the dev server. Because daphne/channels is installed and ASGI is configured,
# runserver serves both HTTP and WebSocket.
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Tests (Django test runner). Run a single app / class / method:
python manage.py test                      # all
python manage.py test users                # one app
python manage.py test users.tests.SomeTest.test_method

# Create an admin (role is forced to 'admin')
python manage.py createsuperuser
```

### Seeding

There are many `seed_*` management commands (Faker-based) spread across apps. The aggregate entry point is:

```powershell
python manage.py seed_all --users 20 --orders 5 --subscriptions 5
```

Individual seeders: `seed_users`, `seed_freelancers`, `seed_jobs_tasks`, `seed_employer_jobs_tasks`, `seed_pricing`, `seed_plans`, `seed_reviews`, `seed_user_reviews`, `seed_offer`, `seed_messaging`. Note `seed_all` currently has `seed_messaging` commented out. `link_company` (in `company/`) wires companies to users.

## Required services & configuration

- **Redis on `127.0.0.1:6379`** is required for the WebSocket/Channels layer (`channels_redis`). Without it, messaging WebSocket connections fail. The HTTP site still runs.
- **Environment variables** are read via `python-decouple` from a `.env` file (gitignored). Copy `.env.example` to `.env`. `SECRET_KEY` has no default and will crash startup if missing. Other keys (`AFRICANMONEY_API_KEY`/`AFRICANMONEY_SECRET_KEY`, `EMAIL_HOST_PASSWORD`, Google OAuth, Google Maps, Facebook) default to empty strings, so features degrade rather than crash.
- **Database** is SQLite (`db.sqlite3`) checked into `.gitignore` — local only.
- **Email** backend is set to console (`console.EmailBackend`) in `settings.py`; SMTP variants (Mailtrap, Gmail, cPanel) are commented out. OTP/verification emails print to the terminal in dev.

## Architecture

Django 5.2 + Django REST Framework backend with server-rendered frontend, organized as ~17 apps. Two surfaces share the same project:

1. **JSON API** under `/api/...` (DRF + SimpleJWT) — the primary application interface.
2. **Server-rendered HTML** via the `frontend` app (mounted at `/`) and the `adminpanel` app (mounted at `/site-admin/`). These render Django templates (`frontend/templates/`, `adminpanel/templates/`). Note `/admin/` is the stock Django admin; `/site-admin/` is the custom staff dashboard.

URL composition lives in `jobwebsite/urls.py`. Each app owns its own `urls.py`; API apps are namespaced under `/api/<app>/`.

### Apps and responsibilities

- **users** — `CustomUser` (the `AUTH_USER_MODEL`, email-as-username, role = freelancer/employer/admin) plus `UserProfile`, `UserKYC`, `Skill`, `Category`, `WorkHistory`, `UserActivityLog`. The user model carries account-control state (suspend/ban) with helper methods (`.suspend()`, `.ban()`, `.is_suspended`).
- **authentication** — login/register/logout, email OTP verification, password reset, two-factor, and Google/Facebook OAuth. Issues JWTs both as Bearer tokens and as HttpOnly cookies (the `Cookie*` views).
- **ManageJobsTasks** — the core domain: `Job` + `JobApplication` (employment listings) and `Task` + `TaskBidding` (freelance projects with bids). Both Job and Task auto-set a 30-day `expiration_date` in `save()` and have featured/expired flags.
- **payments** — escrow-style flow: `Payment` (status NOT_INITIATED→ESCROWED→RELEASED), `Wallet` (available/pending balances), `Transaction`, `BankAccount`, `Escrow`. African Money (africanmoney.net) is the only payment provider (Paystack was removed); payments are verified server-side on return via `AfricanMoneyService.verify_collection`. The 10% platform commission (`PLATFORM_FEE_PERCENTAGE`) is deducted in `PaymentService.release_payment`; `VAT_RATE`/`VAT_ENABLED` apply to subscription checkout.
- **pricing** — subscription plans: `Plan` + `PlanFeature` (per-feature limits), `Order`, `Subscription`, `Transaction`. `Subscription.remaining_features` is a JSON usage counter; `Subscription.use_feature()` decrements it (null limit = unlimited).
- **Messaging** — real-time chat over WebSockets (`MessagingConsumer`, route `ws/messaging/`). This is the only WebSocket surface and the reason Redis/Channels exist.
- **company** — employer company profiles. **offers** — direct offers to freelancers. **reviews** — ratings (feeds `UserProfile.avg_rating`). **bookmarks** — saved jobs/tasks. **notifications** — in-app notifications. **admins** — admin-only API endpoints (distinct from the `adminpanel` HTML dashboard).
- **frontend** — public-facing pages + authenticated user dashboard (templates + `views.py`). Also home of the cross-cutting DRF `custom_exception_handler` and `seed_all`.

### Cross-cutting conventions

- **Auth defaults**: DRF uses JWT + Session auth globally (`REST_FRAMEWORK` in settings). Access tokens live 5 minutes, refresh tokens 1 day. Tokens can be carried in the `access` HttpOnly cookie.
- **Custom DRF exceptions**: `frontend.exceptions.custom_exception_handler` is the global `EXCEPTION_HANDLER`; add API-wide error shaping there.
- **Request logging**: `jobwebsite.middleware.request_debugger.RequestDebugMiddleware` logs every request as JSON to `logs/request_debug.log`. The `subscriptions` logger writes to `logs/subscription.log`. (Note: a large `app.log` also appears at the project root.)
- **Many models redefine choices/imports inline** (e.g. `payments/models.py` re-imports `get_user_model` mid-file, `ManageJobsTasks/models.py` repeats `STATUS_CHOICES`). Match the surrounding style of the file you edit rather than refactoring opportunistically.
- **ASGI is the entry point** (`jobwebsite.asgi.application`): `ProtocolTypeRouter` routes HTTP to Django and WebSocket through `Messaging.routing`. `Messaging.routing` must be imported after `get_asgi_application()` — preserve that ordering when touching `asgi.py`.

### Deployment context

`DOMAIN`/`ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` reference `freelancetesting.onemillionjobs.com.ng` and a PythonAnywhere host (`lichtcode.pythonanywhere.com`). `GOOGLE_OAUTH2_REDIRECT_URI` and the email backend have commented local/server/PythonAnywhere variants in `settings.py` — switch the active line per environment. A `jobwebsite/settings(server).py` variant is kept locally and gitignored.
