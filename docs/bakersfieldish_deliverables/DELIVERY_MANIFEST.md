# Bakersfield-ish Final Deliverables Manifest

- **Deliverables Folder:** `G:\Quake\Combat\BakersfieldQuake\docs\bakersfieldish_deliverables`
- **Total Files Staged:** 13 (159.09 MB total)
- **Telegram Delivery:** **DELIVERED** — Delivered 13/13 artifacts natively to Telegram chat -4993867752 via vps-curl.

| # | Deliverable | File | Size (MB) | Details | Telegram | SHA-256 (first 12) |
|---:|---|---|---:|---|---|---|
| 1 | Fox Theater — 3-Stage Destruction & Slow Rebuild | `fox_destruct.mp4` | 22.10 | 1280x720, 55.48s, streams=2 (h264+aac) | msg #103 | `6EFAE06000B5` |
| 2 | Padre Hotel — 3-Stage Controlled Demolition | `padre_destruct.mp4` | 17.71 | 1280x720, 39.48s, streams=2 (h264+aac) | msg #104 | `017EB6563D20` |
| 3 | The Bakersfield Sign — 3-Stage Break & Topple | `sign_destruct.mp4` | 9.77 | 1280x720, 21.98s, streams=2 (h264+aac) | msg #105 | `23DD076B3AE9` |
| 4 | Shatterable Storefront Glass | `glass_destruct.mp4` | 5.77 | 1280x720, 12.38s, streams=2 (h264+aac) | msg #106 | `F2A37425DD50` |
| 5 | 360° Orbit — Fox Theater (Intact) | `fox_orbit_intact.mp4` | 7.42 | 1280x720, 15.58s, streams=2 (h264+aac) | msg #107 | `67A99ED4C98D` |
| 6 | 360° Orbit — Fox Theater (Collapsed) | `fox_orbit_collapsed.mp4` | 8.51 | 1280x720, 16.38s, streams=2 (h264+aac) | msg #108 | `91A1B7F642A8` |
| 7 | 360° Orbit — Padre Hotel (Intact) | `padre_orbit_intact.mp4` | 11.19 | 1280x720, 15.58s, streams=2 (h264+aac) | msg #109 | `D306ABF71382` |
| 8 | 360° Orbit — Padre Hotel (Collapsed) | `padre_orbit_collapsed.mp4` | 10.46 | 1280x720, 16.45s, streams=2 (h264+aac) | msg #110 | `1A6617A02CEC` |
| 9 | 360° Orbit — Bakersfield Sign (Intact) | `sign_orbit_intact.mp4` | 9.79 | 1280x720, 15.55s, streams=2 (h264+aac) | msg #111 | `C805AB5322A5` |
| 10 | 360° Orbit — Bakersfield Sign (Collapsed) | `sign_orbit_collapsed.mp4` | 10.35 | 1280x720, 16.38s, streams=2 (h264+aac) | msg #112 | `1D573C0B134E` |
| 11 | Full Downtown Bakersfield-ish Fly-Through | `bakersfieldish_flythrough.mp4` | 30.78 | 1280x720, 45.95s, streams=2 (h264+aac) | msg #113 | `5B810C2AC960` |
| 12 | Offline Interactive 3D WebGL2 Map Viewer | `bakersfieldish_interactive.html` | 13.54 | offline_clean=True, external_refs=0 | msg #114 | `0901C085D608` |
| 13 | Offline Showcase & Engineering Changelog Page | `bakersfieldish_showcase.html` | 1.72 | offline_clean=True, external_refs=0 | msg #115 | `0FDAD9F3F57B` |

## Re-Send to Telegram Anytime
```powershell
$env:TG_BOT_TOKEN = "<your-bot-token>"
python source/mm_tools/deliver_bakersfieldish_telegram.py --transport vps-curl --deliverables-dir "G:\Quake\Combat\BakersfieldQuake\docs\bakersfieldish_deliverables"
```
