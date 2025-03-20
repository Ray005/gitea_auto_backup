import os
import json
import logging
import re
import requests
from flask import Flask, request, jsonify
from base64 import b64encode

# 确保日志目录存在
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "webhook_receiver.log")),  # 使用绝对路径
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook-receiver")

app = Flask(__name__)

# 从环境变量获取配置
TARGET_GITEA_URL = os.getenv('TARGET_GITEA_URL')
TARGET_GITEA_USERNAME = os.getenv('TARGET_GITEA_USERNAME')
TARGET_GITEA_TOKEN = os.getenv('TARGET_GITEA_TOKEN')     # 改回使用token
SOURCE_GITEA_URL = os.getenv('SOURCE_GITEA_URL')        # 新增源Gitea URL
SOURCE_GITEA_USERNAME = os.getenv('SOURCE_GITEA_USERNAME')
SOURCE_GITEA_TOKEN = os.getenv('SOURCE_GITEA_TOKEN')

# 更新必需的环境变量列表
required_env_vars = [
    'TARGET_GITEA_URL', 
    'TARGET_GITEA_USERNAME', 
    'TARGET_GITEA_TOKEN',  # 改回检查token环境变量
    'SOURCE_GITEA_URL',    # 新增检查项
    'SOURCE_GITEA_USERNAME',
    'SOURCE_GITEA_TOKEN'
]

# 验证环境变量是否设置
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
    raise EnvironmentError(f"缺少必要的环境变量: {', '.join(missing_vars)}")

logger.info("Webhook接收器启动中...")

def validate_repo_name(repo_name):
    """验证仓库名是否符合规范"""
    # 通常仓库名只允许字母、数字、下划线、短横线和点
    pattern = r'^[a-zA-Z0-9_\-\.]+$'
    return bool(re.match(pattern, repo_name))

def check_target_repo_exists(owner, repo_name):
    """检查目标Gitea实例中是否已存在同名仓库"""
    url = f"{TARGET_GITEA_URL}/api/v1/repos/{owner}/{repo_name}"
    headers = {'Authorization': f'token {TARGET_GITEA_TOKEN}'}
    
    try:
        response = requests.get(url, headers=headers, verify=False) # 添加 verify=False,不使用ssl认证
        exists = response.status_code == 200
        if exists:
            logger.info(f"目标仓库 {owner}/{repo_name} 已存在")
        else:
            logger.info(f"目标仓库 {owner}/{repo_name} 不存在")
        return exists
    except Exception as e:
        logger.error(f"检查仓库存在性失败: {str(e)}")
        return False

def create_mirror_repo(source_clone_url, owner, repo_name, description=""):
    """创建镜像仓库"""
    url = f"{TARGET_GITEA_URL}/api/v1/repos/migrate"
    
    headers = {
        'Authorization': f'token {TARGET_GITEA_TOKEN}',
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # 直接使用SOURCE_GITEA_URL构建认证URL
    # 在clone_addr中添加认证信息
    source_url_parts = source_clone_url.split('://')
    repo_path = source_url_parts[1].split('/', 1)[1]  # 去掉域名部分,只保留路径
    source_gitea_url = SOURCE_GITEA_URL.rstrip('/') # 从环境变量中读取要克隆的地址，而不是从payload中，这样会更稳定
    clone_addr = f"{source_gitea_url}/{repo_path}"
    print(clone_addr)
    data = {
        "clone_addr": clone_addr,
        "repo_name": repo_name,
        "repo_owner": owner,
        "mirror": True,
        "private": True,
        "description": description,
        "mirror_interval": "8h",
        "service": "gitea",
        "wiki": True,
        "issues": True,
        "pull_requests": True,
        "releases": True,
        "lfs": True,
        "auth_token": SOURCE_GITEA_TOKEN
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, verify=False)
        if response.status_code in (201, 200):
            logger.info(f"成功创建镜像仓库: {owner}/{repo_name}")
            return True
        else:
            logger.error(f"创建镜像仓库失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"创建镜像仓库时发生错误: {str(e)}")
        return False

@app.route('/', methods=['POST'])
def handle_webhook():
    # 验证请求头和内容类型
    if 'X-Gitea-Event' not in request.headers:
        logger.warning("收到非Gitea webhook请求")
        return jsonify({"status": "error", "message": "非Gitea webhook请求"}), 400
    
    # 验证 webhook secret (如果设置了)
    if TARGET_GITEA_TOKEN:
        if 'X-Gitea-Signature' not in request.headers:
            logger.warning("缺少Webhook签名")
            return jsonify({"status": "error", "message": "缺少安全签名"}), 401
        
        # 此处可添加签名验证代码
        # ...
    
    # 解析请求数据
    try:
        payload = request.json
    except Exception as e:
        logger.error(f"解析JSON数据失败: {str(e)}")
        return jsonify({"status": "error", "message": "无效的JSON数据"}), 400
    
    # 验证payload必须字段
    if not payload or 'repository' not in payload:
        logger.warning("无效的webhook负载: 缺少repository信息")
        return jsonify({"status": "error", "message": "无效的webhook数据"}), 400
    
    # 提取仓库信息
    try:
        repo_info = payload['repository']
        repo_name = repo_info.get('name')
        repo_owner = repo_info.get('owner', {}).get('username')
        clone_url = repo_info.get('clone_url')
        repo_description = repo_info.get('description', '')
        
        # 附加验证
        event_type = request.headers.get('X-Gitea-Event')
        
        logger.info(f"收到 {event_type} 事件: {repo_owner}/{repo_name}")
        
        # 验证仓库名和克隆URL
        if not repo_name or not repo_owner or not clone_url:
            logger.warning("无效的仓库信息: 缺少名称、所有者或克隆URL")
            return jsonify({"status": "error", "message": "无效的仓库信息"}), 400
        
        if not validate_repo_name(repo_name):
            logger.warning(f"仓库名不符合规范: {repo_name}")
            return jsonify({"status": "error", "message": "仓库名不符合规范"}), 400

        # 检查目标实例中是否已存在该仓库
        target_owner = TARGET_GITEA_USERNAME
        if check_target_repo_exists(target_owner, repo_name):
            logger.info(f"仓库 {target_owner}/{repo_name} 已存在，无需创建")
            return jsonify({"status": "success", "message": "仓库已存在"}), 200
        
        # 创建镜像仓库
        success = create_mirror_repo(clone_url, target_owner, repo_name, repo_description)
        if success:
            return jsonify({"status": "success", "message": "成功创建镜像仓库"}), 200
        else:
            return jsonify({"status": "error", "message": "创建镜像仓库失败"}), 500
        
    except KeyError as e:
        logger.error(f"处理webhook数据时缺少关键字段: {str(e)}")
        return jsonify({"status": "error", "message": f"缺少关键字段: {str(e)}"}), 400
    
    except Exception as e:
        logger.error(f"处理webhook时发生未知错误: {str(e)}")
        return jsonify({"status": "error", "message": "内部服务器错误"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


