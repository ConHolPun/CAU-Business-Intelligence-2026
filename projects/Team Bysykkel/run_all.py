"""Run the whole data step in order: download trips, download weather, check, build table."""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

for step in ["01_download_trips.py", "02_download_weather.py", "03_check_data.py", "04_build_table.py"]:
    print(f"\n=== {step} ===")
    runpy.run_path(str(SRC / step), run_name="__main__")
