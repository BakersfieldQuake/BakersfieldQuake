/*
================
robhead_defs.qc — Rob Dob DJI Drone Remote Viewmodel (FG_DOB, impulse 61 / 17)
  progs/v_robhead_drone.md3 (2-surface MD3: card + far-right floating Rob head)
  launches steerable FD_Launch drone (floathead.qc)

112-skin viewmodel layout:
  0..59   idle loop (60f)
  60..75  ready / target-lock loop (16f)
  76..83  thumb-to-button press (8f; drone launches at skin 84)
  84..93  remote lower follow-through (10f)
  94..111 raise / reset reload (18f)
================
*/

float	RH_VM_IDLE_SKIN			= 0;
float	RH_VM_IDLE_COUNT		= 60;		// 0..59 @ 24 FPS * anim_spd
float	RH_VM_WIND_SKIN			= 60;
float	RH_VM_WIND_COUNT		= 16;		// 60..75 @ 32 FPS * anim_spd
float	RH_VM_PRE_SKIN			= 76;
float	RH_VM_PRE_COUNT			= 8;		// 76..83 button press
float	RH_VM_POST_SKIN			= 84;
float	RH_VM_POST_COUNT		= 10;		// 84..93 release + remote lower
float	RH_VM_RELOAD_SKIN		= 94;
float	RH_VM_RELOAD_COUNT		= 18;		// 94..111 raise / reset reload

float	RH_DRONE_DELAY			= 0.11;		// thumb moves to & presses red button before FD_Launch() (1.45x speed)
float	RH_DRONE_ANIM_SPEED		= 1.45;		// David's final tuned Drone animation speed multiplier
float	RH_DRONE_BOB_SCALE		= 0.50;		// David's final tuned Drone bobPct (50%)
float	RH_FOLLOW_TIME			= 0.22;		// follow-through duration (scaled by 1 / anim_spd)
float	RH_RAISE_TIME			= 0.25;		// reload raise duration (scaled by 1 / anim_spd)

.float	rh_charging;		// player: timestamp when hold-fire started (0 = idle)
.float	rh_charge_gun;		// player: FG_DOB when active
.float	rh_next_juggle;		// player: next charge sound timestamp
.float	rh_fire_t;			// player: timestamp when button-press animation started
.float	rh_throw_at;		// player: timestamp when FD_Launch() fires
.float	rh_throw_gun;		// player: FG_DOB when launching
.float	rh_threw_t;			// player: timestamp when drone launched
.float	rh_reload_t;		// player: timestamp when raise/reset started
.float	rh_empty;			// player: TRUE while out of ammo after follow-through
.float	rhvm_on;			// viewmodel entity: active slot (FG_DOB or 0)
.entity	fd_head;			// player: the Rob Dob head he is flying (world = not flying)
.float	fd_warn_t;			// player: throttle Rob Dob body-under-attack warning
.float	fd_chatter_t;		// head: next random mid-flight voice chatter (Rob / Paul)
.float	fd_chatter_idx;		// head: alternate chatter index
.entity	fd_miss_ent;		// head: closest enemy approached during Dash for near-miss check
.float	fd_miss_d;			// head: closest distance recorded to fd_miss_ent
.float	fd_miss_t;			// head: cooldown timestamp for "Aw, I missed!"

void() RobHead_Precache;
void() RH_DronePress;
void() RH_Frame;
void(entity p) RH_ResetPlayer;
void(entity vm, float is_quad) RobHead_ViewFrame;
