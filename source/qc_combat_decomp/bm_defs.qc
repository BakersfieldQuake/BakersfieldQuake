#ifndef COMBATPLUS
#define COMBATPLUS
#endif
/*
================
BAKERSFIELD LAN RULES - definitions (Combat+ only)

bm_reload.qc	magazines and reloading for every gun
bm_match.qc		spawn protection, self-damage, regen tuning, score rules, map playlist, HUD stats
underdog.qc		frag-gap catch-up: the leader lights up, last place gets boosts

Compiled right after funguns_defs.qc so everything below can call into the later files.
All tuning is cvars (autocvar_bm_*); the defaults here are what you get without a cfg.
================
*/

// ---------------------------------------------------------------- tuning (cvars)
var float	autocvar_bm_reload			= 1;		// 0 = stock Combat+ ammo
var float	autocvar_bm_mag_scale		= 1;		// magazine sizes x this
var float	autocvar_bm_reload_scale	= 1;		// reload times x this
var float	autocvar_bm_holster			= 0.25;		// holstered guns refill at this fraction of the held reload speed
var float	autocvar_bm_idle_reload		= 2.5;		// seconds without firing before a part-empty gun tops itself up

var float	autocvar_bm_selfdamage		= 0.6;		// self-inflicted damage x this (on top of the stock 0.5 splash halving)
var float	autocvar_bm_rocketself		= 0.4;		// your own rockets' self-damage x this as well (0.4 = 60% less)
var float	autocvar_bm_falldamage		= 0;		// 1 = stock fall damage
var float	autocvar_bm_spawnnear		= 1200;		// spawn near the action: the free spawn closest to a living rival but not nearer than this and out of sight (0 = stock round robin)
var float	autocvar_bm_fg_lock			= 0;		// seconds after a fun gun fires before a DIFFERENT fun gun can fire (0 = off)
var float	autocvar_bm_preload			= 0;		// 0 = off, 1 = preload the Wheelman Cannon sprites (~315 MB) with the map instead of on the first charge
var float	autocvar_bm_nopredict		= 1;		// 1 = no client prediction while the server drives your speed (jetpack, shock, milk): less snap-back online
var float	autocvar_bm_spawnprot		= 3;		// seconds of spawn protection (firing ends it)
var float	autocvar_bm_spawnpause		= 0.5;		// seconds after a spawn with protection before you can fire
var float	autocvar_bm_regen_delay		= 5;		// seconds after the last hit before health comes back
var float	autocvar_bm_regen_rate		= 10;		// health per second
var float	autocvar_bm_armor_regen		= 1;		// 0 = armor never comes back
var float	autocvar_bm_armor_rate		= 1;		// armor per second, slow; up to 4x that when you are well behind; none in first place
var float	autocvar_bm_intermission	= 10;		// deathmatch intermission seconds before the next map loads by itself
var float	autocvar_bm_botfill			= 0;		// keep adding FrikBots until there are this many players
var float	autocvar_bm_botfill_empty	= 0;		// 1 = fill even with nobody connected (testing)
var float	autocvar_bm_vote			= 1;		// 1 = players can vote on the map ("vote map fox" in chat, then vote yes / vote no)
var float	autocvar_bm_npcs			= 0;		// 1 = maps get their NPCs (street crowd, bar crowd, bosses, the Fox repair crew); 0 = none (2026-11-26)
var float	autocvar_bm_traffic			= 0;		// 1 = AI cars and the spruce school bus drive around; 0 = clear streets (2026-11-26)
var float	autocvar_bm_kartspawn		= 0.3;		// share of human spawns that start in a go-kart, on spawns with room to drive (0 = off)

// Map-placed NPCs and traffic: off unless bm_npcs / bm_traffic. Map entities spawn before the first server frame
// (framecount 0); the cheat summon impulses call the same spawn functions later, so those still work.
float() BM_NoMapNPC = { return (!autocvar_bm_npcs && !framecount); };
float() BM_NoMapTraffic = { return (!autocvar_bm_traffic && !framecount); };
var float	autocvar_bm_votetime		= 30;		// seconds a vote stays open
var float	autocvar_bm_votecool		= 60;		// seconds before the same player can call another vote
var float	autocvar_bm_debug			= 0;		// 1 = print every player's magazine / reload / frag-gap state every 2 s
var float	autocvar_bm_warmup			= 0;		// set by warmup.cfg: shows the "press F1" hint

