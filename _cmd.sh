python3 deployment.py \
    --project-id development-490607 \
    --region us-central1 \
    --service image-video-qa-static \
    --source /home/sarbadal/image-video-qa-app \
    --bucket-name create-qa-static \
    --port 8000 \
    --allow-unauthenticated \
    --skip-install-requirements

gcloud run deploy image-video-qa-static \
    --source /home/sarbadal/image-video-qa-app \
    --project development-490607 --region us-central1 \
    --platform managed \
    --port 8000 \
    --set-build-env-vars 'GOOGLE_ENTRYPOINT=gunicorn \
    --bind :$PORT --chdir src core.wsgi:application' \
    --set-env-vars '^|^DJANGO_DEBUG=False|DJANGO_SECRET_KEY=B4aUvjk3X-0vt-no2Jq-pTS5pyDSolpnp2Dg2zx5-DsVhPe5WiliJqGXtaVZwripZEY|ALLOWED_HOSTS=.run.app,127.0.0.1,localhost|CSRF_TRUSTED_ORIGINS=https://*.run.app|STATIC_URL=https://storage.googleapis.com/create-qa-static/20260622-142427/static/|USE_GCS_MEDIA=True|GS_BUCKET_NAME=create-qa-static|GS_MEDIA_PREFIX=media|GS_QUERYSTRING_AUTH=False' \
    --quiet \
    --allow-unauthenticated