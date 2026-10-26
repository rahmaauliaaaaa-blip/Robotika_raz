# lab_motion

Package ROS 2 Humble (`ament_python`) untuk **Modul 6 Praktikum Robotika**:
kontrol gerak *differential-drive* TurtleBot3 Burger.

| Executable    | Fungsi                                                    |
|---------------|-----------------------------------------------------------|
| `open_loop`   | Gerak berbasis durasi (tidak membaca `/odom`)             |
| `closed_loop` | Go-to-goal proporsional dengan umpan balik `/odom` + watchdog |

Lintasan (`-p trajectory:=...`): `line` (A), `rotate` (B), `square` (C), `figure8` (D).

## Build

```bash
cd /ws/src
git clone https://github.com/<username>/lab_motion.git
cd /ws
colcon build --packages-select lab_motion --symlink-install
source /ws/install/setup.bash
ros2 pkg executables lab_motion
```

## Menjalankan

```bash
# Open-loop (default v=0.10 m/s, w=0.50 rad/s)
ros2 run lab_motion open_loop --ros-args -p trajectory:=line
ros2 run lab_motion open_loop --ros-args -p trajectory:=rotate

# Closed-loop
ros2 run lab_motion closed_loop --ros-args -p trajectory:=line
ros2 run lab_motion closed_loop --ros-args \
  -p trajectory:=square -p v_max:=0.10 -p w_max:=0.50

# Sensitivitas gain (Tabel 6.3)
ros2 run lab_motion closed_loop --ros-args \
  -p trajectory:=line -p k_rho:=0.3 -p k_alpha:=1.0 \
  -p v_max:=0.10 -p w_max:=0.50 -p tol_pos:=0.03
```

## Parameter closed_loop

| Parameter     | Default | Arti                                   |
|---------------|---------|----------------------------------------|
| `k_rho`       | 0.6     | gain jarak -> kecepatan linear         |
| `k_alpha`     | 1.5     | gain selisih arah -> kecepatan sudut   |
| `v_max`       | 0.15    | batas kecepatan linear (m/s)           |
| `w_max`       | 1.0     | batas kecepatan sudut (rad/s)          |
| `tol_pos`     | 0.03    | toleransi posisi (m)                   |
| `tol_heading` | 5 deg   | toleransi heading (rad)                |

## Catatan

- Pastikan tidak ada publisher `/cmd_vel` lain (teleop) saat controller berjalan.
- `closed_loop` berhenti otomatis jika `/odom` tidak diterima > 0,5 s.
- Rekam data: `ros2 bag record -o /ws/data/bags/<nama_trial> /odom /cmd_vel`