var float	autocvar_bm_handicap		= 1;		// 0 = no leader glow / underdog boosts
var float	autocvar_bm_bounty			= 1;		// killing someone 4+ frags ahead of the pack is worth +1
var float	autocvar_bm_newbie			= 0.3;		// chance that killing the player in last place plays funny/newbie.wav (0 = never)
var float	autocvar_bm_giantslayer		= 0;		// max extra damage an underdog deals to players ranked above them
var float	autocvar_bm_ud_resist		= 0;		// max cut in the damage an underdog takes from players ranked above them (0 = reliable TTK)
var float	autocvar_bm_ud_span			= 8;		// frags behind the leader for the full gap signal in a 1v1 (tighter with more players)
var float	autocvar_bm_ud_streak		= 6;		// deaths in a row for Last Stand with 3-5 players (+1 in a 1v1, -1 at 6+, -2 at 10+)
var float	autocvar_bm_ud_botcap		= 0.6;		// bots' boost stops here and they never get Last Stand
var float	autocvar_bm_spawnarmor		= 100;		// green armor every deathmatch spawn (0 = none, like stock Quake)
var float	autocvar_bm_ud_yellow		= 0.3;		// boost for spawning with yellow armor (150)
var float	autocvar_bm_ud_red			= 0.75;		// boost for spawning with red armor (capped at 150 yellow stack by default)

var float	autocvar_bm_fun				= 1;		// 0 = no kill announcer (bm_fun.qc): no first blood, sprees, revenge, clips
var float	autocvar_bm_fun_gap			= 10;		// seconds between two global announcer voice clips
var float	autocvar_bm_scroll_fun		= 1;		// 1 = mouse-wheel cycles through ALL guns (including Rob Dob, Jar o' Green Guys, Pickle Surprise, NetSend PC, Wheelman Cannon, M4/Garand); 0 = skip FG1..FG6
var float	autocvar_bm_fun_multi		= 3;		// kills this close together are a DOUBLE / TRIPLE / MULTI KILL
var float	autocvar_bm_fun_cheer		= 1;		// chance the room cheers when the player in last place gets a kill
var float	autocvar_bm_fun_larry		= 0.7;		// chance an announcer clip is the Larry McCart one instead of the stock clip (0 = never)
var float	autocvar_bm_dm_startgun		= 1;		// DM starting weapon: 1 = rotate RL / M4 / Garand, 2 = RL, 3 = M4, 5 = Garand, 0 = MegaMan
var float	autocvar_bm_bot_easy		= 1;		// 1 = easy, fun, aggressive bots with human aim spread (0 = full FrikBot aim)
var float	autocvar_bm_bot_dmg			= 0.65;		// damage multiplier dealt by bots to players (keeps 5-10 aggressive bots fun & forgiving)
var float	autocvar_bm_bot_tags		= 1;		// 1 = show floating [BOT] nameplates over visible bots
var float	autocvar_bm_public_server	= 0;		// 1 = this is the public dedicated server (server_vps.cfg): bot cap, free-slot reserve, cooldown and idle cleanup apply (0 = local/LAN games stay unrestricted)
var float	autocvar_bm_bots_allowed	= 1;		// public server: 1 = any player can add/kick bots (F1/F2, impulse 100-102) with no sv_cheats; 0 = off
var float	autocvar_bm_bot_max			= 15;		// most bots that can be on the server at once
var float	autocvar_bm_bot_reserve		= 1;		// free slots bots must leave open so a human can always join (bots step aside if humans fill them)
var float	autocvar_bm_bot_cooldown	= 0.7;		// seconds between bot adds (stops F1 held down)
var float	autocvar_bm_bot_idle		= 45;		// dedicated servers: seconds with no human connected before the bots are cleared (0 = never)
var float	autocvar_bm_bot_jpfuel		= 2.2;		// starting jetpack fuel (seconds) for bots so they fly around downtown buildings

