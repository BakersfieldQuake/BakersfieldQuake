# Nana Plaza — Reference Coverage Gaps & Placeholder Log (`gaps.md`)

Per project ground-truth rules, **only geometry, signage, vehicles, props, and surface materials directly visible in the attached reference material (`nana-plaza-gallery-self-contained.html`, extracted to `ref_images/ref_001.jpg`..`ref_371.jpg`) are textured and detailed.** Every surface, interior room, or distant block face not visible in the reference photographs uses the plain neutral placeholder texture `np_placehld` (a flat warm-grey neutral block with a subtle 1 px border, logged in `texture_sources.md`) rather than invented detail.

---

## 1. Plain Placeholder Surfaces (`np_placehld`) in the Map

### A. Nana Plaza Interior Bar Rooms & Unphotographed Storefront Bays
- **Ground Floor (1F) Open-Front & Closed Bars**:
  - **Photographed room-by-room**: Only the **SE Corner Pool-Table Bar** (`ref_077.jpg`–`ref_084.jpg`, `ref_204.jpg`, 2017 pano `CIHM0ogKEICAgICu1L3d2wE`) has full interior photographs. It is built room-by-room (`s = 35.8..42.25 m, w = -16.4..-11.2 m`) with its cyan-cloth pool table, cue rack, cocktail tables, green-topped bar stools, mahogany bar counter, red cooler, live football TV screen, geometric orange/black/grey polygon feature wall, green-LED tray ceiling, and rear curtained service door. Even inside that bar, the **closed rear toilet/staff room behind `ref_083.jpg`'s curtained doorway** is unphotographed and kept sealed.
  - **Open-front courtyard beer bars** (*Stumble Inn*, *Morning Night*, *Kickoff*, *Luke's Tiki Bar*, *Temptations 1F*, *Lollipop*, *Twister BKK*, *Bangkok Bunnies*, *Witchcraft*, *Bunny / Erotica GF*, *Rainbow Bar*, *Playskool*, *London Calling*, *Sports Bus*): Only their courtyard/street frontages, fascia signs, counter fronts, stools, awnings, and shallow alcoves (such as *Lollipop*'s red lantern interior `ref_066`/`067` and *Rainbow Bar*'s blue-yellow tile `ref_075`) appear in the reference photos. Deep rear back-of-house kitchens/toilets behind those counters are unphotographed and use `np_placehld` rear walls.
  - **Closed 1F Go-Go Interiors** (*Obsession*): Exterior sign (`ref_297`) and entry threshold (`ref_296`) are built to photo ground truth, while its unphotographed interior seating/stage behind closed curtains is not guessed (`np_placehld` backing).
- **Second Floor (2F) Go-Go Bars**:
  - Walkway galleries, balustrades, `FL. 2` stairwell plaque (`ref_117.jpg`), escalators, stairwells, NE pop-art mural (`ref_187.jpg`), lift doors (`ref_130.jpg`), *Beauty Shop* (`ref_174.jpg`), *Mandarin & Mercury* (`ref_184.jpg`), *Charades* (`ref_179.jpg`), *Spanky's* (`ref_272.jpg`), *Angelwitch* (`ref_099.jpg`, `ref_165.jpg`), *DC-10* (`ref_101.jpg`), *Sexy Night* (`ref_107.jpg`), and *Casanova* (`ref_109.jpg`, `ref_115.jpg`) are photographed and built on the 2F perimeter gallery.
  - **2F South & East-South Unphotographed Individual Door Signs**: In `ref_018.jpg`, the 2F South wing (`s = 16.5..33.5 m`) shows terracotta wall tiling (`np_angel_tl`) from across the courtyard, while close-up individual door signs along 2F South (*Twister 2F*, *Temptations 2F*, *Rainbow 4*, *Stockings*) and `East-South 2F` / `South-East 2F` (`s = 33.5..41.2 m`) are not legibly photographed in the gallery; those unphotographed bays use `np_angel_tl` (where visible in `ref_018.jpg`) and `np_placehld` without inventing sign text.
  - **Closed 2F Go-Go Interiors**: Zero interior room photos exist inside the closed 2F go-go bar doors; they remain sealed behind their photographed facades.
- **Third Floor (3F) Go-Go Bars & Short-Time Hotel Units**:
  - **Sole Photographed Stage Interior — *Billboard Bangkok* (`ref_028.jpg`)**: Per explicit gallery instructions, *Billboard Bangkok* (`s = 23.0..35.0 m, w = 11.5..16.4 m` on 3F North) is the ONLY bar built with an interior stage room, featuring its white plush faux-fur stage (`np_bill_fur`), brushed chrome dance poles (`np_chrome`), overhead cyan/purple carousel LED ring (`np_led_cyan`), backlit bottle bar (`np_bill_bar`), and explicit interior `"Billboard BANGKOK"` (`np_billboard`) room label. Because `ref_028.jpg` looks NE across the stage and bottle bar without showing the West/East side partitions or entry wall back, those unphotographed interior side/entry walls use `np_placehld`.
  - **Other Photographed 3F Exterior Frontages**: *Erotica 3F* + `FL. 3` plaque at NW 3F (`ref_137.jpg`), *Geisha* on 3F East (`ref_020.jpg`), and *Butterflies* on 3F South (`ref_151.jpg`, `ref_230.jpg`) are built on their exact wings; their unphotographed interiors remain sealed.
  - **Three 3F Short-Time Hotel Units & Unphotographed 3F Bays** (`South-West 3F`, `North-East 3F`, `East-South 3F`, and `South-East 3F` noted in `Plan A ref_003.jpg` and prose): Zero close-up photographs of the short-time hotel doors or guest rooms exist in the gallery; their unphotographed exterior bay walls and interiors use `np_placehld`.

### B. Nana Plaza Exterior North, East & South Lot Perimeter Walls
- The **West street facade** on Sukhumvit Soi 4 (`ref_029`–`ref_040`, `ref_181`–`ref_208`) and the **2018 5-bay tensile roof canopy** (`ref_008`–`ref_017`, `ref_267`) are fully photographed and calibrated to `z20_sat_grid.jpg`.
- The tight **North party wall**, **East rear service wall** (`s = 46.2 m`, bordering *The Landmark Bangkok* podium), and **South party wall** (`w = -16.4 m`) are occluded from Street View at alley level and use `np_placehld`.

### C. Surrounding Soi 4 & Neighborhood Buildings (`Stage 3` & `Stage 4b`)
- **Street-facing Soi 4 & Sukhumvit Mouth Facades** (*Yellow Corner Shophouse*, *Morning Night*, *Stumble Inn*, *PRO EXCHANGE*, *Kickoff*, *Bunny*, *Hillary 2*, *King Indian*, *Grey Compound Wall*, *Absolute Tattoo*, *Pharmacy World* + `Rx` blade, *Nana Burger*, *Thai Cannabis Club*, *Nana Hotel* gate & ribbon-window wings, *Hooters*, *BLEZ*, *PTT Canopy*, *The Landmark*, *JW Marriott*) use rectified photo-derived textures from `ref_020`–`ref_370`.
- **Unphotographed Rear/Side Faces & Outer `z=18` Neighborhood Blocks** (*Krungthai Bank*, *Maison Hotel*, *Hotel Icon*, *Thai Obayashi*, *Saranjai Mansion*, *East Soi 4 Mid-South / Novotel Podium / South Blocks*, *West Soi 4 South Blocks*, and *Sukhumvit NE Soi 5–11 Blocks*) are extruded to their exact `z=20` / `z=19` / `z=18` aerial footprints and textured with `np_placehld` without guessing window grids or signage.
- **Truncated Historical `BIG DOGS` Crop (`ref_020.jpg` Left Edge)**: In the older evening view `ref_020.jpg`, the left two letters (`"BI"`) of the blue neon sign sit beyond the left edge of the camera frame (`"...G DOGS"`), while the primary Dec 2025 Soi 4 Street View sequence (`ref_029`–`ref_039`) shows no `BIG DOGS` sign on the *Stumble Inn* black-slat balcony; rather than fabricating unphotographed letters or placing a truncated `"G DOGS"` crop on the Dec 2025 streetscape, it is omitted and logged here.

---

## 2. Temporal Differences Across Reference Epochs (2017–2026)

1. **Courtyard Roof Canopy & Arch**: Built to the **2018–2026 permanent architectural state** (5-bay white steel-ribbed tensile canopy + black/silver `NANA PLAZA` entrance arch + Dec 2025 Soi 4 streetscape), while preserving all photographed interior courtyard bar signs, flag bunting, beer-garden island counters/parasols, and the SE Pool-Table Bar interior from the 360° panos.
2. **Transient Street Delivery Vehicles**: A green *Chang* delivery box truck appears momentarily inside the entrance throat in `ref_268.jpg` (2018) and a moving white pickup appears mid-lane in `ref_029.jpg`, whereas the primary Dec 2025 Street View sequence (`ref_031`–`ref_051`) shows clear East-lane sightlines into *Stumble Inn* and *Morning Night*; transient mid-lane obstructions were omitted so fixed Street View sightlines match ground truth.

---

## 3. Excluded, Unembedded, or Non-Ground-Truth Reference Items

1. **`ref_023.jpg` (`RedLightAsia hero image`) — EXCLUDED (Spurious / AI-Altered Image)**: Excluded per explicit gallery instructions and verified absent from `specs/textures.json` and `texture_sources.md`.
2. **`ref_025.jpg`–`ref_027.jpg` (Collage Overlays) & `ref_347.jpg`–`ref_354.jpg` (*Walking Team* Exterior Soi 4 Thumbnails)**: Collage text banners excluded from texture crops; exterior Soi 4 south thumbnails (`Hillary 2`, `King Indian`) applied strictly to their true exterior Soi 4 lots (`Y = -78..-50 m`), never inside Nana Plaza.
3. **Unembedded External IDs**: YouTube ID `qOBGEI0dnoY` and Google Maps photo ID `CIABIhCqJVzRv5BCRIpjcL_DtFCI` have no embedded media in the HTML; nothing was guessed from them.
4. **Prose "Three/Four-Storey" vs Photographed 3-Storey Complex**: Every floor plan (`ref_001`–`ref_006`), `FL. 2` / `FL. 3` plaque (`ref_117`, `ref_137`), and courtyard photo (`ref_018`–`ref_021`) confirms **3 public levels (`1F`, `2F`, `3F`) plus tensile roof canopy**.
