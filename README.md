# Image & Video QA (Django)

A Django web application for QA-style validation of uploaded creative images, with user registration, approver-based activation, profile management, and tabular image metadata review.

## What this app does

- Supports email-based authentication with a custom user model.
- Provides registration with domain validation and approver selection.
- Uses an email confirmation plus approver activation flow before full access.
- Lets authenticated users upload one or more images for QA checks.
- Extracts image metadata (type, size, dimensions) and compares dimensions encoded in filename vs. actual image dimensions.
- Shows upload results in a table and supports single-image preview.

## Tech stack

- Python + Django
- SQLite (default local database)
- Pillow for image processing
- django-import-export for admin import/export
- django-cleanup for automatic media cleanup

See [requirements.txt](requirements.txt) for the full dependency list.

## Project structure

High-level layout:

```text
image-video-qa/
├── README.md
├── requirements.txt
└── src/
		├── manage.py
		├── core/        # project settings, root URLs, landing page
		├── accounts/    # custom user/auth forms/admin
		├── users/       # registration, profile, activation/email flow
		├── image/       # upload and image metadata QA logic
		├── templates/   # HTML templates
		├── static/      # CSS/JS/images
		├── media/       # uploaded media
		└── db.sqlite3   # local DB
```

## Docker Compose setup (no local Python package install)

All dependencies are installed inside Docker image layers. You do not need to install any Python packages on your host machine.

1. Build and start the app:

```bash
docker compose up --build -d
```

2. Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

3. Open the app:

- Landing page: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

4. Stop containers:

```bash
docker compose down
```

## First-run admin bootstrap

For registration/approval to work as intended, initialize approver data in admin:

1. Sign in to `/admin/` with your superuser.
2. Create or identify the user who should act as approver (its email is used in approval checks).
3. Create an `Approvers` record for that approver user.

The registration form sources approver options from `Approvers` entries.

## Core URL map

- `/` -> landing page
- `/image/` -> image upload + QA results table (login required)
- `/image/creative-img/image/<id>/` -> single image preview (login required)
- `/user/login/`, `/user/logout/`
- `/user/register/` -> registration
- `/user/profile/` -> update name/profile image
- `/user/email/confirmation/<activation_key>/` -> requester email confirmation
- `/user/activation/confirmation/<activation_key>/` -> approver-driven account activation
- `/user/change-password/`
- `/user/password-reset/*` -> password reset flow

## Image QA behavior

When files are uploaded at `/image/`:

- Only files with `image/*` content type are processed.
- For each image, the app stores:
	- file name
	- size
	- MIME subtype (as `img_type`)
	- actual width/height from Pillow
	- width/height parsed from filename pattern like `300x250`
- Table output includes a boolean-style comparison of actual vs filename dimensions.
- Only the latest upload batch per user is retained in `ImageTable`.

## Email and activation flow

1. User registers.
2. App sends a confirmation email to the requester.
3. After requester confirms email, app emails the selected approver.
4. Approver visits activation link while logged in.
5. Requester account is activated.

Notes:

- `send_mail(..., fail_silently=True)` is used in views, so email misconfiguration may fail quietly.
- Configure Django email settings in [src/core/settings.py](src/core/settings.py) for real mail delivery.

## Domain restrictions

Registration email domains are restricted by [src/users/allowed_email_domains.py](src/users/allowed_email_domains.py).

Current list:

- `annalect.com`
- `omc.com`
- `gmail.com`
- `yahoo.com`
- `outlook.com`

## Configuration notes

- Default DB is SQLite at [src/db.sqlite3](src/db.sqlite3).
- In Docker Compose, SQLite is moved to `/data/db.sqlite3` via the `SQLITE_PATH` environment variable and persisted in a Docker volume.
- Media uploads are stored under [src/media](src/media).
- Static assets live under [src/static](src/static).
- EXIF executable path can now be configured by environment variable `EXIF_PATH`.

### Google Cloud media storage

For Cloud Run deployments using `deployment.py`:

- Static files are uploaded to a timestamped prefix in the configured bucket.
- Local media files from `src/media` are backfilled to `gs://<bucket>/media` during deploy.
- Runtime uploads are written directly to the same bucket prefix via Django storage settings.

The deployment script now sets these runtime environment variables automatically:

- `USE_GCS_MEDIA=True`
- `GS_BUCKET_NAME=<bucket-name>`
- `GS_MEDIA_PREFIX=media` (customizable with `--media-prefix`)
- `GS_QUERYSTRING_AUTH=False`

Ensure the Cloud Run runtime service account has object write access to the bucket (for example `roles/storage.objectAdmin`).

### Google Cloud Run auto-deploy command

Run this from the repository root to deploy the app to Cloud Run, upload static files, backfill local media to `gs://<bucket>/media`, and set runtime environment variables:

```bash
python3 deployment.py \
	--project-id YOUR_GCP_PROJECT_ID \
	--region us-central1 \
	--service image-video-qa-static \
	--source . \
	--bucket-name YOUR_GCS_BUCKET_NAME \
	--service-account YOUR_CLOUD_RUN_SERVICE_ACCOUNT \
	--allow-unauthenticated
```

Optional flags:

- `--media-prefix media` to change the media folder prefix in the bucket.
- `--static-release-dir 20260622-120000` to control static release path naming.
- `--set-env KEY=VALUE` (repeatable) to inject extra runtime environment variables.
- `--skip-install-requirements` if dependencies are already installed in the chosen Python environment.

## Common container commands

```bash
# Make migrations
docker compose exec web python manage.py makemigrations

# Apply migrations
docker compose exec web python manage.py migrate

# Django shell
docker compose exec web python manage.py shell

# Follow logs
docker compose logs -f web

# Rebuild image after requirements changes
docker compose up --build -d
```

## Troubleshooting

- `No approver choices during registration`:
	- Add at least one `Approvers` entry in admin.
- `Uploaded files not appearing`:
	- Ensure files are actual images (`image/*` content type).
- `Activation link says unauthorized approver`:
	- The logged-in user email must match the requester's selected approver email.
- `No email received`:
	- Configure SMTP/email backend in settings and verify sender/domain policies.

## Security and production notes

This repository is currently configured for development defaults (`DEBUG=True`, local SQLite, development static/media behavior). Before production deployment:

- Move sensitive values (for example `SECRET_KEY`) to environment variables.
- Set `DEBUG=False`.
- Configure `ALLOWED_HOSTS`.
- Configure a production database and storage strategy.
- Add proper email backend configuration.

