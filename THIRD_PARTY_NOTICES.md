# Third-party notices

FIND YOURSELF uses the Godot Engine 4.6.3 (MIT license). The native distribution includes the Godot runtime and its third-party libraries. See the bundled `third_party/godot-LICENSE.txt` and `third_party/godot-COPYRIGHT.txt` for the engine license and third-party license texts. Source: https://github.com/godotengine/godot/tree/4.6.3-stable .

Game geometry, UI, shaders/material choices, icon and synthesized sound waveforms are created in this project, except for the anatomical head topology described below. No external music, face photographs or commercial mall logos are included. This notice does not grant a license to the original game source or game assets.

Japanese text uses the bundled Noto Sans CJK JP Regular font, extracted without changing glyphs from the system Noto CJK collection. Noto CJK is distributed under the SIL Open Font License 1.1; copyright and full license text are in `third_party/noto-cjk-COPYRIGHT.txt`. The font is bundled with the game and does not require a font installation or network connection.

The development-only balance simulator uses NumPy 2.3.5 (BSD-3-Clause and bundled dependency notices provided with the installed package). NumPy is not distributed with the game and is not needed to play.

The civilian head topology is adapted from the MakeHuman hm08 base mesh, released as CC0 1.0 Universal in September 2020. Asset copyright holders at that release: Data Collection AB, Joel Palmius and Jonas Hauquier. Source revision: `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`, `makehuman/data/3dobjs/base.obj`, https://github.com/makehumancommunity/makehuman . The asset header and the project's asset license explicitly identify CC0; the full text is bundled in `third_party/makehuman-CC0.txt`. Only graphical mesh data is incorporated; the MakeHuman application's AGPL source code is not incorporated. The game adapts and fits the head, adds its own eyes/hair/clothing, materials, baked vertex occlusion and animation. Reproduction data, the pinned asset SHA256 and the original OBJ are in `tools/source_assets/` in the source distribution; they are not needed to play.

Skin and textile detail/normal maps are authored procedurally in this project (`tools/build_character_textures.py`), without face photographs or third-party texture images. Asset authoring optionally uses NumPy and Pillow; these Python libraries are not bundled with the game and are not required to play.

Limestone, oak and paint maps are authored from numeric fields in this project (`tools/build_interior_textures.py`), without source photographs or third-party texture images. The static floor-contact mask is generated from the project's collider geometry. Optional NumPy/Pillow authoring tools are not bundled with or required by the game.

Retail prop meshes, fictional posters, price cards and display artwork are authored in this project (`scripts/retail_models.gd`, `tools/build_retail_art.py`) from numeric geometry, original graphic shapes and the bundled Noto font. No photographs, external product models or commercial logos are incorporated. Optional Pillow authoring is not needed to play.
