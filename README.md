# Blockchain Demo

## Usage
``` shell
# 启动容器
docker-compose up

# 查看正在运行容器的ID
docker ps

# 进入正在运行的容器
docker exec -it ${CONTAINER ID} /bin/bash

# 全节点容器内运行全节点
cd LW-BC-IDMS/
python full_node.py

# 轻节点容器内运行轻节点测试程序
cd LW-BC-IDMS/
python test_node.py
```
