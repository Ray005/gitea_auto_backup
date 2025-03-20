# git自动备份到其他仓库

## 先决条件

* 涉及到三方面的host
    * source：需要备份的仓库
    * target：备份到的仓库
    * webhook receiver：接收source的webhook，并进行备份
* 网络拓扑至少要满足如下条件：

![alt text](<img/show.png>)

## 使用方法

``` bash
git clone https://github.com/Ray005/gitea_auto_backup.git/
cd gitea_auto_backup/dockerfile
```

### 准备工作：创建webhook、source和target的token

* 

### 第一步：构建镜像

``` bash
bash build.sh
```

### 第二步：运行容器

``` bash
# 编辑容器中的配置文件，填写恰当的如下参数
vim run.sh

-p 5000:5000 \ # 前一个为主机端口，选择后记得在防火墙开放。端口用来接收webhook
-e TARGET_GITEA_URL=https://100.102.101.xx:8418 \ # target的gitea地址
-e TARGET_GITEA_TOKEN=9xxxxxxxxxxxa \ # target的gitea token
-e TARGET_GITEA_USERNAME=xxx \ # target的gitea username
-e SOURCE_REPO_URL="http://xxxx:3000/xxx/xxx.git" \ 
-e SOURCE_GITEA_TOKEN="bxxxxxxxxxxxxxxxxx3" \ 
-e WEBHOOK_SECRET=xxxxxx \ # 与source的webhook secret一致（在创建source的webhook时设置）

# 运行容器
bash run.sh
```