// ---------------------------------------------------------------- magazines
// slot numbers (bm_reload.qc), 0 = no magazine (axe, banana)
float	BM_SG		= 1;
float	BM_SSG		= 2;
float	BM_NG		= 3;
float	BM_SNG		= 4;
float	BM_GL		= 5;
float	BM_RL		= 6;
float	BM_LG		= 7;
float	BM_LASER	= 8;
float	BM_MM		= 9;
float	BM_FG1		= 10;
float	BM_FG2		= 11;
float	BM_FG3		= 12;
float	BM_FG4		= 13;
float	BM_FG5		= 14;
float	BM_FG6		= 15;
float	BM_FG7		= 16;	float	BM_FG8		= 17;	float	BM_FG9		= 18;	float	BM_FG10		= 19;	// M4 / Kyle / Garand / Cyrax
float	BM_SLOTS	= 19;

float	BM_EF_NODEPTHTEST	= 8192;	// DarkPlaces: draw through walls (and skip the server's visibility culling)

float	BM_RELOAD_IMPULSE	= 41;		// R (30 is the flashlight)

.float	bm_m1, bm_m2, bm_m3, bm_m4, bm_m5, bm_m6, bm_m7, bm_m8;		// stock gun magazines (ammo units)
.float	bm_a1, bm_a2, bm_a3, bm_a4, bm_a5, bm_a6, bm_a7, bm_a8, bm_a9, bm_a10, bm_a11, bm_a12, bm_a13, bm_a14, bm_a15, bm_a16, bm_a17, bm_a18, bm_a19;	// holstered refill, fractional
.float	bm_ns_n, bm_ns_t;	// bots: NetSend PC count and when it was last counted (BM_BotNSCount)
.float	bm_init;			// magazines have been filled since connecting
.float	bm_slot;			// slot whose magazine is in the ammo_* field right now
.float	bm_shown_s, bm_shown_n, bm_shown_r, bm_shown_c;		// what we last wrote to ammo_*, to spot pickups
.float	bm_rl_slot;			// slot being reloaded (0 = none)
.float	bm_rl_start;		// reload started
.float	bm_rl_end;			// reload finishes
.float	bm_rl_quiet;		// 1 = background idle top-up (keep viewmodel visible & silent)
.float	bm_full_refill;		// 1 = backpack/supply-pack touch refills fun-gun superweapons too
.float	bm_vm_hidden;		// the gun is out of sight while it reloads: the slot being reloaded (0 = in view)
.string	bm_vm_str;			// the held gun's model, put back when the reload is over (a strzone'd copy)
.float	bm_lastshot;		// last time the held magazine went down
.float	bm_holster_dt;		// time gathered for the holstered-gun refill, which runs 10 times a second (BM_Frame)
.float	bm_lastframe;		// last BM_Frame time (holster refill dt)
.float	bm_ssgburst;		// QC super shotgun: 15 = one barrel left (was a global shared by everyone)

// HUD stats (addstat, read by csprogs.dat)
.float	bm_st_mag;			// held magazine (rounds)
.float	bm_st_magmax;		// held magazine size (rounds)
.float	bm_st_reload;		// reload progress 1..100, 0 = not reloading
.float	bm_st_slot;			// active weapon slot (BM_*, 16 = M4)
.float	bm_st_prot;			// spawn protection left, tenths of a second
.float	bm_st_heat;			// your lead over the pack (leader effects)
.float	bm_st_boost;		// your underdog boost 0..100
.float	bm_st_regen;		// 1 while health is regenerating
.float	bm_st_warmup;		// 1 in the local warmup game
.float	bm_st_lheat;		// the current leader's heat
.float	bm_st_lx, bm_st_ly, bm_st_lz;	// the leader's position, when they show through walls (tier 3+)
.float	bm_st_lshow;		// 1 = draw the HUD marker at bm_st_lx/ly/lz
.string	bm_st_leader;		// the current leader's name ("" = nobody far enough ahead)
.float	bm_st_botmask;		// bitmask of live visible bot client slots 0..15 (stat 76, csqc/bm_hud.qc)
.float	bm_st_playermask;	// bitmask of live visible human client slots 0..15 (stat 80, csqc/bm_hud.qc)
.float	bm_st_botcnt;		// active bot count (stat 77, csqc/bm_hud.qc)
.float	bm_st_toymask;		// bitmask of ready fun-gun superweapons & Winged John (stat 78, csqc/bm_hud.qc)
.float	bm_st_toycd;		// Winged John cooldown seconds remaining (stat 79, csqc/bm_hud.qc)
.float	fd_st_mode;			// Rob Dob X-Ray HUD: 0=off, 1=cruise, 2=dash, 3=post-blast fade (stat 81)
.float	fd_st_timer;		// Rob Dob flight seconds*10 remaining, 999=unlimited (stat 82)
.float	fd_st_speed;		// Rob Dob drone velocity u/s (stat 83)
.float	fd_st_arm;			// Rob Dob dash armed flag (stat 84)
.float	fd_st_seq;			// Rob Dob hacking terminal sequence 1..14 (stat 85)
.float	gk_st_mode;			// Go-Kart rocket HUD: 0=off, 1=charging, 2=armed, 3=low nitro, 4=reloading (stat 109)
.float	gk_st_prog;			// Go-Kart rocket HUD: 0..100 charge/nitro/cooldown % (stat 110)
.float	gk_st_nitro;		// Go-Kart rocket HUD: 0..100 current nitro % (stat 111)
.float	gk_st_lock;			// Go-Kart rocket HUD: 1 = locked on a player (stat 120)
.float	gk_st_tx;			// Go-Kart rocket HUD: locked target world X (stat 121)
.float	gk_st_ty;			// ...Y (stat 122)
.float	gk_st_tz;			// ...Z (stat 123)
.float	cy_st_mode;			// Cyrax Net HUD: 0=off, 1=charging, 2=pulling, 3=holding, 4=trapped (stat 128)
.float	cy_st_prog;			// Cyrax Net HUD: 0..100 charge % or 0..300 remaining tenths (stat 129)
.float	cy_st_flash;		// Cyrax Net HUD: incremented on each capture for green edge flash (stat 130)
.float	cy_st_kind;			// Cyrax Net HUD: 0=player/bot, 1=Winged John Bird, 2=Milky Grenade (stat 131)
.float	cy_st_dist;			// Cyrax Net HUD: distance in units to captured target (stat 132)

