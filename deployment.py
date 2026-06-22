#!/usr/bin/env python3
"""Deploy this Django app to Google Cloud Run with static and media sync to GCS.

Example:
    python deployment.py --project-id my-gcp-project --region us-central1
"""

from __future__ import annotations

import argparse
import os
import secrets
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_cmd(command: list[str], *, env: dict[str, str] | None = None, dry_run: bool = False) -> str:
    """Run a command and stream output to the terminal."""
    print(f"\n$ {shlex.join(command)}")
    if dry_run:
        return ""
    try:
        completed = subprocess.run(command, env=env, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout.strip())
        if exc.stderr:
            print(exc.stderr.strip(), file=sys.stderr)
        raise
    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip())
    return completed.stdout.strip()


def command_exists(command: str) -> bool:
    try:
        subprocess.run([command, "--version"], check=True, text=True, capture_output=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_active_project() -> str | None:
    try:
        output = run_cmd(["gcloud", "config", "get-value", "project"])
    except subprocess.CalledProcessError:
        return None

    value = output.strip()
    if not value or value == "(unset)":
        return None
    return value


def ensure_bucket(project_id: str, bucket_name: str, location: str, dry_run: bool = False) -> None:
    bucket_uri = f"gs://{bucket_name}"
    if dry_run:
        run_cmd(
            ["gcloud", "storage", "buckets", "describe", bucket_uri, "--project", project_id],
            dry_run=True,
        )
        run_cmd(
            [
                "gcloud",
                "storage",
                "buckets",
                "create",
                bucket_uri,
                "--project",
                project_id,
                "--location",
                location,
                "--uniform-bucket-level-access",
            ],
            dry_run=True,
        )
        return

    try:
        run_cmd(["gcloud", "storage", "buckets", "describe", bucket_uri, "--project", project_id])
        print(f"Bucket exists: {bucket_uri}")
    except subprocess.CalledProcessError:
        print(f"Bucket not found. Creating {bucket_uri} in {location}...")
        run_cmd(
            [
                "gcloud",
                "storage",
                "buckets",
                "create",
                bucket_uri,
                "--project",
                project_id,
                "--location",
                location,
                "--uniform-bucket-level-access",
            ]
        )


def ensure_public_object_access(bucket_name: str, dry_run: bool = False) -> None:
    """Grant public read access to bucket objects for static hosting."""
    run_cmd(
        [
            "gcloud",
            "storage",
            "buckets",
            "add-iam-policy-binding",
            f"gs://{bucket_name}",
            "--member=allUsers",
            "--role=roles/storage.objectViewer",
        ],
        dry_run=dry_run,
    )


def parse_extra_env(values: list[str]) -> dict[str, str]:
    env_vars: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Invalid --set-env value: {raw}. Expected KEY=VALUE.")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid --set-env key in: {raw}")
        env_vars[key] = value
    return env_vars


def format_gcloud_env_vars(env_vars: dict[str, str]) -> str:
    """Format env vars for gcloud flags, supporting comma-containing values.

    gcloud splits --set-env-vars values by comma by default, which breaks
    values such as ALLOWED_HOSTS that legitimately include commas.
    """
    delimiter = "|"
    for key, value in env_vars.items():
        if delimiter in key or delimiter in value:
            raise ValueError(
                f"Unsupported character '{delimiter}' in environment key/value for: {key}"
            )
    joined = delimiter.join(f"{k}={v}" for k, v in env_vars.items())
    return f"^{delimiter}^{joined}"


def install_requirements(args: argparse.Namespace, source_dir: Path) -> None:
    """Install Python dependencies into the interpreter used for deployment steps."""
    if args.skip_install_requirements:
        return

    requirements_file = source_dir / "requirements.txt"
    if not requirements_file.exists():
        print("requirements.txt not found. Skipping dependency installation.")
        return

    print(f"Installing dependencies from {requirements_file}...")
    try:
        run_cmd(
            [args.python, "-m", "pip", "install", "-r", str(requirements_file)],
            dry_run=args.dry_run,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Dependency installation failed for the selected interpreter. "
            "Use --python with a writable virtualenv interpreter, then retry."
        ) from exc


