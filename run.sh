docker run -d \
  --name webhook-receiver \
  -p 5000:5000 \
  -e TARGET_GITEA_URL=https://100.102.101.xx:8418 \
  -e TARGET_GITEA_TOKEN=90f618xxxxxxxxxxdae08ad2ae69a \
  -e TARGET_GITEA_USERNAME=xxx \
  -e SOURCE_REPO_URL="http://xxxx:3000/xxx/xxx.git" \ 
  -e SOURCE_GITEA_TOKEN="bxxxxxxxxxxxxxxxxx3" \ 
  -e WEBHOOK_SECRET=xxxxxx \
  -v $(pwd)/logs:/app/logs \
  --restart always \
  gitea-webhook-handler:latest