// ---------------------------------------------------------------- survivability / match
.float	bm_prot_t;			// spawn protection until
.entity	bm_aura;			// the glowing bubble round a protected player (bm_match.qc)
.float	bm_regen_on;		// regenerating right now (for the HUD)
float	bm_blocked;			// T_Damage: the hit was absorbed by spawn protection (knockback still applies)
float	bm_kb;				// T_Damage: damage used for knockback (before self-damage scaling)
float	bm_inter_t;			// when the intermission auto-advances
float	bm_botfill_t;
float	bm_debug_t;			// next bm_debug printout		// next bot-fill check
string	bm_nextmap;			// playlist pick, strzoned

// ---------------------------------------------------------------- underdog / leader (underdog.qc)
.float	ud_heat;			// frags - average of everyone else
.float	ud_deficit;			// top score - frags
.float	ud_lead;			// 1 = in first place (the most frags, and somebody has fewer): armor stops regenerating
.float	bm_ar_frac;			// armor regeneration carried between frames
.float	ud_boost;			// 0..1 underdog strength: losing streak, K/D and frags behind (Underdog_Update)
.float	ud_kills;			// player kills this match (the bounty and other bonus frags don't count)
.float	ud_deaths;			// deaths to players and monsters this match (suicides, lava and falls don't count)
.float	ud_earned;			// 1 = a player or monster killed you last, so this spawn may get a free power-up
.float	ud_full;			// deaths in a row for Last Stand at the current player count
.float	ud_tier;			// leader effect tier 0..4 (announcements fire on the way up)
.entity	ud_aura;			// leader effects entity (glow, beacon, x-ray copy)
entity	ud_leader;			// player with the most heat (world = nobody far enough ahead)
.float	ud_shell_stage;		// Flying Blue Shell: 0 = normal Mega Man, 1 = 3D flight, 2 = overhead lock-on, 3 = slam
.float	ud_shell_t;			// Flying Blue Shell stage timer
.float	ud_laststand;		// 1 = spawned with Underdog Last Stand (Quad + Pentagram), cleared after first kill
.float	mr_geyser_t;		// Morro Rock ocean-geyser rescue cooldown

// ---------------------------------------------------------------- kill announcer (bm_fun.qc)
.float	bm_streak;			// player: kills since their last death
.float	bm_streak_tier;		// player: streak tier already announced (1 spree, 2 rampage, 3 godlike)
.float	bm_multi_t;			// player: when their last kill was
.float	bm_multi_n;			// player: kills in the current burst
.entity	bm_killer;			// player: who killed them last (revenge)
.float	bm_fun_cp_t;		// player: last time BM_Fun_Killed / Underdog_Killed sent a kill centerprint
.float	bm_taunt_t;			// player: PlayerPreThink taunt check throttle (separate from self.delay)
.float	bm_shirt_t;			// player: PlayerPreThink armor-shirt throttle (separate from self.delay)
.float	bm_ctf_dead_t;		// bot: CTF death respawn timer (separate from self.delay)
float	bm_fun_first;		// first blood has been drawn this map
float	bm_fun_say_t;		// when the next announcer clip may play

