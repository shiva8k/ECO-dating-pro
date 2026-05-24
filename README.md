# ECO

ECO is a modern Django web application scaffold for a college social and matching platform.

## Quick Start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

## Beginner File Guide

### Root files

- `manage.py` is Django's command-line helper. You use it to run the server, create database tables, make apps, and open the admin.
- `requirements.txt` lists Python packages: Django, Gunicorn, Whitenoise, PostgreSQL drivers, Pillow, and Razorpay.
- `.gitignore` tells Git which local files to ignore, such as virtual environments, cache files, and the SQLite database.
- `README.md` is this guide. It explains how to run the project and what each generated file does.

### `ECO/` project configuration

- `ECO/__init__.py` marks the folder as a Python package.
- `ECO/settings.py` contains the project settings: installed apps, database, templates, static files, login redirects, and security basics.
- `ECO/urls.py` is the main URL router. It connects browser paths like `/`, `/accounts/`, and `/admin/` to the correct app.
- `ECO/wsgi.py` is the WSGI entry point used by Gunicorn, Vercel, and Railway.
- `ECO/settings.py` reads `DATABASE_URL` for Neon PostgreSQL in production and falls back to SQLite locally.

### `core/` homepage app

- `core/__init__.py` marks the app folder as a Python package.
- `core/apps.py` registers the `core` app with Django.
- `core/views.py` contains the homepage view. A view receives a web request and returns a response.
- `core/urls.py` maps the homepage URL to the homepage view.

### `accounts/` authentication app

- `accounts/__init__.py` marks the app folder as a Python package.
- `accounts/apps.py` registers the `accounts` app with Django.
- `accounts/models.py` defines the profile, matching, chat, notification, premium, subscription, and payment database models.
- `accounts/admin.py` makes profiles, likes/passes, matches, chat rooms, chat messages, notifications, premium plans, subscriptions, and payments manageable from Django admin.
- `accounts/signals.py` automatically creates a profile whenever a new user account is created.
- `accounts/chat_service.py` saves chat messages and notifications (HTTP-based chat for serverless deploys).
- `accounts/payments.py` contains Razorpay helper functions for creating orders and verifying payment signatures.
- `accounts/forms.py` defines the signup form and profile edit form. Forms turn model fields into safe HTML inputs.
- `accounts/context_processors.py` gives every template the unread notification count, so the navbar can show a badge.
- `accounts/views.py` contains signup, profile display, profile edit, explore, like/pass, matches, chat list, chat room, and notifications views. Views decide what happens when a user opens or submits a page.
- `accounts/urls.py` maps signup, login, logout, profile, edit-profile, explore, like/pass, matches, chat list, chat room, and notification URLs.
- `accounts/migrations/` stores database migration files. Migrations are Django's step-by-step instructions for creating or changing database tables.

### `templates/` HTML files

- `templates/base.html` is the shared page layout. It loads Bootstrap, the navbar, messages, and the main content area.
- `templates/core/home.html` is the homepage for ECO.
- `templates/accounts/profile_detail.html` shows a student's public ECO profile.
- `templates/accounts/profile_edit.html` lets a logged-in student update their profile details and upload a profile picture.
- `templates/accounts/explore.html` shows all other student profiles with Like and Pass buttons.
- `templates/accounts/matches.html` shows students who mutually liked the logged-in user.
- `templates/accounts/chat_list.html` shows all chat rooms for the logged-in user's matches.
- `templates/accounts/chat_room.html` shows one chat room with HTTP send + polling (works on Vercel/Railway).
- `templates/accounts/notifications.html` shows likes, matches, and message notifications, with a button to mark them as read.
- `templates/accounts/premium_plans.html` shows available premium subscription plans.
- `templates/accounts/payment_checkout.html` opens Razorpay Checkout for a selected plan.
- `templates/accounts/payment_failure.html` explains when payment is cancelled or fails.
- `templates/accounts/payment_history.html` lists a user's payment records.
- `templates/accounts/who_liked_you.html` shows a premium-only list of users who liked the current user.
- `templates/registration/login.html` is the login page used by Django's built-in login view.
- `templates/registration/signup.html` is the signup page.

### `static/` styling

- `static/css/styles.css` contains custom styles that sit on top of Bootstrap.

### Uploaded media

- `media/` is created when users upload files. Profile pictures are stored inside `media/profile_pictures/`. This folder is ignored by Git because uploaded user files are local data, not source code.

## Useful Commands

```powershell
py manage.py migrate
py manage.py createsuperuser
py manage.py runserver
```

## Production deployment

See **[DEPLOY.md](DEPLOY.md)** for step-by-step Vercel and Railway deployment with Neon PostgreSQL.

## Chat

Chat uses standard HTTP (POST to send, polling every 3 seconds for new messages). No WebSockets required — works on serverless hosts.

Run the app normally:

```powershell
py manage.py runserver
```

Chat URLs:

- `/accounts/chats/` shows your chat list.
- `/accounts/chats/<room_id>/` opens a chat room.
- Chat uses HTTP POST + polling (no WebSocket URL required).

## Notifications Setup

Notifications are stored in the database with the `Notification` model.

- `recipient` is the user who receives the notification.
- `sender` is the user who caused the notification.
- `notification_type` is `like`, `match`, or `message`.
- `message` is the text shown to the user.
- `is_read` controls whether it appears in the unread count.
- `timestamp` stores when it happened.

Where notifications are created:

- A like notification is created in `accounts/views.py` when a user likes another profile.
- Match notifications are created in `accounts/views.py` when two users like each other.
- Message notifications are created in `accounts/consumers.py` when a WebSocket chat message is saved.

The navbar badge works through `accounts/context_processors.py`, which counts unread notifications on every page load. The navbar dropdown shows the latest five notifications, and `/accounts/notifications/` shows the full notifications page.

## Premium And Razorpay Setup

Premium uses three main models:

- `PremiumPlan` stores plan name, price, duration, and whether the plan is active.
- `PremiumSubscription` stores whether a user is premium, expiry date, and profile boost status.
- `PaymentHistory` stores Razorpay order ID, payment ID, signature, amount, status, and payment timestamps.

Set Razorpay keys as environment variables before running the server:

```powershell
$env:RAZORPAY_KEY_ID="rzp_test_your_key_id"
$env:RAZORPAY_KEY_SECRET="your_key_secret"
py manage.py runserver
```

Payment flow:

1. User opens `/accounts/premium/`.
2. User selects a plan.
3. Django creates a Razorpay order on the backend.
4. Razorpay Checkout opens in the browser.
5. Razorpay sends `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature` back.
6. Django verifies the signature on the backend.
7. If verification passes, ECO activates premium and sets the expiry date.

Premium features:

- Free users get 5 likes per 24-hour window.
- Premium users get unlimited likes.
- Premium users can open `/accounts/premium/who-liked-you/`.
- Premium profiles show a Premium badge.
- Boosted premium profiles are sorted higher on Explore.
