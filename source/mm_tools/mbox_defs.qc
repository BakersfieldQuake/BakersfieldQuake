/*
================
THE MYSTERY BOX (fun gun 5, impulse 65, key U; mbox.qc has the code)

You throw a rainbow-sparkle Mystery Box. It trails glitter, lands and bursts into confetti and magic, and out of it
come MB_SPAWNS random monster (one). Each one runs flat out along the floor at the nearest enemy (no jumping), gets in its
face and hits it every MB_HIT_GAP seconds, and blows up after MB_HITS hits or MB_LIFE seconds (or when shot).

Which monsters can come out is the cvar mb_pool, a list of roster numbers ("1 3 9 11"; empty = every monster that is
built). The roster (MB_TypeName in mbox.qc) is the 16 characters of the vote page mystery_box_monster_vote.html:
 1 Mega Man   2 Suit Rider   3 Pink Supercar   4 Squat Rider   5 NetSend PC   6 Casino Horse   7 Big-Ears   8 Forklift
 9 Wheelman  10 JessKart    11 Kyle (scissors) 12 Earhead     13 Pickle       14 Friend Rob    15 John's Hand  16 Rolling Wheelman
17 Bryan & Demons
Roster entries without a model in the game yet (12, 13, 15) are skipped by the draw. Every monster has the same
behaviour for now (MB_Think); the per-monster behaviours come once the user has said what each one does
(MB_Special in mbox.qc is the hook).

Models: progs/v_mysterybox.md3 (220 frames: 0-191 idle, 192-219 the throw), progs/proj_mysterybox.md3 (32-frame tumble),
built by source/mm_tools/mystery_box/build_mbox_models.py. Effects: effectinfo.txt "Mystery Box" block.
Hooks: funguns.qc (tables, FunGun_Attack, FunGun_ViewFrame), bm_reload.qc (BM_FG5 magazine).
================
*/

float	MB_THROW		= 1500;		// the box's speed when thrown: it goes a long way
float	MB_GRAVITY		= 0.45;		// the box's gravity (1 = normal): a flat, far throw
float	MB_THROW_DELAY	= 0.42;		// the hand lets go at frame 207 of v_mysterybox.md3, 0.42 s into the throw
float	MB_ANIM_FPS		= 36;		// v_mysterybox.md3 frames 192-219 play at this rate
float	MB_LIFE_BOX		= 6;		// a box that has not landed by then is lost (and the magazine gets it back)
float	MB_SPAWNS		= 1;		// monsters out of each box (the user cut it from 2 to 1 on 2026-11-01)
float	MB_SPEED		= 640;		// a monster's run along the floor toward its enemy (a player runs 320)
float	MB_FACE			= 30;		// it stops this close to its enemy (floor distance): right in their face (a player and a monster touch at about 34)
float	MB_STUCK		= 0.7;		// seconds without getting 48 units on before it glides through walls
float	MB_REACH		= 64;		// it can hit an enemy this close (floor distance)
float	MB_HITS			= 5;		// hits on the enemy before it blows up
float	MB_HIT_DMG		= 14;		// damage of each hit
float	MB_HIT_GAP		= 0.45;		// seconds between two hits that count
float	MB_LIFE			= 9;		// a monster blows up after this long whatever happens
float	MB_BLAST		= 45;		// its explosion, radius damage at the centre (T_RadiusDamage)
float	MB_HEALTH		= 30;		// shoot it to pieces: it explodes at once
float	MB_RETARGET		= 0.5;		// seconds between two looks for a nearer enemy
float	MB_WANDER		= 150;		// with nobody to chase it strolls about at this speed (review 2026-11-01: "it should start trolling around, looking around")
float	MB_MAX			= 4;		// monsters one player can have out; the oldest go first

.float	mb_type;		// monster: roster number
.float	mb_born;		// box / monster: spawn time
.float	mb_hits;		// monster: bounces on enemies so far
.float	mb_next_hit;	// monster: when the next bounce may count
.float	mb_next_look;	// monster: when it may pick its enemy again
.float	mb_run;			// monster: 1 while it is running (the sprites show their running frames)
.float	mb_yaw0;		// monster: yaw added to its heading (models that do not face +X)
.float	mb_f0, mb_fn, mb_fps;	// monster: first frame, frame count and rate of its running loop (3D models; 0 count = frame 0)
.vector	mb_pos;			// monster: where it was when mb_pos_t was set (the stuck check)
.float	mb_pos_t;		// monster: when it last checked it had got somewhere
.float	mb_snd_t;		// monster: when its running sound may be played again
.float	mb_glide;		// monster: TRUE once it is gliding through the geometry (noclip)
.float	mb_wt;			// monster: when it next decides what to do with nobody to chase
.float	mb_wy;			// monster: the way it is walking, or looking, while it wanders
.float	mb_wgo;			// monster: TRUE while it is strolling (else standing and looking round)
.entity	mb_target;		// monster: the enemy it is after

.float	mb_throw_at;	// player: when the box leaves the hand (0 = not throwing)
.float	mb_fire_t;		// player: when the throw began

void() MB_Precache;
void() MB_Throw;
void() MB_BoxTouch;
void() MB_BoxThink;
void() MB_Think;
void() MB_Touch;
void() MB_Explode;
void() MB_Shot;