// ---------------------------------------------------------------- prototypes
void() BM_Frame;
void() BM_SwapIn;
void() BM_OutOfAmmo;
float() BM_CheckNoAmmo;
void() BM_Spawn;
void() BM_FillAll;
void() BM_FillCombatOnly;
float(entity p, float s) BM_GetMag;
float(float s) BM_MagSize;
float() BM_CurSlot;
void(float s) BM_StartReload;
void(entity p, float s, float v) BM_SetMag;
void() BM_WriteFields;
void() BM_FiredSSG;
void() BM_Precache;
float(entity targ, entity inflictor, entity attacker, float damage) BM_Damage;
void() BM_PlayerSpawned;
void() BM_SpawnArmor;
void() BM_LifeFrame;
float() BM_NextLevel;
float() BM_IntermissionThink;
void() BM_Stats;
void() BM_StartFrame;
void() BM_TestImpulses;
void() BM_Fun_Precache;
void(entity e, string clip) BM_Fun_Say;
void(entity targ, entity attacker) BM_Fun_Killed;
float(entity p) Underdog_IsLast;

void() Underdog_Update;
void() Underdog_FxFrame;
float() Underdog_PulseOn;
float() Underdog_RegenDelay;
float() Underdog_RegenRate;
void(float dt) Underdog_ArmorRegen;
float(entity p) Underdog_AmmoRate;
void(entity p) Underdog_Reset;

void() ExitIntermission;
void() execute_changelevel;

// ---------------------------------------------------------------- map votes (bm_match.qc)
.float	bm_voted;			// 0 = no vote, 1 = yes, 2 = no (reset when a vote starts)
.float	bm_vote_cool;		// this player can call a vote again after this time
float	bm_vote_on;			// a vote is open
float	bm_vote_end;		// when it times out
float	bm_vote_go_t;		// passed: change the map at this time
float	bm_vote_tick_t;
float	bm_vote_prompt_t;
float	bm_v_n;				// BM_VoteCount: humans, yes, no
float	bm_v_yes;
float	bm_v_no;
string	bm_vote_map;		// the map being voted on, strzoned

// ---------------------------------------------------------------- per-frame cached cvars & active player list
entity	bm_player_head;		// active connected "player" entities rebuilt once per frame in BM_StartFrame
.entity	bm_player_next;
float	bm_botmask_cache;
float	bm_playermask_cache;
var float	autocvar_sv_gravity		= 800;
var float	autocvar_sv_maxvelocity	= 2000;
var float	autocvar_ltg_video		= 0;
var float	autocvar_br_mode		= 0;
var float	autocvar_dv_mode		= 0;
var float	autocvar_dv_stay		= 0;
var float	autocvar_dn_mode		= 0;
var float	autocvar_dn_stay		= 0;
var float	autocvar_pk_viewoffset	= 0;
var float	autocvar_developer		= 0;
var float	autocvar_slowmo			= 1;
var float	autocvar_chase_active	= 0;
var float	autocvar_sv_cheats		= 0;
var float	autocvar_teamplay		= 0;
var float	autocvar_skill			= 1;
var float	autocvar_sv_maxspeed	= 320;
var float	autocvar_sv_friction	= 4;
var float	autocvar_sv_accelerate	= 10;
var float	autocvar_sv_stopspeed	= 100;
float	bm_cvar_grav;
float	bm_cvar_maxvel;
float	bm_cvar_ltg_video;
float	bm_cvar_br_mode;
float	bm_cvar_dv_mode;
float	bm_cvar_dv_stay;
float	bm_cvar_dn_mode;
float	bm_cvar_dn_stay;
float	bm_cvar_pk_ofs;
float	bm_cvar_dev;
float	bm_fun_precached;
float	david_precached;
float	daniel_precached;
float	greensuit_precached;
float	robeguy_precached;
void() David_Precache;
void() Daniel_Precache;
void() GreenSuit_Precache;
void() RobeGuy_Precache;
void() GreenSuit_Summon;
void() RobeGuy_Summon;
var float	autocvar_rnpc_mode	= 0;
var float	autocvar_rnpc_stay	= 0;
float	bm_cvar_rnpc_mode;
float	bm_cvar_rnpc_stay;
float	random_npcs_precached;
.float	bm_last_hit_dmg;
.float	bm_last_hit_explosive;
.float	npc_dead;
.float	npc_dstep;
float(entity e) NPC_ShouldGib;
void() RandomNPCs_Precache;
void(float kind) RandomNPC_Summon;
void() RandomNPC_SummonAll4;
float	bryan_precached;
float	vehicles_precached;
float	veh_has_vans;
float	jetpack_precached;
float	bktv_precached;
float	ltg_vid_precached;
.float	ud_fx_t;
.float	bm_dm_gun_alt;		// per-player DM starting weapon toggle (1 = RL, 2 = M4)
float	bm_dm_gun_seed;
float	skypad_precached;
float	skypad_present;
entity	skypad_head;
.entity	skypad_next;
.float	skypad_cool_t;
.float	skypad_steer_t;
.float	skypad_fx_t;
.float	skypad_safe_t;
.float	skypad_vel_sent;
void() SkyPad_Precache;
void() Q3Pad_Init;
void() MMT_DowntownInit;
void() SkyPad_LandWave;
void() SkyPad_Report;
void() SkyPad_Frame;
void() info_skypad;

