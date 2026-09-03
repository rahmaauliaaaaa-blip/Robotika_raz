# Robotics TurtleBot3 — Praktikum Robotika

Repository ini berisi environment pengembangan ROS 2 Humble yang di-containerize dengan Docker, dipakai selama praktikum Modul 1–12.

## Requirements
- Docker Engine >= 24
- Docker Compose plugin >= v2.20
- WSL2 dengan Ubuntu 22.04 (untuk pengguna Windows)

## Cara Build & Run

1. Clone repository ini:
   git clone <URL-repo-ini>
   cd robotics-turtlebot3

2. Set variabel environment (opsional, ada default-nya):
   export HOST_UID=$(id -u) HOST_GID=$(id -g) ROS_DOMAIN_ID=31

3. Masuk ke folder docker, build image, dan nyalakan container:
   cd docker
   docker compose build
   docker compose up -d

4. Masuk ke dalam container:
   docker compose exec dev bash

5. Build workspace ROS 2:
   cd /ws
   colcon build --symlink-install
   source install/setup.bash

6. Jalankan node contoh:
   ros2 run my_first_robot_package hello_robot

## Struktur Folder
- docker/       -> Dockerfile, compose.yaml, entrypoint.sh
- src/          -> ROS 2 package (workspace source)
- config/       -> file konfigurasi
- launch/       -> ROS 2 launch files
- data/, maps/  -> data dan peta hasil eksperimen
- docs/         -> laporan modul

## Catatan
- Folder build/, install/, log/ TIDAK di-commit ke Git (lihat .gitignore), karena berupa artefak hasil build yang dibuat ulang otomatis.
- Commit hash rilis terakhir: (isi manual setelah commit)
