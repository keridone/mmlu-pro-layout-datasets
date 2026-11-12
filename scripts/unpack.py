"""Create readable JSONL copies; keep canonical compressed files unchanged."""
import argparse
import gzip
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tier', choices=['small', 'medium', 'large'])
    args = parser.parse_args()
    destination = ROOT / 'unpacked' / args.tier
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / args.tier).glob('*.jsonl.gz')):
        target = destination / source.stem
        with gzip.open(source, 'rb') as inp, target.open('xb') as out:
            shutil.copyfileobj(inp, out)
        print(target.relative_to(ROOT))


if __name__ == '__main__':
    main()
