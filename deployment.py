#!/usr/bin/env python3
"""Deploy this Django app to Google Cloud Run with static sync to GCS.

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
from pathlib import Path


def run_cmd(command: list[str], *, env: dict[str, str] | None = None, dry_run: bool = False) -> str:
    """Run a command and stream output to the terminal."""
    print(f"\n$ {shlex.join(command)}")
    if dry_run:
        return ""
    completed = subprocess.run(command, env=env, check=True, text=True, capture_output=True)
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

    bucket_name = args.bucket or f"{project_id}-django-static"
    bucket_uri = f"gs://{bucket_name}"
    static_url = f"https://storage.googleapis.com/{bucket_name}/static/"

    print(f"Project: {project_id}")
    print(f"Region: {args.region}")
    print(f"Service: {args.service}")
    print(f"Bucket: {bucket_uri}")

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

    local_env = os.environ.copy()
    local_env.setdefault("DJANGO_DEBUG", "False")
    local_env.setdefault("ALLOWED_HOSTS", "127.0.0.1,localhost")
    local_env["STATIC_URL"] = static_url

    print("Collecting static files...")
    run_cmd(
        [args.python, str(manage_py), "collectstatic", "--noinput", "--clear"],
        env=local_env,
        dry_run=args.dry_run,
    )

    print("Syncing static files to GCS...")
    run_cmd(
        [
            "gcloud",
            "storage",
            "rsync",
            "--recursive",
            "--delete-unmatched-destination-objects",
            str(static_dir),
            f"{bucket_uri}/static",
            "--project",
            project_id,
        ],
        dry_run=args.dry_run,
    )

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
        ",".join(f"{k}={v}" for k, v in env_vars.items()),
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
        description="Deploy Django app to Google Cloud Run and upload static files to GCS."
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
    parser.add_argument("--bucket", help="GCS bucket name for static files.")
    parser.add_argument("--bucket-location", default="US", help="Bucket location (for new buckets).")
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


    # python3 deployment.py --project-id YOUR_PROJECT_ID --region us-central1 --service image-video-qa --allow-unauthenticated
