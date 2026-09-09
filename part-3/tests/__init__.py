import sys
import os

# Pastikan folder part-3 selalu berada di sys.path agar test module dapat mengimpor 'src' dan 'web_app'
# baik dijalankan dari dalam folder part-3 maupun dari root repositori monorepo.
PART3_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PART3_DIR not in sys.path:
    sys.path.insert(0, PART3_DIR)
