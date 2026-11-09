import sys
import numpy as np
import yaml
from PIL import Image

# Setup default file atau mengambil dari argumen command-line
pgm = sys.argv[1] if len(sys.argv) > 1 else 'lab_map_slow.pgm'
yml = pgm.replace('.pgm', '.yaml')

# Membaca resolusi dari file YAML
with open(yml) as f:
    res = yaml.safe_load(f)['resolution']

    # Membaca gambar PGM sebagai array numpy
    img = np.array(Image.open(pgm))
    print('ukuran peta (baris x kolom):', img.shape)

    # Menentukan status sel (berdasarkan threshold warna PGM)
    occupied = img < 100
    unknown = (img > 200) & (img < 210)

    print('occupied cells:', occupied.sum())
    print('unknown cells:', unknown.sum())
    print('unknown (%):', round(100 * unknown.sum() / img.size, 1))

    # Ukur jarak antar dua dinding pada satu baris (atau kolom)
    mode = sys.argv[3] if len(sys.argv) > 3 else 'baris'

    # Memilih baris atau kolom yang akan diukur
    if mode == 'kolom':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else img.shape[1] // 2
        line = occupied[:, n]
    else:
        n = int(sys.argv[2]) if len(sys.argv) > 2 else img.shape[0] // 2
        line = occupied[n]

                    # Mencari indeks sel yang merupakan dinding (occupied)
    idx = np.where(line)[0]

                    # Menghitung jarak jika ditemukan minimal dua sisi dinding
    if len(idx) >= 2:
        print(mode, n, '-> jarak antar dinding (m):', (idx.max() - idx.min()) * res)
    else:
        print(mode, n, 'tidak memotong dua dinding; coba nomor lain')
