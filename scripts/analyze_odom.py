#!/usr/bin/env python3
"""Analisis Modul 5 - error odometri TurtleBot3.

Menghitung Tabel 5.2 (gerak lurus) dan Tabel 5.3 (rotasi) dari CSV hasil
spreadsheet, lalu membuat grafik lintasan odometri langsung dari rosbag2.

Tidak membutuhkan ROS terpasang: rosbag dibaca lewat sqlite3 dan pesan
nav_msgs/Odometry (CDR) di-decode manual. Bag boleh berupa .db3 biasa atau
.db3.zstd (rosbag2 --compression-mode file).

Jalankan dari root repository:
    python3 scripts/analyze_odom.py
"""
import math
import os
import sqlite3
import struct
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BAG_DIR = "data/bags/m05_straight_1m_t01"
BAG_NAME = "m05_straight_1m_t01_0.db3"
RES = "data/results"

# Jendela waktu tiap trial (detik sejak pesan pertama di bag), diambil dari
# segmen gerak pada /odom.
TRIAL_WINDOWS = {1: (765, 800), 2: (1228, 1262), 3: (1450, 1490),
                 4: (1620, 1652), 5: (1810, 1834)}


# ------------------------------------------------------------------ Tabel 5.2
def straight_table(yaw0):
    """yaw0: {trial: yaw awal robot di bingkai odom (rad)} dari rosbag."""
    df = pd.read_csv(f"{RES}/m05_straight.csv")
    df = df.rename(columns={"x_odom": "x_odom_raw", "y_odom": "y_odom_raw"})
    df["yaw0_deg"] = [math.degrees(yaw0[k]) for k in df.trial]
    # Sumbu x odom = arah 0 IMU (tidak ikut reset), bukan arah hadap robot.
    # Putar perpindahan sebesar -yaw0 agar x = maju, y = lateral kiri.
    c, s_ = np.cos(-df.yaw0_deg.map(math.radians)), np.sin(-df.yaw0_deg.map(math.radians))
    df["x_odom"] = c * df.x_odom_raw - s_ * df.y_odom_raw
    df["y_odom"] = s_ * df.x_odom_raw + c * df.y_odom_raw
    df["e_odom"] = np.hypot(df.x_odom - df.x_ref, df.y_odom - df.y_ref)
    df["e_fisik"] = np.hypot(df.x_meas - df.x_ref, df.y_meas - df.y_ref)
    df["delta_odom_fisik"] = np.hypot(df.x_odom - df.x_meas,
                                      df.y_odom - df.y_meas)
    # Ukuran tanpa rotasi (bingkai odom mentah)
    df["e_odom_raw"] = np.hypot(df.x_odom_raw - df.x_ref, df.y_odom_raw - df.y_ref)
    df["jarak_odom"] = np.hypot(df.x_odom_raw, df.y_odom_raw)
    df["arah_odom_deg"] = np.degrees(np.arctan2(df.y_odom_raw, df.x_odom_raw))
    df["e_sepanjang_lintasan"] = df.jarak_odom - 1.0
    return df


def summary(df, cols):
    n = len(df)
    out = df[cols].agg(["mean", "std", "min", "max"])
    out.loc["std_populasi"] = df[cols].std(ddof=0)
    # t-student dua sisi 95%, dof = n-1 (n kecil)
    t95 = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447,
           8: 2.365, 9: 2.306, 10: 2.262}[n]
    out.loc["ci95_halfwidth"] = t95 * df[cols].std(ddof=1) / math.sqrt(n)
    return out


# ------------------------------------------------------------------ Tabel 5.3
def rotation_table():
    r = pd.read_csv(f"{RES}/m05_rotation_raw.csv")
    df = pd.DataFrame({"trial": r.trial})
    df["theta_odom"] = 360 - (r.odom_qz_end - r.odom_qz_start)
    df["theta_imu"] = np.where(
        r.trial.isin([2, 4]),
        360 + (r.imu_qz_end - r.imu_qz_start),
        360 - (r.imu_qz_end - r.imu_qz_start))
    df.loc[3, "theta_imu"] = 360 - -(r.imu_qz_end[3] - r.imu_qz_start[3])
    df["theta_fisik"] = r.fisik_read_1 - r.fisik_read_2
    df["e_theta_odom"] = 360 - df.theta_odom
    df["e_theta_imu"] = 360 - df.theta_imu
    return df


