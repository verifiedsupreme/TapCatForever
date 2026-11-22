# Cosmetic sets: one file per set

Each themed cosmetic set (Molten Core, and the later dungeons) is one Python file here. It draws its
own pieces, builds its own textures and writes its own Lua data, so several artists can work on
different sets at the same time without the global art build (`tools/build_vector_art.py`) and
without editing shared files, except one line in the TOC when a new set ships.

Reference set: `molten_core.py` (Molten Core, animated fire).

## What a set is in the game
- 6 pieces, all cosmetic only: a statement helm or crown (`head`), shoulders (`shoulder`), chest
  (`chest`), cape (`back`, side drapes), weapon (`main`) and an aura (`effect`).
- Each piece is guaranteed from one Adventure boss of the set's zone until the player owns it
  (`TCF.BOSS_COSMETICS[boss] = { item ids }`, which Adventure.lua reads). One piece per boss.
- The Compendium and the tooltip say where each piece comes from and show the set's progress:
  "Molten Core set (2/6), cosmetic only: crown from Ragnaros, shoulders from Golemagg the Incinerator, ...".
- Pieces are animated with the layer system in `CatAnim.lua` (flipbooks, pulses, scrolling
  textures clipped inside a shape, particles, glints, colour cycling).

## Add a set in 6 steps
1. Copy `molten_core.py` to `tools/sets/<set>.py` (lowercase, e.g. `scholomance.py`).
2. Fill in `SET`:
   - `key`: short and unique (`scholo`). Item ids are `set_<key>_<piece>`, art names `<key>_<piece>`
     (textures become `Art/v/k_<art>_<layer>.tga`), so nothing collides with another set.
   - `name` ("Scholomance"), `zone` (the Adventure tier key from `TCF.TIERS` in GearData.lua, e.g.
     `scholo`), `lua` (the Lua file name, `Scholomance` gives `Sets/Scholomance.lua`), `file`
     (this file's name without `.py`), `about` (one line), `preview_fur` or `preview_skin`.
   - `pieces`: one dict per piece: `id`, `slot`, `kind` (head, shoulder, chest, back, weapon,
     effect), `art`, `name` (plain English, no exclamation marks), `rarity` (4 Epic, 5 Legendary),
     `icon` (a WoW icon name for the Appearance tab), `boss` (exact Adventure boss name), `word`
     (what the Compendium calls it: crown, shoulders, chest, cape, sword, aura...), `svg` (the
     drawing), `layers` (extra drawings for the animation: flipbook frames, glows, masks) and `anim`
     (the animated layers, see below). An `effect` piece has no `svg`; give it `glow` (an r, g, b
     colour for the old pixel cat's aura texture) and `fx` (`{"layer": "back", "anim": "flicker"}`).
3. Draw. Everything is SVG in the 256-unit cosmetics canvas of `tools/vector_items.py`, in the
   flat sticker style with thick dark outlines (`INK`): use `P`, `LN`, `CI`, `EL`, `RC`, `GEM`, `GLOW`
   from `tools/setlib.py` (which re-exports them). Where things sit:
   - helm: head space, wrap it in `HEAD(...)`. The head is about x 45-211, y 28-168 in head space
     (ears at x 58 and 198, y 28); a crown band sits around y 60-90.
   - shoulders: body space, draw the left pauldron around `SH_C` (64, 131) and wrap in `BOTH(...)`
     for both shoulders (mirrored). The head covers their inner part.
   - chest: body space, inside `BODY_OUT`.
   - cape: the side drapes `DRAPE_OUT` / `DRAPE_IN` (they hang down both sides and tuck behind the body);
     `DRAPE_EDGE` and `qpts` give points along the outer edges for flames, fur and studs.
   - weapon: right paw, wrap in `RHAND(...)`; grip at 0, blade up (negative y), like `draw_mace`.
   - main drawings get the cel shading automatically; `layers` don't unless given as `(svg, True)`.
4. Animate. Layers in `anim` (CatAnim.lua has the full list):
   - `{"kind": "flip", "keys": [K(art, "fl1"), ...], "fps": 9}`: a flipbook of `layers` drawings
     (flickering flames). At most 4 frames.
   - `{"kind": "pulse", "key": K(art, "veins"), "a": [0.2, 1.0], "speed": 3, "blend": "ADD"}`: a glow that
     breathes; or `"sprite": "a_catglow", "rect": [0, 0, 512, 512]` for a glow behind the whole cat.
   - `{"kind": "scroll", "sprite": "a_lava", "mask": K(art, "seam"), "scale": 150, "vx": 6, "vy": -26}`: a tile
     drifting inside a shape (the mask is a white drawing in `layers`). Tiles: a_stars, a_nebula,
     a_lava, a_firetile, a_frost, a_swirl, a_shine.
   - `{"kind": "particles", "sprite": "a_ember", "n": 6, "box": [x0, y0, x1, y1], "vy": [-80, -45], ...}`: rising
     or falling sprites (box in the 512 canvas). Sprites: a_ember, a_spark, a_flame, a_wisp, a_glow, and
     the ink-outlined t_leaf, t_snow, t_bubble, t_coin, t_star, t_sparkle, t_flame, t_skull.
   - `{"kind": "glint", "spots": [[x0, y0, x1, y1]], ...}`: sparkles popping up in place.
   - `"at": "front"` or `"behind"` draws a layer in front of everything or behind the whole cat.
   Keep it cheap: at most 6 layers a piece, 8 particles a layer, 4 flipbook frames (the art test checks).
5. Preview (does not touch Art/v or the addon):

       python3 tools/set_preview.py tools/sets/<set>.py <out_dir>

   writes `sets_<key>.gif` (animated, paws tapping), `sets_<key>.png` and `sets_<key>_pieces.png`
   (each piece alone, which boss drops it, and the full set). It uses the real CatVector and
   CatAnim code (`tools/catrender.py`), so what you see is what the game draws.
6. Ship:

       python3 tools/sets/<set>.py

   writes only this set's files: `Art/v/k_<art>_*.tga`, `Art/<art>.tga` (a small texture for the old
   pixel cat) and `Sets/<Lua>.lua`. Add one line `Sets\<Lua>.lua` to `TapCatForever.toc` after the
   other `Sets\` lines, run `python3 tools/test_harness.py` (the art section checks every set: zone,
   bosses, one piece per boss, drawings, animation budget) and list the set in your notes.
   The global build runs every `tools/sets/*.py` again at its end, so sets survive a full rebuild.

## Later dungeons in Adventure and their bosses (GearData.lua, TCF.TIERS)
| Zone key | Dungeon | Bosses (the last one is the final boss) |
|---|---|---|
| sm | Scarlet Monastery | Azshir the Sleepless, Fallen Champion, Arcanist Doan, High Inquisitor Fairbanks, Herod, High Inquisitor Whitemane |
| rfd | Razorfen Downs | Mordresh Fire Eye, Lady Falther'ess, Glutton, Ragglesnout, Tuten'kash, Amnennar the Coldbringer |
| uld | Uldaman | Revelosh, Ironaya, Ancient Stone Keeper, Galgann Firehammer, Grimlok, Archaedas |
| zf | Zul'Farrak | Witch Doctor Zum'rah, Dustwraith, Gahz'rilla, Antu'sul, Shadowpriest Sezz'ziz, Chief Ukorz Sandscalp |
| mara | Maraudon | Lord Vyletongue, Razorlash, Meshlok the Harvester, Celebras the Cursed, Landslide, Princess Theradras |
| st | Sunken Temple | Atal'alarion, Spawn of Hakkar, Ogom the Wretched, Jammal'an the Prophet, Shade of Hakkar, Shade of Eranikus |
| brd | Blackrock Depths | Anub'shiah, Lord Incendius, Bael'Gar, General Angerforge, Ambassador Flamelash, Emperor Dagran Thaurissan |
| brs | Blackrock Spire (one zone, no Lower/Upper split) | War Master Voone, Overlord Wyrmthalak, The Beast, Warchief Rend Blackhand, Lord Valthalak, General Drakkisath |
| dim | Dire Maul | Hydrospawn, Alzzin the Wildshaper, Mizzle the Crafty, Prince Tortheldrin, King Gordok, Immol'thar |
| scholo | Scholomance | Kirtonos the Herald, Rattlegore, Jandice Barov, Ras Frostwhisper, Kormok, Darkmaster Gandling |
| strat | Stratholme | Baroness Anastari, Ramstein the Gorger, Nerub'enkan, Cannon Master Willey, Maleki the Pallid, Baron Rivendare |
| mc | Molten Core (raid, done) | Lucifron, Magmadar, Baron Geddon, Garr, Golemagg the Incinerator, Ragnaros |

Every dungeon has exactly 6 bosses, one per piece. Majordomo Executus is not in Adventure's Molten
Core, so Lucifron drops the hammer.
