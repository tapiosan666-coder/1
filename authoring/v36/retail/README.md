# v36 retail authoring

The shipped Godot project reads calibrated coordinates in res://source/v36. The following scripts are offline authoring tools. Production gameplay has no dependency on Python, Blender or external downloads.

- art.py paints the original department print sheet. model.py and department_fixtures.py build 23 trades' original retail fittings, along with the physical plinths, uprights and worktops in studio-solids.json. dining_rooms.py writes SUVEL MUSE and MIREVA LINE furniture plus their separate physical shapes.
- bake.gd converts each intermediate model directory into shared Godot ArrayMesh resources. Run Godot in the project directory with `--headless --script res://authoring/v36/retail/bake.gd -- RAW_DIRECTORY` after the project has imported its textures.
- lay_out.py reads the legacy stores, sales/service routes, existing fixture outlines and v32 fixture replacement data. It produces uncalibrated candidates. thresholds.py then checks entry-floor geometries and paints the 15 brand sheets. These tools use Python, Pillow, Shapely 2 and the zstd CLI.
- Run qa_sites.gd on the v35 project to survey freestanding candidates. For the second pass, use threshold and in-place replacement candidates so the test can exclude each original host collision body. The two arguments are candidate JSON and output JSON. Keep candidate files outside the source tree while resurveying.
- apply_floor_survey.py takes both survey results plus the path for a decision log and writes accepted records and grounded coordinates. The checked-in files have already passed through this step.
- qa_dining_rooms.gd accepts the full path to dining-programs.json and output JSON. Run the v35 site once to test clearances. On v36 add `with-install` to check residents, walk the two rooms with the player controller, and sample the access lanes.

- refit_envelopes.py RAW_DIRECTORY REPORT_JSON --fit-refits measures the final mesh vertices against the previous fitting envelopes and vertically fits each replacement to the available height. Remove the optional flag for a read-only check. Requires NumPy.