# ------------------------------------------------------------------ rosbag2
def _align(o, n):  # CDR: alignment dihitung setelah header 4 byte
    return 4 + ((o - 4 + n - 1) // n) * n


def _parse_odom(b):
    o = 4 + 8                                   # header CDR + stamp
    o += 4 + struct.unpack_from("<I", b, o)[0]  # frame_id
    o = _align(o, 4)
    o += 4 + struct.unpack_from("<I", b, o)[0]  # child_frame_id
    o = _align(o, 8)
    x, y, _z, qx, qy, qz, qw = struct.unpack_from("<7d", b, o)
    return x, y, 2 * math.atan2(qz, qw)


def read_odom():
    path = os.path.join(BAG_DIR, BAG_NAME)
    tmp = None
    if not os.path.exists(path):
        import zstandard
        tmp = tempfile.NamedTemporaryFile(suffix=".db3", delete=False)
        with open(path + ".zstd", "rb") as f:
            zstandard.ZstdDecompressor().copy_stream(f, tmp)
        tmp.close()
        path = tmp.name
    db = sqlite3.connect(path)
    tid = db.execute("select id from topics where name='/odom'").fetchone()[0]
    rows = db.execute("select timestamp, data from messages "
                      "where topic_id=? order by timestamp", (tid,)).fetchall()
    db.close()
    if tmp:
        os.unlink(tmp.name)
    t = np.array([r[0] for r in rows]) / 1e9
    xyz = np.array([_parse_odom(r[1]) for r in rows])
    return t - t[0], xyz


def trial_yaw0(t, xyz):
    out = {}
    for k, (a, b) in TRIAL_WINDOWS.items():
        m = (t >= a) & (t <= b)
        out[k] = float(np.median(xyz[m, 2]))
    return out


# ------------------------------------------------------------------ grafik
def plot_trajectory(t, xyz, df):
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    for k, (a, b) in TRIAL_WINDOWS.items():
        m = (t >= a) & (t <= b)
        p = xyz[m, :2] - xyz[m, :2][0]
        y0 = math.radians(df.loc[df.trial == k, "yaw0_deg"].iloc[0])
        c, s_ = math.cos(-y0), math.sin(-y0)
        q = np.c_[c * p[:, 0] - s_ * p[:, 1], s_ * p[:, 0] + c * p[:, 1]]
        if k == 3:  # trial 3 dijalankan mundur; tanda dibalik (lihat laporan)
            q = -q
        ax.plot(q[:, 0], q[:, 1], lw=1.6, label=f"trial {k}")
    ax.plot([0, 1], [0, 0], "k--", lw=1, label="referensi (1, 0)")
    ax.plot(1, 0, "k*", ms=11)
    ax.set_xlim(-0.05, 1.1)
    ax.set_ylim(-0.15, 0.15)
    ax.set_xlabel("maju / x (m)")
    ax.set_ylabel("lateral / y (m)")
    ax.set_title("Lintasan /odom (bingkai arah hadap awal robot)")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8, ncol=3, loc="lower left")
    fig.tight_layout()
    fig.savefig(f"{RES}/m05_trajectory.png", dpi=170)
    plt.close(fig)


def plot_box(df):
    fig, ax = plt.subplots(figsize=(5.2, 4))
    ax.boxplot([df.e_odom, df.e_fisik, df.delta_odom_fisik],
               tick_labels=["e_odom\n(vs ref)", "e_fisik\n(vs ref)",
                            "\u0394 odom\u2013fisik"])
    ax.set_ylabel("error posisi (m)")
    ax.grid(alpha=.3, axis="y")
    fig.tight_layout()
    fig.savefig(f"{RES}/m05_error_box.png", dpi=170)
    plt.close(fig)


def main():
    pd.set_option("display.width", 160)
    t, xyz = read_odom()
    s = straight_table(trial_yaw0(t, xyz))
    s.to_csv(f"{RES}/m05_straight_computed.csv", index=False)
    print("== Tabel 5.2 (bingkai arah hadap awal robot) ==")
    print(s.round(4).to_string(index=False))
    print(summary(s, ["x_odom", "y_odom", "e_odom", "e_fisik", "delta_odom_fisik",
                      "jarak_odom", "e_sepanjang_lintasan"]).round(4))
    r = rotation_table()
    r.to_csv(f"{RES}/m05_rotation_computed.csv", index=False)
    print("\n== Tabel 5.3 ==")
    print(r.round(4).to_string(index=False))
    print(summary(r, ["theta_odom", "theta_imu", "theta_fisik",
                      "e_theta_odom", "e_theta_imu"]).round(4))
    plot_trajectory(t, xyz, s)
    plot_box(s)
    print("\nGrafik disimpan di", RES)


if __name__ == "__main__":
    main()