def deploy(args: argparse.Namespace) -> None:
    if not command_exists("gcloud"):
        raise RuntimeError("gcloud CLI is not installed or not available in PATH.")

    project_id = args.project_id or get_active_project()
    if not project_id:
        raise RuntimeError(
            "No project configured. Provide --project-id or run: gcloud config set project <PROJECT_ID>"
        )

    source_dir = Path(args.source).resolve()
    if not source_dir.exists():
        raise RuntimeError(f"Source directory does not exist: {source_dir}")

    manage_py = (source_dir / args.manage_py).resolve()
    if not manage_py.exists():
        raise RuntimeError(f"manage.py not found at: {manage_py}")

    static_dir = (source_dir / args.static_dir).resolve()
    static_dir.mkdir(parents=True, exist_ok=True)
    media_dir = (source_dir / args.media_dir).resolve()

    bucket_name = args.bucket_name or args.bucket or f"{project_id}-django-static"
    bucket_uri = f"gs://{bucket_name}"
    static_release_dir = args.static_release_dir or datetime.now(timezone.utc).strftime(
        "%Y%m%d-%H%M%S"
    )
    media_prefix = args.media_prefix.strip("/")
    if not media_prefix:
        raise RuntimeError("--media-prefix cannot be empty")
    static_prefix = f"{static_release_dir}/static"
    static_url = f"https://storage.googleapis.com/{bucket_name}/{static_prefix}/"

    print(f"Project: {project_id}")
    print(f"Region: {args.region}")
    print(f"Service: {args.service}")
    print(f"Bucket: {bucket_uri}")
    print(f"Static release dir: {static_release_dir}")
    print(f"Media prefix: {media_prefix}")

    run_cmd(["gcloud", "config", "set", "project", project_id], dry_run=args.dry_run)

    # Enable required APIs once; safe to run repeatedly.
    run_cmd(
        [
            "gcloud",
            "services",
            "enable",
            "run.googleapis.com",
            "cloudbuild.googleapis.com",
            "artifactregistry.googleapis.com",
            "--project",
            project_id,
        ],
        dry_run=args.dry_run,
    )

    ensure_bucket(
        project_id=project_id,
        bucket_name=bucket_name,
        location=args.bucket_location,
        dry_run=args.dry_run,
    )
    ensure_public_object_access(bucket_name=bucket_name, dry_run=args.dry_run)

    install_requirements(args=args, source_dir=source_dir)

    local_env = os.environ.copy()
    local_env.setdefault("DJANGO_DEBUG", "False")
    local_env.setdefault("ALLOWED_HOSTS", "127.0.0.1,localhost")
    local_env["STATIC_URL"] = static_url

    print("Collecting static files...")
    try:
        run_cmd(
            [args.python, str(manage_py), "collectstatic", "--noinput", "--clear"],
            env=local_env,
            dry_run=args.dry_run,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "collectstatic failed. Ensure dependencies are installed in the interpreter passed via "
            "--python and retry. Example: --python /path/to/venv/bin/python"
        ) from exc

    print("Syncing static files to GCS...")
    run_cmd(
        [
            "gcloud",
            "storage",
            "rsync",
            "--recursive",
            "--delete-unmatched-destination-objects",
            str(static_dir),
            f"{bucket_uri}/{static_prefix}",
            "--project",
            project_id,
        ],
        dry_run=args.dry_run,
    )

    if media_dir.exists():
        print("Syncing local media files to GCS...")
        run_cmd(
            [
                "gcloud",
                "storage",
                "rsync",
                "--recursive",
                str(media_dir),
                f"{bucket_uri}/{media_prefix}",
                "--project",
                project_id,
            ],
            dry_run=args.dry_run,
        )
    else:
        print(f"Media directory not found, skipping media sync: {media_dir}")

    secret_key = args.secret_key or os.getenv("DJANGO_SECRET_KEY")
    if not secret_key:
        secret_key = secrets.token_urlsafe(50)
        print("Generated temporary DJANGO_SECRET_KEY for deployment.")

    env_vars = {
        "DJANGO_DEBUG": "False",
        "DJANGO_SECRET_KEY": secret_key,
        "ALLOWED_HOSTS": ".run.app,127.0.0.1,localhost",
        "CSRF_TRUSTED_ORIGINS": "https://*.run.app",
        "STATIC_URL": static_url,
        "USE_GCS_MEDIA": "True",
        "GS_BUCKET_NAME": bucket_name,
        "GS_MEDIA_PREFIX": media_prefix,
        "GS_QUERYSTRING_AUTH": "False",
    }
    env_vars.update(parse_extra_env(args.set_env))

    deploy_cmd = [
        "gcloud",
        "run",
        "deploy",
        args.service,
        "--source",
        str(source_dir),
        "--project",
        project_id,
        "--region",
        args.region,
        "--platform",
        "managed",
        "--port",
        str(args.port),
        "--set-build-env-vars",
        "GOOGLE_ENTRYPOINT=gunicorn --bind :$PORT --chdir src core.wsgi:application",
        "--set-env-vars",
        format_gcloud_env_vars(env_vars),
        "--quiet",
    ]

    if args.allow_unauthenticated:
        deploy_cmd.append("--allow-unauthenticated")

    if args.service_account:
        deploy_cmd.extend(["--service-account", args.service_account])

    run_cmd(deploy_cmd, dry_run=args.dry_run)

    print("\nDeployment finished successfully.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deploy Django app to Google Cloud Run and upload static/media files to GCS."
    )
    parser.add_argument("--project-id", help="Google Cloud project ID. Defaults to active gcloud project.")
    parser.add_argument("--region", default="us-central1", help="Cloud Run region.")
    parser.add_argument("--service", default="image-video-qa", help="Cloud Run service name.")
    parser.add_argument("--source", default=".", help="Source directory for Cloud Run deployment.")
    parser.add_argument("--manage-py", default="src/manage.py", help="Path to manage.py from source dir.")
    parser.add_argument(
        "--static-dir",
        default="src/staticfiles",
        help="Directory populated by collectstatic and synced to GCS.",
    )
    parser.add_argument(
        "--media-dir",
        default="src/media",
        help="Local media directory to backfill into GCS before deploy.",
    )
    parser.add_argument("--bucket-name", help="GCS bucket name for static files.")
    parser.add_argument(
        "--bucket",
        help="Backward-compatible alias for --bucket-name.",
    )
    parser.add_argument("--bucket-location", default="US", help="Bucket location (for new buckets).")
    parser.add_argument(
        "--static-release-dir",
        help="Static release subdirectory in yyyymmdd-hhmmss format. Defaults to current UTC timestamp.",
    )
    parser.add_argument(
        "--media-prefix",
        default="media",
        help="Bucket path prefix used for Django media uploads.",
    )
    parser.add_argument("--python", default=sys.executable or "python3", help="Python executable to run manage.py")
    parser.add_argument("--port", type=int, default=8080, help="Container port for Cloud Run.")
    parser.add_argument("--secret-key", help="Django secret key for Cloud Run runtime.")
    parser.add_argument(
        "--allow-unauthenticated",
        action="store_true",
        help="Allow public unauthenticated access to the Cloud Run service.",
    )
    parser.add_argument("--service-account", help="Runtime service account email for Cloud Run service.")
    parser.add_argument(
        "--set-env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Additional Cloud Run runtime environment variables. Can be repeated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them.",
    )
    parser.add_argument(
        "--skip-install-requirements",
        action="store_true",
        help="Skip running '<python> -m pip install -r requirements.txt' before collectstatic.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        deploy(args)
    except (RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Deployment failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# python3 deployment.py \
#   --project-id development-490607 \
#   --region us-central1 \
#   --service image-video-qa-static \
#   --source /home/sarbadal/image-video-qa-app \
#   --bucket-name development-490607-django-static \
#   --allow-unauthenticated \
#   --skip-install-requirements

# python3 deployment.py \
#     --project-id development-490607 \
#     --region us-central1 \
#     --service image-video-qa-static \
#     --source . \
#     --bucket-name  create-qa-static \
#     --allow-unauthenticated \
#     --skip-install-requirements
