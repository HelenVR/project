#!/bin/sh
docker rm -f task_planner
docker run \
-e APP_PORT=8001 \
-e CONFIG_FILE=/usr/task_planner/task_planner/configs/config.yaml \
-e STATIC_DIR=/usr/task_planner/task_planner/static \
-e TEMPLATES_DIR=/usr/task_planner/task_planner/templates \
-v $(pwd)/task_planner/configs/config.yaml:/usr/task_planner/task_planner/configs/config.yaml \
-v $(pwd)/task_planner/static:/usr/task_planner/task_planner/static \
-v $(pwd)/task_planner/templates:/usr/task_planner/task_planner/templates \
--network=host \
--restart=always \
--name=task_planner \
--detach=true \
task_planner:1.0.0
