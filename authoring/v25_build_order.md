# v25 authoring order (not needed to play)

Requires Blender4.3/Python/Pillow/numpy/Shapely/zstandard. All runtime assets already included. Keep inherited assets immutable; new outputs only assets/v25.

Blender: v25_apparel.py, v25_window_outfits.py, v25_specialists.py, v25_finish_modules.py, v25_commons.py. Each imports v25_blender_common.py (output v25).
Python: v25_layout.py (always resets from retained source/v24, do not use --pilot for full build), v25_specialist_layout.py (not repeatable without resetting base), v25_enrich.py (guards duplicate application), v25_editorial.py, v25_cafe_gallery.py. New raw retail-plan.json must be compressed to FYJZ only after the read-only index and proofs have been rebuilt.

Current fixture data and source/v25 validation artifacts are authoritative for this delivery. Do not run older v24 authoring scripts: those intentionally target immutable assets/v24. No download or modelling operation is required for F5.
