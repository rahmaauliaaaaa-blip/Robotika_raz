import sys
import numpy as np
from PIL import Image

# Membaca gambar dari argumen command-line
img = np.array(Image.open(sys.argv[1]))

# Mencetak header kolom (angka 0-9 berulang)
print('    ' + ''.join(str(c % 10) for c in range(img.shape[1])))

# Mencetak setiap baris piksel menjadi karakter ASCII
for i, row in enumerate(img):
    print(f'{i:3d} ' + ''.join('#' if v < 100 else ('.' if v > 240 else ' ') for v in row))