// ---------------------------------------------------------------- downtown bots & full-arsenal AI (bm_bots.qc)
.float	bm_bot_wep_t;
.float	bm_bot_burst_t;
.float	bm_bot_pause_t;
.float	bm_bot_react_t;
.entity	bm_bot_lastfoe;
.float	bm_bot_gar_alt;
.float	bm_bot_wc_rel;
.float	bm_bot_hm_rel;
.float	bm_bot_jp_cd;
.float	bm_bot_jp_end;
.float	bm_bot_stuck_t;
.vector	bm_bot_stuck_org;
.float	bm_bot_free_t;
.vector	bm_bot_free_dir;
.float	bm_bot_hunt_t;
.float	bm_bot_roof_t;
.vector	bm_bot_aim_err;
.float	bm_bot_aim_t;
.float	bm_bot_mm_cd;
float	bm_manual_bots;
float	bm_dt_way_t;
float	bm_dt_way_done;
float	bm_route_lock_t;
float	bm_autobot_check_t;
float	bm_bot_add_t;
float	bm_bot_slot_t;
float	bm_bot_idle_t;

void() BM_MapLoad;
void(entity caller) BM_BotConnected;
void(string kname) BM_BotNotifyKick;
float() BM_BotImpulses;
vector(float wep) BM_BotWeaponRange;
float(float brange) BM_BotWeaponSwitch;
void() BM_BotShoot;
float(entity thing) BM_BotItemPriority;
void() BM_BotAimAdjust;
void() BM_BotPostAI;
void() BM_BotSpawnLoadout;
void() BM_BotStartFrame;
entity() BM_BotPickSpawn;

// ---------------------------------------------------------------- server observer / auto-director (bm_match.qc)
.float	bm_obs;				// 1 = headless recording observer client (invisible, non-solid, auto-director camera)
.float	bm_obs_frags_last;	// last seen frag count on watched players (action-switch scoring)
float	bm_obs_count;		// live observer count (subtracted from bot-reserve free-slot math)
float	bm_obs_qualify_t;	// cumulative seconds with >= 2 humans in this map
entity	bm_obs_targ;		// player currently watched by the auto-director
float	bm_obs_switch_t;	// earliest time auto-director may switch targets
float	bm_obs_force_t;		// latest time before auto-director rotates to another player
float	bm_obs_death_t;		// time watched target died (brief linger before switching)
vector	bm_obs_cam_org;		// smoothed camera origin
vector	bm_obs_cam_ang;		// smoothed camera angles
float	bm_obs_cam_init;	// 1 once camera origin/angles have been initialized
float	bm_obs_frame_t;		// previous server frame time for observer camera smoothing
void(entity e) BM_ObsActivate;
void() BM_ObsFrame;
void() BM_ObsCheckDiscard;

// wasfreed (#353) with a real type: the Combat+ defs declare it as __variant, which cannot be tested with ! or if ()
float(entity e) bm_wasfreed = #353;
