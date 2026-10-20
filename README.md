# Book Shop

[![CI](https://github.com/alex-anisimov-hillel/hillel_hw_deploy/actions/workflows/django.yml/badge.svg?branch=master)](https://github.com/alex-anisimov-hillel/hillel_hw_deploy/actions/workflows/django.yml)
[![codecov](https://codecov.io/gh/alex-anisimov-hillel/hillel_hw_deploy/branch/master/graph/badge.svg)](https://codecov.io/gh/alex-anisimov-hillel/hillel_hw_deploy)

Django-застосунок інтернет-магазину книг з кошиком на сесіях, оформленням
замовлень та оплатою через Stripe.

## Можливості

- Каталог книг з категоріями (django-mptt), CRUD для книг
- Кошик на сесіях (async views) — додавання/видалення позицій, підрахунок суми
- Оформлення замовлення (гостьове або від імені зареєстрованого користувача)
- Оплата через Stripe: створення `PaymentIntent`, підтвердження оплати,
  email-сповіщення про успішну оплату
- Кастомна модель користувача (email як логін)
- Локалізація (django `gettext`)

## Технології

Django 6.1, Django REST Framework, django-mptt, Stripe, PostgreSQL, Redis,
Gunicorn + Uvicorn worker (ASGI), WhiteNoise, Docker / docker-compose, pytest / pytest-django / pytest-factoryboy.

## Запуск локально (Docker)

1. Скопіюйте/перевірте `.env` (POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
   POSTGRES_HOST, POSTGRES_PORT, а також `STRIPE_SECRET_KEY`/`STRIPE_PUBLIC_KEY`,
   якщо плануєте тестувати оплату).
2. Підняти сервіси:
   ```bash
   docker compose up --build
   ```
   Це підніме Postgres, Redis і сам застосунок (застосує міграції автоматично
   через `entrypoint.sh`) на `http://localhost:8000`.

## Gunicorn, статика та health check

- **Gunicorn** (`gunicorn.conf.py`) запускає ASGI-застосунок з воркерами
  `uvicorn_worker.UvicornWorker`: `gunicorn book_shop.asgi:application -c gunicorn.conf.py`.
  Налаштовується змінними оточення: `PORT` (8000), `WEB_CONCURRENCY` (3),
  `GUNICORN_TIMEOUT`, `GUNICORN_MAX_REQUESTS`, `GUNICORN_LOG_LEVEL`.
- **Статичні файли** віддає **WhiteNoise** (middleware одразу після
  `SecurityMiddleware`). У production файли хешуються й стискаються
  (`CompressedManifestStaticFilesStorage`); `collectstatic` виконується під час
  збірки образу (і в `docker compose`). Nginx лише проксіює запити.
  У development WhiteNoise вимкнений — статику віддає `runserver`.
- **Health check**:
  - `GET /health/` — liveness: процес живий (без звернень до БД/Redis);
  - `GET /health/ready/` — readiness: перевіряє PostgreSQL і Redis,
    повертає `503` та назву збійного компонента, якщо щось недоступне.

  Обидва ендпоінти виключені з HTTPS-редіректу (`SECURE_REDIRECT_EXEMPT`), тож
  працюють для Docker/балансувальника по звичайному HTTP. Хост із запиту
  (напр. `localhost` для Docker healthcheck) має бути в `DJANGO_ALLOWED_HOSTS`.

## Тести та coverage

```bash
pytest
pytest --cov=payment.models --cov=orders.models --cov=users.models --cov-report=term-missing
```

Детальний coverage-звіт (з поясненням, чому саме ці 3 моделі та звідки взяті
цифри) — у `COVERAGE_REPORT.md`.

## AI Usage

У рамках домашнього завдання "Використати AI для покращення проєкту" AI (Claude,
Anthropic) використовувався для трьох задач:

1. **Code review** трьох найскладніших views/serializers проєкту
   (`PaymentViewSet` + `StripePayment`, cart/order views у `orders/views.py`,
   `PaymentSerializer`) — знайдено й виправлено кілька реальних багів (падіння на
   гостьових замовленнях, невідповідність назв полів моделі й серіалізатора,
   втрату `Payment` при переданому `idempotency_key`, відсутню автентифікацію на
   payment-ендпоінтах, мертвий/непрацюючий код у `order_create`). Повний розбір
   "було / рекомендація AI / стало" — у `AI_REVIEW.md`.
2. **Генерація тестів** для моделей `Payment`, `Order`/`OrderItem` та `User` —
   нові тести (позначені коментарем `# Generated with AI, reviewed and modified`)
   цілять саме в раніше непокриту логіку: властивості `is_success`/
   `can_be_refunded`/`remaining_amount`, `OrderItem.get_total()`, і, найважливіше,
   `UserManager.create_user`/`create_superuser` (раніше взагалі не викликались
   жодним тестом, оскільки фабрики `pytest-factoryboy` створюють користувачів в
   обхід менеджера). Детальніше, включно з реальними цифрами покриття "до" (з
   вашого попереднього `.coverage`) — у `COVERAGE_REPORT.md`.
3. **Документація** — docstrings додано до всіх views/viewset-методів проєкту
   (`books/views.py`, `orders/views.py`, `payment/views.py`, `users/views.py`), і
   оновлено цей README.

Повний список промптів, якими виконувалась кожна з трьох задач — у `AI_PROMPTS.md`.

## Налаштування (settings) та змінні оточення

Налаштування розділені на пакет `book_shop/settings/`:

| Модуль | Призначення |
| --- | --- |
| `base.py` | спільні налаштування, усе читається зі змінних оточення |
| `development.py` | `DEBUG=True`, debug-toolbar, e-mail у консоль (типово для `manage.py`, Celery і pytest) |
| `production.py` | `DEBUG=False`, HTTPS-редірект, HSTS, secure/HttpOnly cookies, `X-Frame-Options: DENY`, без debug-toolbar; без `DJANGO_SECRET_KEY`/`DJANGO_ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` (https) застосунок не стартує (типово для `wsgi.py`, `asgi.py` і Docker-образу) |

Активний модуль вибирається змінною `DJANGO_SETTINGS_MODULE`. Секрети беруться з
`.env` (шаблон — `.env.example`; реальний `.env` у git **не комітимо**). Справжні
змінні оточення завжди мають пріоритет над `.env`.

```bash
cp .env.example .env   # заповнити значення
python -c "import secrets; print(secrets.token_urlsafe(60))"   # для DJANGO_SECRET_KEY
python manage.py check --deploy                                   # перевірка production-налаштувань
```

## CI/CD (GitHub Actions)

Pipeline — `.github/workflows/django.yml`:

1. **lint** — `flake8` та `black --check`
2. **test** — `pytest` + coverage (поріг 70%) на Postgres і Redis; перевірка
   відсутніх міграцій та `check --deploy` для production-налаштувань
3. **docker** — збірка образу, smoke-тест, push у Docker Hub (лише `main`/`master` і теги `v*`;
   у pull request образ тільки збирається)

Потрібні secrets репозиторію (*Settings → Secrets and variables → Actions*):
`CODECOV_TOKEN` (для badge покриття: [codecov.io](https://codecov.io) → додати
репозиторій → скопіювати токен), `DOCKERHUB_USERNAME` та `DOCKERHUB_TOKEN` (Docker Hub → Account settings →
Personal access tokens, права *Read & Write*). Образ: `<username>/book-shop`.

Локально те саме:

```bash
pip install -r requirements-dev.txt
flake8 . && black --check .
pytest --cov
```
