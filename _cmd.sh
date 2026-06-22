python3 deployment.py \
    --project-id development-490607 \
    --region us-central1 \
    --service image-video-qa-static \
    --source /home/sarbadal/image-video-qa-app \
    --bucket-name create-qa-static \
    --port 8000 \
    --allow-unauthenticated \
    --skip-install-requirements