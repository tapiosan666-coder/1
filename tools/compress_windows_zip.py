#!/usr/bin/env python3
"""Optional release-tool dependency: zopfli==0.4.3; ordinary ZIP Deflate output."""
from pathlib import Path
import hashlib
import json
import time
import zlib
import zopfli.zlib

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "builds/FIND_YOURSELF.exe"
data = source.read_bytes()
start = time.monotonic()
print(f"Optimizing standard Deflate for {source.name}: {len(data):,} bytes", flush=True)
compressed = zopfli.zlib.compress(data, numiterations=5)[2:-4]
assert zlib.decompress(compressed, -15) == data
(ROOT / "builds/windows-exe.deflate").write_bytes(compressed)
evidence = {"source_sha256": hashlib.sha256(data).hexdigest(), "compressed_sha256": hashlib.sha256(compressed).hexdigest(), "method": "standard ZIP Deflate (Zopfli optimal encoding)", "iterations": 5, "compressed_bytes": len(compressed), "uncompressed_bytes": len(data), "seconds": time.monotonic() - start}
(ROOT / "builds/windows-exe-compression.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(f"Verified identical executable bytes; Deflate stream: {len(compressed):,} bytes", flush=True)
