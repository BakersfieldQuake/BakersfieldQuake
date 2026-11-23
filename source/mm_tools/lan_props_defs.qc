/*
================
EXPLODABLE 3D LAN PARTY PROPS - definitions (Combat+)

Populates Unit 130A B-LAN Hall, 120A room, and ORCOM CONNECT LAN PARTY Hall with
destructible, chain-exploding 3D hardware & furniture:
  - misc_lan_monitor : 4 unique 3D CRT monitors (cnt 1..4) playing animated
                       Quake 3 Arena (skins 0,3), Counter-Strike 1.5 (skins 1,4),
                       and Windows 98 / Winamp / GameSpy / BSOD (skins 2,5)
  - misc_lan_pc      : 4 unique 3D PC towers (cnt 1..4: Beige ATX, Modded UV Chieftec
                       w/ top carry handle & neon, Bondi 2-tone, Brushed Silver Full-Tower)
  - misc_lan_chair   : 4 unique 3D LAN chairs (cnt 1..4: Burgundy Banquet, Black Exec
                       Swivel, Padded Steel Folding, Cobalt Ergonomic Task)
  - misc_lan_table   : 4 unique 3D LAN tables (cnt 1..4 8-ft tables + cnt 5 compact desk)

Cheat test impulses (sv_cheats 1):
  - impulse 95 : Spawn full 4x4 showcase row of all monitors, PCs, chairs, and tables
  - impulse 96 : Detonate nearest LAN prop within 450 units
================
*/

float	LAN_KIND_MONITOR	= 1;
float	LAN_KIND_PC			= 2;
float	LAN_KIND_CHAIR		= 3;
float	LAN_KIND_TABLE		= 4;
float	LAN_KIND_QUAKEDESK	= 5;

var float	autocvar_lan_prop_respawn	= 45;	// > 0: seconds before destroyed map LAN prop respawns in DM (0 = stay destroyed)

float	lan_precached;
float	lan_debris_precached;
float	lan_inflicting;
float	lan_debris_count;

.float	lan_kind;			// LAN_KIND_* (0 on non-LAN entities)
.float	lan_variant;		// 1..4 (or 5 for compact desk)
.float	lan_init_skin;		// initial CRT screen skin (0..5)
.float	lan_dead;			// TRUE while blown up & waiting to respawn
.float	lan_temp;			// TRUE when spawned via impulse 95
.vector	lan_spawn_org;		// original map spawn origin (restored on respawn)
.vector	lan_spawn_ang;		// original map spawn angles
.entity	lan_attacker;		// attacker credited with chain blast

void() LanProps_Precache;
void() LanProps_Impulse;
void() misc_lan_quakedesk;
