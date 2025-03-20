docker run -d \
  --name webhook-receiver \
  -p 5000:5000 \
  -e TARGET_GITEA_URL="http://xxxxx:8418" \
  -e TARGET_GITEA_USERNAME="xxxx" \
  -e TARGET_GITEA_TOKEN="xxxxxxxxxxxxxxxx" \
  -e SOURCE_GITEA_URL="http://xxxx:xxx" \
  -e SOURCE_GITEA_USERNAME=xxxx \
  -e SOURCE_GITEA_TOKEN="xxxxxxxxxxx" \
  -e WEBHOOK_SECRET="xxxx" \
  -v $(pwd)/logs:/app/logs \
  --restart always \
  gitea-webhook-handler:latest \
  python webhook_receiver.py

