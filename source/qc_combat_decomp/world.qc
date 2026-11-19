//Decompiled code. Please respect the original copyright.

void() main =
{
	dprint("main function\n");
	precache_file("progs.dat");
	precache_file("gfx.wad");
	precache_file("quake.rc");
	precache_file("default.cfg");
	precache_file("end1.bin");
	precache_file2("end2.bin");
	precache_file("demo1.dem");
	precache_file("demo2.dem");
	precache_file("demo3.dem");
	precache_file("gfx/palette.lmp");
	precache_file("gfx/colormap.lmp");
	precache_file2("gfx/pop.lmp");
	precache_file("gfx/complete.lmp");
	precache_file("gfx/inter.lmp");
	precache_file("gfx/ranking.lmp");
	precache_file("gfx/vidmodes.lmp");
	precache_file("gfx/finale.lmp");
	precache_file("gfx/conback.lmp");
	precache_file("gfx/qplaque.lmp");
	precache_file("gfx/menudot1.lmp");
	precache_file("gfx/menudot2.lmp");
	precache_file("gfx/menudot3.lmp");
	precache_file("gfx/menudot4.lmp");
	precache_file("gfx/menudot5.lmp");
	precache_file("gfx/menudot6.lmp");
	precache_file("gfx/menuplyr.lmp");
	precache_file("gfx/bigbox.lmp");
	precache_file("gfx/dim_modm.lmp");
	precache_file("gfx/dim_drct.lmp");
	precache_file("gfx/dim_ipx.lmp");
	precache_file("gfx/dim_tcp.lmp");
	precache_file("gfx/dim_mult.lmp");
	precache_file("gfx/mainmenu.lmp");
	precache_file("gfx/box_tl.lmp");
	precache_file("gfx/box_tm.lmp");
	precache_file("gfx/box_tr.lmp");
	precache_file("gfx/box_ml.lmp");
	precache_file("gfx/box_mm.lmp");
	precache_file("gfx/box_mm2.lmp");
	precache_file("gfx/box_mr.lmp");
	precache_file("gfx/box_bl.lmp");
	precache_file("gfx/box_bm.lmp");
	precache_file("gfx/box_br.lmp");
	precache_file("gfx/sp_menu.lmp");
	precache_file("gfx/ttl_sgl.lmp");
	precache_file("gfx/ttl_main.lmp");
	precache_file("gfx/ttl_cstm.lmp");
	precache_file("gfx/mp_menu.lmp");
	precache_file("gfx/netmen1.lmp");
	precache_file("gfx/netmen2.lmp");
	precache_file("gfx/netmen3.lmp");
	precache_file("gfx/netmen4.lmp");
	precache_file("gfx/netmen5.lmp");
	precache_file("gfx/sell.lmp");
	precache_file("gfx/help0.lmp");
	precache_file("gfx/help1.lmp");
	precache_file("gfx/help2.lmp");
	precache_file("gfx/help3.lmp");
	precache_file("gfx/help4.lmp");
	precache_file("gfx/help5.lmp");
	precache_file("gfx/pause.lmp");
	precache_file("gfx/loading.lmp");
	precache_file("gfx/p_option.lmp");
	precache_file("gfx/p_load.lmp");
	precache_file("gfx/p_save.lmp");
	precache_file("gfx/p_multi.lmp");
	precache_sound("misc/menu1.wav");
	precache_sound("misc/menu2.wav");
	precache_sound("misc/menu3.wav");
	precache_sound("ambience/water1.wav");
	precache_sound("ambience/wind2.wav");
	precache_file("maps/start.bsp");
	precache_file("maps/e1m1.bsp");
	precache_file("maps/e1m2.bsp");
	precache_file("maps/e1m3.bsp");
	precache_file("maps/e1m4.bsp");
	precache_file("maps/e1m5.bsp");
	precache_file("maps/e1m6.bsp");
	precache_file("maps/e1m7.bsp");
	precache_file("maps/e1m8.bsp");
	precache_file2("gfx/pop.lmp");
	precache_file2("maps/e2m1.bsp");
	precache_file2("maps/e2m2.bsp");
	precache_file2("maps/e2m3.bsp");
	precache_file2("maps/e2m4.bsp");
	precache_file2("maps/e2m5.bsp");
	precache_file2("maps/e2m6.bsp");
	precache_file2("maps/e2m7.bsp");
	precache_file2("maps/e3m1.bsp");
	precache_file2("maps/e3m2.bsp");
	precache_file2("maps/e3m3.bsp");
	precache_file2("maps/e3m4.bsp");
	precache_file2("maps/e3m5.bsp");
	precache_file2("maps/e3m6.bsp");
	precache_file2("maps/e3m7.bsp");
	precache_file2("maps/e4m1.bsp");
	precache_file2("maps/e4m2.bsp");
	precache_file2("maps/e4m3.bsp");
	precache_file2("maps/e4m4.bsp");
	precache_file2("maps/e4m5.bsp");
	precache_file2("maps/e4m6.bsp");
	precache_file2("maps/e4m7.bsp");
	precache_file2("maps/e4m8.bsp");
	precache_file2("maps/end.bsp");
	precache_file2("maps/dm1.bsp");
	precache_file2("maps/dm2.bsp");
	precache_file2("maps/dm3.bsp");
	precache_file2("maps/dm4.bsp");
	precache_file2("maps/dm5.bsp");
	precache_file2("maps/dm6.bsp");
};

float(entity dummyent, float changedflags) SendWorldType =
{
	msg_entity = self;
	WriteByte(MSG_ENTITY, ET_WORLDSPAWN);
	WriteByte(MSG_ENTITY, world.worldtype);
	return (TRUE);
};

float() connect_me_with_client =
{
	setorigin(self, other.origin);
	return (TRUE);
};

void() worldspawn =
{
	local entity foo;

	lastspawn = world;
	World_DetectQ1Surfaces();
	BotInit();
	InitBodyQue();
	clientstat(40, 2, grenade_ammo);
	clientstat(41, 2, invisible_counter);
	clientstat(42, 2, super_damage_counter);
	clientstat(43, 2, radsuit_counter);
	clientstat(44, 2, invincible_counter);
	clientstat(45, 2, lives);
	clientstat(46, 2, slowmo_timer);
	clientstat(47, 2, PLR_SNDSPD);
	clientstat(48, 3, origin);
	clientstat(49, 2, blue_captures);
	clientstat(50, 2, red_captures);
	clientstat(51, 2, gametype);
	BM_Stats();
	if ((autocvar_ctf == 1))
	{
		enable_ctf();
	}
	if (autocvar_chasecam_death_view)
	{
		cvar_set("chase_active", "0");
		cvar_set("chase_back", "65");
		cvar_set("chase_up", "10");
		cvar_set("chase_overhead", "0");
	}
	if ((self.model == "maps/e1m8.bsp"))
	{
		cvar_set("sv_gravity", "100");
	}
	else
	{
		cvar_set("sv_gravity", "800");
	}
	W_Precache();
	Practice_Precache();
	precache_sound("demon/dland2.wav");
	precache_sound("misc/h2ohit1.wav");
	precache_sound("player/watersplash.wav");
	precache_sound("ambience/lavasplash.wav");
	precache_sound("misc/corpsegib.wav");
	precache_sound("zombie/z_hit.wav");
	precache_model("progs/null.spr");
	precache_sound("player/click.wav");
	precache_sound("player/personal_player_teleport.wav");
	// Precache runtime-used assets unconditionally in worldspawn (no post-spawn precache_* calls)
	precache_sound("ambience/lavasplash_shotgun.wav");
	precache_model("progs/backpack1.mdl");
	precache_sound("zombie/penttouch.wav");
	precache_sound("items/suit.wav");
	precache_sound("items/suit2.wav");
	precache_sound("items/damage.wav");
	precache_sound("items/damage2.wav");
	precache_sound("items/damage3.wav");
	precache_sound("items/inv1.wav");
	precache_sound("items/inv2.wav");
	precache_sound("items/inv3.wav");
	precache_sound("items/protect.wav");
	precache_sound("items/protect2.wav");
	precache_sound("items/protect3.wav");
	precache_model("progs/backpack_soldier.mdl");
	precache_model("progs/backpack_enforcer.mdl");
	precache_model("progs/backpack_ogre.mdl");
	precache_sound("ambience/backpack_soldier.wav");
	precache_sound("ambience/backpack_enforcer.wav");
	precache_sound("ambience/backpack_ogre.wav");
	precache_sound("ambience/backpack_enforcer_ambience.wav");
	precache_model("progs/corpse_pent.mdl");
	precache_sound("zombie/corpse_lit.wav");
	precache_sound("zombie/corpse_fire.wav");
	precache_sound("player/inflame.wav");
	if ((autocvar_gruntcasing || autocvar_shellcasing))
	{
		precache_model("progs/casing.mdl");
		precache_model("progs/nailcasing.mdl");
		precache_model("progs/missilecasing.mdl");
		precache_sound("weapons/casings1.wav");
		precache_sound("weapons/casings2.wav");
		precache_sound("weapons/casings3.wav");
		precache_sound("weapons/nailcase1.wav");
		precache_sound("weapons/nailcase2.wav");
		precache_sound("weapons/nailcase3.wav");
		precache_sound("weapons/rockcase1.wav");
		precache_sound("weapons/rockcase.wav");
	}
	precache_sound("weapons/weapon1.wav");
	precache_sound("weapons/weapon2.wav");
	precache_sound("weapons/weapon3.wav");
	precache_sound("weapons/weapon4.wav");
	precache_sound("weapons/weapon5.wav");
	precache_sound("weapons/weapon6.wav");
	precache_sound("weapons/weapon7.wav");
	precache_sound("weapons/weapon8.wav");
	precache_sound("hipweap/weapon9.wav");
	precache_sound("ambience/coaled_monster_explode.wav");
	precache_sound("misc/null.wav");
	precache_sound("kickgib/gib_metal.wav");
	precache_sound("kickgib/gib_plastic.wav");
	precache_sound("weapons/explodedist.wav");
	precache_sound("misc/swordbounce.wav");
	precache_sound("kickgib/gib_miss.wav");
	precache_sound("kickgib/gib_hit.wav");
	precache_sound("player/gibexplode.wav");
	precache_sound("kickgib/kick_debris1.wav");
	precache_sound("kickgib/kick_debris2.wav");
	precache_sound("kickgib/kick_debris3.wav");
	precache_sound("items/itembk2.wav");
	precache_sound("player/plyrjmp8.wav");
	precache_sound("player/land.wav");
	precache_sound("player/land2.wav");
	precache_sound("player/drown1.wav");
	precache_sound("player/drown2.wav");
	precache_sound("player/gasp1.wav");
	precache_sound("player/gasp2.wav");
	precache_sound("player/h2odeath.wav");
	precache_sound("player/lavadeath.wav");
	precache_sound("player/slimedeath.wav");
	precache_sound("player/blasterdeath.wav");
	precache_sound("misc/burn1.wav");
	precache_sound("misc/burn2.wav");
	precache_sound("soldier/fall_forwards.wav");
	precache_sound("weapons/lstart.wav");
	precache_sound2("shalrath/firesum.wav");
	precache_sound2("misc/summon.wav");
	if (((!deathmatch && (world.model != "maps/start.bsp")) && ((((((((((autocvar_spider_replace_demon || autocvar_spider_replace_dog) || autocvar_spider_replace_enforcer) || autocvar_spider_replace_hknight) || autocvar_spider_replace_knight) || autocvar_spider_replace_ogre) || autocvar_spider_replace_shalrath) || autocvar_spider_replace_shambler) || autocvar_spider_replace_soldier) || autocvar_spider_replace_tarbaby) || autocvar_spider_replace_zombie)))
	{
		precache_model("progs/spider.mdl");
		precache_model("progs/h_spidbody.mdl");
		precache_model("progs/spider_shambler.mdl");
		precache_model("progs/h_spidbodyshamb.mdl");
		precache_model("progs/web.mdl");
		precache_sound("spider/spider_walk1.wav");
		precache_sound("spider/spider_walk2.wav");
		precache_sound("spider/spider_sight.wav");
		precache_sound("spider/spider_idle.wav");
		precache_sound("spider/spider_bite.wav");
		precache_sound("spider/spider_headbang.wav");
		precache_sound("spider/spider_legattack.wav");
		precache_sound("spider/spider_jump.wav");
		precache_sound("spider/spider_spit.wav");
		precache_sound("spider/spider_impact.wav");
		precache_sound("spider/spider_pain.wav");
		precache_sound("spider/spider_death.wav");
	}
	if (((!deathmatch && (world.model != "maps/start.bsp")) && (autocvar_warlord_replace_hknight || autocvar_warlord_replace_ogre)))
	{
		precache_model("progs/warlord.mdl");
		precache_model("progs/h_warlord.mdl");
		precache_model("progs/k_spike2.mdl");
		precache_model("progs/h_grenade2.mdl");
		precache_model("progs/h_grenade1.mdl");
		precache_model("progs/face.mdl");
		precache_sound("warlord/attack1.wav");
		precache_sound("warlord/attack2.wav");
		precache_sound("warlord/attack3.wav");
		precache_sound("warlord/death1.wav");
		precache_sound("warlord/pain1.wav");
		precache_sound("warlord/pain2.wav");
		precache_sound("warlord/sight1.wav");
		precache_sound("warlord/slash1.wav");
		precache_sound("warlord/idle.wav");
		precache_sound("warlord/growl.wav");
		precache_sound("warlord/ram.wav");
		precache_sound("warlord/throw.wav");
		precache_sound("warlord/fall.wav");
		precache_sound("warlord/homing.wav");
		precache_sound("warlord/homing_shot.wav");
		precache_sound("warlord/homing_pain.wav");
		precache_sound("warlord/homing_touch.wav");
		precache_sound("walk/hknight1.wav");
		precache_sound("walk/hknight2.wav");
		precache_sound("walk/hknight3.wav");
		precache_sound("knight/sword1.wav");
		precache_sound("knight/sword2.wav");
	}
	if (((!deathmatch && (world.model != "maps/start.bsp")) && (((autocvar_torment_replace_demon || autocvar_torment_replace_hknight) || autocvar_torment_replace_knight) || autocvar_torment_replace_ogre)))
	{
		precache_model("progs/torment.mdl");
		precache_model("progs/h_torment.mdl");
		precache_model("progs/torm_lavaball.mdl");
		precache_sound("torment/alert.wav");
		precache_sound("torment/idle.wav");
		precache_sound("torment/scratch.wav");
		precache_sound("torment/death1.wav");
		precache_sound("torment/fall.wav");
		precache_sound("torment/hellstaff_swing1.wav");
		precache_sound("torment/hellstaff_swing2.wav");
		precache_sound("torment/pain1.wav");
		precache_sound("torment/pain2.wav");
		precache_sound("torment/pain3.wav");
		precache_sound("torment/firehit.wav");
		precache_sound("torment/hellstafffire.wav");
		precache_sound("walk/torment1.wav");
		precache_sound("walk/torment2.wav");
	}
	if (((!deathmatch && (world.model != "maps/start.bsp")) && ((((autocvar_carnivean_replace_hellknight || autocvar_carnivean_replace_ogre) || autocvar_carnivean_replace_shalrath) || autocvar_carnivean_replace_shambler) || autocvar_carnivean_replace_knight)))
	{
		precache_model("progs/carnivean.mdl");
		precache_model("progs/h_carnivean.mdl");
		precache_model("progs/carniv_rocks.mdl");
		precache_model("progs/k_spike.mdl");
		precache_sound("demon/fall_backwards.wav");
		precache_sound("soldier/decap.wav");
		precache_sound("warlord/shielddrop.wav");
		precache_sound("player/gibsplit.wav");
		precache_sound("demon/dhit2.wav");
		precache_sound("carnivean/rock_throw.wav");
		precache_sound("carnivean/death1.wav");
		precache_sound("carnivean/death2.wav");
		precache_sound("carnivean/idle1.wav");
		precache_sound("carnivean/idle2.wav");
		precache_sound("carnivean/swing.wav");
		precache_sound("carnivean/pain1.wav");
		precache_sound("carnivean/pain2.wav");
		precache_sound("carnivean/scream.wav");
		precache_sound("carnivean/step1.wav");
		precache_sound("carnivean/step2.wav");
	}
	if (((!deathmatch && (world.model != "maps/start.bsp")) && ((((autocvar_yakman_replace_hellknight || autocvar_yakman_replace_ogre) || autocvar_yakman_replace_shalrath) || autocvar_yakman_replace_shambler) || autocvar_yakman_replace_knight)))
	{
		precache_model("progs/yakman.mdl");
		precache_model("progs/h_yak.mdl");
		precache_model("progs/s_kinn.spr");
		precache_sound("yakman/woosh.wav");
		precache_sound("yakman/big1.wav");
		precache_sound("yakman/big3.wav");
		precache_sound("yakman/grunt.wav");
		precache_sound("yakman/snort1.wav");
		precache_sound("yakman/snort2.wav");
		precache_sound("yakman/crash.wav");
		precache_sound("yakman/death.wav");
		precache_sound("yakman/die.wav");
		precache_sound("yakman/expsmall.wav");
		precache_sound("yakman/firefblt.wav");
		precache_sound("yakman/pain.wav");
		precache_sound("yakman/slam.wav");
		precache_sound("yakman/step1.wav");
		precache_sound("yakman/step2.wav");
		precache_sound("shambler/fall.wav");
	}
	precache_model("progs/ghost.mdl");
	precache_sound("ghost/ghost.wav");
	if ((world.model != "maps/start.bsp"))
	{
		precache_sound("traps/flame_loop.wav");
		precache_sound("traps/steam_loop.wav");
		precache_model("progs/s_flame.spr");
		precache_model("progs/invisibl.mdl");
		precache_model("progs/timerune.mdl");
		precache_model("progs/invulner.mdl");
		precache_model("progs/quaddama.mdl");
		precache_sound("items/damage.wav");
		precache_sound("items/damage2.wav");
		precache_sound("items/damage3.wav");
		precache_sound("ambience/backpack_enforcer.wav");
		precache_sound("misc/backpack_armour.wav");
		precache_sound("misc/backpack_ammo.wav");
		precache_sound("items/inv1.wav");
		precache_sound("items/inv2.wav");
		precache_sound("items/inv3.wav");
		precache_sound("items/protect.wav");
		precache_sound("items/protect2.wav");
		precache_sound("items/protect3.wav");
		precache_sound("items/slowmo_pickup.wav");
		precache_sound("items/slowmo_expire.wav");
		precache_model("progs/h_ogre.mdl");
		precache_model2("progs/laser.mdl");
		precache_model("progs/lasrspik.mdl");
		precache_sound2("enforcer/enfire.wav");
		precache_sound2("enforcer/enfstop.wav");
		precache_model("progs/k_spike.mdl");
		precache_sound("afrit/body_explode.wav");
		precache_sound("hknight/attack1.wav");
		precache_model("progs/w_spike.mdl");
		precache_sound("demon/dhit2.wav");
		if (!deathmatch)
		{
			precache_sound("lostsoul/charge.wav");
			precache_sound("lostsoul/idle1.wav");
			precache_sound("lostsoul/pain1.wav");
			precache_sound("lostsoul/idle2.wav");
			precache_sound("vengeance/skulltouch.wav");
			precache_sound("boss1/atk2.wav");
			precache_sound("boss1/quake.wav");
			precache_model("progs/lavacrack.mdl");
			precache_model("progs/voreling.mdl");
			precache_sound("voreling/death.wav");
			precache_sound("voreling/attackmunch.wav");
			precache_sound("voreling/attacktear.wav");
			precache_sound("voreling/pain.wav");
			precache_sound("voreling/idle.wav");
			precache_sound("voreling/sight.wav");
			precache_sound("spider/spider_walk1.wav");
			precache_sound("spider/spider_walk2.wav");
			precache_sound("spider/spider_sight.wav");
			precache_sound("spider/spider_idle.wav");
			precache_sound("spider/spider_bite.wav");
			precache_sound("spider/spider_headbang.wav");
			precache_sound("spider/spider_legattack.wav");
			precache_sound("spider/spider_jump.wav");
			precache_sound("spider/spider_spit.wav");
			precache_sound("spider/spider_impact.wav");
			precache_sound("spider/spider_pain.wav");
			precache_sound("spider/spider_death.wav");
			precache_sound("freddie/sawstart.wav");
			precache_sound("freddie/mangle.wav");
			precache_sound("freddie/idle1.wav");
			precache_sound("freddie/stfire.wav");
			precache_sound("freddie/death.wav");
			precache_sound("freddie/pain.wav");
			precache_sound("freddie/painshrt.wav");
			precache_sound("freddie/sight.wav");
			precache_sound("freddie/step.wav");
			precache_sound("freddie/step2.wav");
			precache_sound("freddie/step3.wav");
			precache_model("progs/mon_freddie.mdl");
			precache_model("progs/mon_jim.mdl");
			precache_model("progs/mon_jimrock.mdl");
			precache_sound("jim/laser_load.wav");
			precache_sound("jim/rocket_load.wav");
			precache_sound("jim/rocket_fire.wav");
			precache_sound("jim/rocket_hit.wav");
			precache_sound("jim/idle1.wav");
			precache_sound("jim/idle1r.wav");
			precache_sound("jim/death1.wav");
			precache_sound("jim/explode_minor.wav");
			precache_sound("jim/explode_major.wav");
			precache_sound("jim/gunidle2.wav");
			precache_sound("jim/sight1.wav");
			precache_sound("jim/pain1.wav");
			precache_sound("jim/pain2.wav");
			precache_model("progs/afrit.mdl");
			precache_model("progs/h_afrit.mdl");
			precache_model("progs/gib_afrit.mdl");
			precache_sound("afrit/attack.wav");
			precache_sound("afrit/awake.wav");
			precache_sound("afrit/death.wav");
			precache_sound("afrit/idle.wav");
			precache_sound("afrit/pain1.wav");
			precache_sound("afrit/pain2.wav");
			precache_sound("afrit/sight.wav");
			precache_sound("afrit/wingsflap.wav");
			precache_sound("afrit/fireballtouch.wav");
			precache_model("progs/skull.mdl");
			precache_sound("vengeance/shalthrow.wav");
			precache_sound("vengeance/shamawake.wav");
			precache_sound("vengeance/shamattck1.wav");
			precache_sound("vengeance/hknightmag.wav");
			precache_model("progs/wings.mdl");
			precache_sound("soul/liftup.wav");
			precache_sound("soul/flash.wav");
			precache_sound("soul/wingsflap.wav");
			precache_sound("soul/wingshot.wav");
			precache_sound("soul/awake.wav");
			precache_model("progs/hydra.mdl");
			precache_sound("hydra/hydra_death.wav");
			precache_sound("hydra/spit_impact_player.wav");
			precache_sound("hydra/hydra_pain.wav");
			precache_sound("hydra/hydra_spit.wav");
			precache_sound("hydra/hydra_idle.wav");
			precache_sound("hydra/hydra_idle2.wav");
			precache_sound("hydra/hydra_tent.wav");
			precache_model("progs/reiver.mdl");
			precache_model("progs/reiver_fireball.mdl");
			precache_model("progs/ghost_follower.spr32");
			precache_model("progs/reiver_shield.mdl");
			precache_model("progs/reiverhands.spr");
			precache_sound("reiver/ghost_flying.wav");
			precache_sound("reiver/ghost_follower_death.wav");
			precache_sound("reiver/reiver_fireball_shoot.wav");
			precache_sound("reiver/raith3.wav");
			precache_sound("reiver/pain1.wav");
			precache_sound("reiver/pain2.wav");
			precache_sound("reiver/ranged_attack.wav");
			precache_sound("reiver/ranged_attack2.wav");
			precache_sound("reiver/run.wav");
			precache_sound("reiver/sight.wav");
			precache_sound("reiver/death.wav");
			precache_sound("reiver/vampire.wav");
		}
	}
	if ((autocvar_evil_faces > 0))
	{
		precache_model("progs/face1.mdl");
		precache_model("progs/face.mdl");
		precache_sound("face/face_pain.wav");
		precache_sound("face/face.wav");
		precache_sound("face/face_touch.wav");
	}
	if (autocvar_player_legs_visibility)
	{
		precache_model("progs/player_legs1.mdl");
		precache_model("progs/player_legs2.mdl");
	}
	precache_sound("ambience/rumblefade.wav");
	precache_sound("misc/talk.wav");
	precache_sound("player/teledth1.wav");
	precache_sound("misc/r_tele1.wav");
	precache_sound("misc/r_tele2.wav");
	precache_sound("misc/r_tele3.wav");
	precache_sound("misc/r_tele4.wav");
	precache_sound("misc/r_tele5.wav");
	precache_sound("weapons/lock4.wav");
	precache_sound("weapons/pkup.wav");
	precache_sound("items/armor1.wav");
	precache_sound("weapons/lhit.wav");
	precache_sound("weapons/lstart.wav");
	precache_sound("weapons/v_mage1_idle.wav");
	precache_sound("items/damage3.wav");
	precache_sound("misc/power.wav");
	if ((autocvar_invisibleweapons != 0))
	{
		invisweapon = 1;
	}
	if ((autocvar_psycho == 1))
	{
		quadpsycho = 1;
	}
	if ((autocvar_psycho == 2))
	{
		pentpsycho = 1;
	}
	if ((autocvar_psycho == 3))
	{
		quadpsycho = 1;
		pentpsycho = 1;
	}
	if ((autocvar_welcome != 0))
	{
		welcomenote = 1;
	}
	precache_sound("player/gib.wav");
	precache_sound("player/udeath.wav");
	precache_sound("player/udeath2.wav");
	precache_sound("player/tornoff2.wav");
	precache_sound("misc/gib2.wav");
	precache_sound("player/pain1.wav");
	precache_sound("player/pain2.wav");
	precache_sound("player/pain3.wav");
	precache_sound("player/pain4.wav");
	precache_sound("player/pain5.wav");
	precache_sound("player/pain6.wav");
	precache_sound("player/death1.wav");
	precache_sound("player/death2.wav");
	precache_sound("player/death3.wav");
	precache_sound("player/death4.wav");
	precache_sound("player/death5.wav");
	precache_sound("misc/fall_backwards.wav");
	precache_sound("misc/gundrop.wav");
	precache_sound("misc/megagib.wav");
	precache_sound("soldier/decap.wav");
	precache_sound("warlord/shielddrop.wav");
	precache_sound("player/gibsplit.wav");
	precache_sound("misc/paste.wav");
	precache_sound("player/buzzdeath.wav");
	precache_sound("weapons/ax1.wav");
	precache_sound("player/axhit1.wav");
	precache_sound("player/axhit2.wav");
	precache_sound("player/axeflesh1.wav");
	precache_sound("player/axeflesh2.wav");
	precache_sound("player/axeflesh3.wav");
	precache_sound("player/kickhitw.wav");
	precache_sound("player/kickflesh.wav");
	precache_sound("player/kickflesh2.wav");
	precache_sound(SOUND_AXE_STONE);
	precache_sound(SOUND_AXE_WOOD);
	precache_sound(SOUND_AXE_GLASS);
	precache_sound(SOUND_AXE_METAL);
	precache_sound("ambience/gibheartbeat.wav");
	precache_sound("misc/z_gib.wav");
	precache_sound("player/h2ojump.wav");
	precache_sound("player/slimbrn2.wav");
	precache_sound("player/inh2o.wav");
	precache_sound("player/inlava.wav");
	precache_sound("misc/outwater.wav");
	precache_sound("player/lburn1.wav");
	precache_sound("player/lburn2.wav");
	precache_sound("misc/water1.wav");
	precache_sound("misc/water2.wav");
	precache_sound("walk/generic1.wav");
	precache_sound("walk/generic2.wav");
	precache_sound("walk/generic3.wav");
	precache_sound("walk/generic4.wav");
	precache_sound("walk/generic5.wav");
	precache_sound("walk/metal1.wav");
	precache_sound("walk/metal2.wav");
	precache_sound("walk/metal3.wav");
	precache_sound("walk/metal4.wav");
	precache_sound("walk/pl_dirt1.wav");
	precache_sound("walk/pl_dirt2.wav");
	precache_sound("walk/pl_dirt3.wav");
	precache_sound("walk/pl_dirt4.wav");
	precache_sound("custom/flesh1.wav");
	precache_sound("custom/flesh2.wav");
	precache_sound("custom/flesh3.wav");
	precache_sound("custom/flesh4.wav");
	precache_sound("custom/flesh5.wav");
	precache_sound("walk/waterwade1.wav");
	precache_sound("walk/waterwade2.wav");
	precache_sound("buzz/buzz.wav");
	precache_sound("buzz/buzz1.wav");
	precache_sound("debris/metal1.wav");
	precache_sound("debris/metal2.wav");
	precache_sound("debris/metal3.wav");
	precache_sound("gib/gibhit1.wav");
	precache_sound("gib/gibhit2.wav");
	precache_sound("gib/gibhit3.wav");
	precache_sound("gib/gibhit4.wav");
	precache_sound("gib/gibhit6.wav");
	if ((autocvar_player_model == 1))
	{
		precache_model("progs/player1.mdl");
		precache_model("progs/h_player1.mdl");
	}
	else
	{
		if ((autocvar_player_model == 2))
		{
			precache_model("progs/player2.mdl");
			precache_model("progs/h_player2.mdl");
		}
		else
		{
			if ((autocvar_player_model == 3))
			{
				precache_model("progs/player3.mdl");
				precache_model("progs/h_player3.mdl");
			}
			else
			{
				if ((autocvar_player_model == 4))
				{
					precache_model("progs/player4.mdl");
					precache_model("progs/h_player4.mdl");
				}
				else
				{
					precache_model("progs/player_id1.mdl");
					precache_model("progs/player.mdl");
					precache_model("progs/h_player.mdl");
					if ((autocvar_player_model == 5))
					{
						precache_model("progs/player_torso.mdl");
						precache_model("progs/player_low.mdl");
					}
				}
			}
		}
	}
	if (autocvar_3rd_person_visible_weapons)
	{
		precache_model("progs/player_shot.mdl");
		precache_model("progs/player_shot2.mdl");
		precache_model("progs/player_nail.mdl");
		precache_model("progs/player_nail2.mdl");
		precache_model("progs/player_rock.mdl");
		precache_model("progs/player_rock2.mdl");
		precache_model("progs/player_light.mdl");
	}
	precache_model("progs/eyes.mdl");
	precache_model("progs/gib1.mdl");
	precache_model("progs/gib2.mdl");
	precache_model("progs/gib3.mdl");
	precache_model("progs/gibby.mdl");
	precache_model("progs/gibheart.mdl");
	precache_model("progs/gib_splat.mdl");
	precache_model("progs/bloodpool.mdl");
	precache_model("progs/gib_soldfoot1.mdl");
	precache_model("progs/gib_soldfoot2.mdl");
	precache_model("progs/rebreather.mdl");
	precache_model("progs/rebr_glass.spr");
	precache_model("progs/pack_attach.mdl");
	precache_model("progs/player_legs1_suit.mdl");
	precache_model("progs/gib_4.mdl");
	precache_model("progs/gib_5.mdl");
	precache_model("progs/chop.mdl");
	precache_model("progs/misc_broken.mdl");
	precache_model("progs/misc_spark.mdl");
	precache_model("progs/zom_gib.mdl");
	precache_model("progs/player_scorch.mdl");
	precache_model("progs/player_melt.mdl");
	precache_model("progs/player_scorchlegs.mdl");
	precache_model("progs/player_swim.mdl");
	precache_model("progs/gib_ribs.mdl");
	precache_model("progs/gib_skull.mdl");
	precache_model("progs/gib_gargwing2.mdl");
	precache_model("progs/w_knightsword.mdl");
	precache_model("progs/w_dknightsword.mdl");
	precache_model("progs/w_soldiergun.mdl");
	precache_model("progs/w_enforcergun.mdl");
	precache_model("progs/w_chainsaw.mdl");
	precache_model("progs/w_ogregl.mdl");
	precache_model("progs/w_wshield.mdl");
	precache_model("progs/w_wsword.mdl");
	precache_model("progs/coal.mdl");
	precache_model("progs/soldier1_sg.mdl");
	precache_model("progs/soldier_sg.mdl");
	precache_model("progs/soldier1_pain.mdl");
	precache_model("progs/soldier_pain.mdl");
	precache_model("progs/player_ssg.mdl");
	precache_model("progs/player_axe.mdl");
	precache_model("progs/player_ng.mdl");
	precache_model("progs/player_decap.mdl");
	precache_model("progs/player_deleg.mdl");
	precache_model("progs/player_disarm.mdl");
	precache_model("progs/player_buzz.mdl");
	precache_model("progs/w_paxe.mdl");
	precache_model("progs/w_playergun.mdl");
	precache_model("progs/player_holes.mdl");
	precache_model("progs/gib_player_helmet.mdl");
	precache_model("progs/gib_player_head.mdl");
	precache_model("progs/gib_player_head_sng.mdl");
	precache_model("progs/gib_player_torso.mdl");
	precache_model("progs/gib_player_torso_sng.mdl");
	precache_model("progs/gib_player_torso_sng_b.mdl");
	precache_model("progs/gib_player_torso_head.mdl");
	precache_model("progs/gib_player_larm.mdl");
	precache_model("progs/gib_player_arm_sng.mdl");
	precache_model("progs/gib_player_legs.mdl");
	precache_model("progs/gib_minoleg1.mdl");
	precache_model("progs/gib_minoclaw1.mdl");
	precache_model("progs/gib_minoleg2.mdl");
	precache_model("progs/gib_minoclaw2.mdl");
	precache_model("progs/gib_hydra.mdl");
	if (autocvar_debris)
	{
		precache_model("progs/debris1.mdl");
		precache_model("progs/debris2.mdl");
		precache_model("progs/debris3.mdl");
		precache_model("progs/debris4.mdl");
		precache_model("progs/debris5.mdl");
		precache_model("progs/debris6.mdl");
		precache_model("progs/debris7.mdl");
		precache_model("progs/debris8.mdl");
		precache_model("progs/debris9.mdl");
		precache_model("progs/debris10.mdl");
	}
	precache_model("progs/s_bubble.spr");
	precache_model("progs/s_explod.spr");
	precache_model("progs/s_explodbigp.spr");
	precache_model("progs/s_explodbig.spr");
	precache_model("progs/s_explodmed.spr");
	precache_model("progs/proj_smoke.mdl");
	precache_model("progs/s_plasma.spr");
	precache_model("progs/muzzleflash1.spr");
	precache_model("progs/muzzleflash2.spr");
	precache_model("progs/muzzleflash3.spr");
	precache_model("progs/muzzleflash.spr");
	precache_model("progs/sng_muzz.spr");
	precache_model("progs/sng_muzz_b.spr");
	precache_model("progs/shot_muzz.spr");
	precache_model("progs/shot_muzz_b.spr");
	precache_model("progs/s_smoke_muzz.spr");
	precache_model("progs/s_spark_muzz.spr");
	precache_model("progs/s_gunsmoke.spr");
	precache_model("progs/v_axe.mdl");
	if ((autocvar_zombieaxeanimation == 1))
	{
		precache_model("progs/v_axe_zombie01.mdl");
		precache_model("progs/v_axe_zombie00.mdl");
	}
	precache_model("progs/v_shot.mdl");
	precache_model("progs/v_saw.mdl");
	precache_model("progs/v_nail.mdl");
	precache_model("progs/v_rock.mdl");
	precache_model("progs/v_shot2.mdl");
	precache_model("progs/v_nail2.mdl");
	precache_model("progs/v_rock2.mdl");
	precache_model("progs/v_laserg.mdl");
	precache_model("progs/proxbomb.mdl");
	precache_model("progs/g_prox.mdl");
	precache_model("progs/lasrspik.mdl");
	if (autocvar_centered_weapons)
	{
		precache_model("progs/centered/v_shot.mdl");
		precache_model("progs/centered/v_nail.mdl");
		precache_model("progs/centered/v_rock.mdl");
		precache_model("progs/centered/v_shot2.mdl");
		precache_model("progs/centered/v_nail2.mdl");
		precache_model("progs/centered/v_rock2.mdl");
		precache_model("progs/centered/v_light.mdl");
		precache_model("progs/centered/v_laserg.mdl");
		precache_model("progs/centered/v_nail2_barrel.mdl");
		precache_model("progs/centered/QC/v_shot2.mdl");
	}
	precache_model("progs/v_nail2_barrel.mdl");
	precache_model("progs/QC/v_shot2.mdl");
	precache_model("progs/s_smoke.spr");
	precache_model("progs/v_boot.mdl");
	precache_model("progs/v_nade.mdl");
	precache_model("progs/p_shot.md3");
	precache_model("progs/p_saw.md3");
	precache_model("progs/p_nail.md3");
	precache_model("progs/p_rock.md3");
	precache_model("progs/p_ssg.md3");
	precache_model("progs/QC/p_ssg.md3");
	precache_model("progs/p_nail2.md3");
	precache_model("progs/p_rock2.md3");
	precache_model("progs/p_light.md3");
	precache_model("progs/p_laser.md3");
	precache_model("progs/p_axe.md3");
	if (autocvar_weapon_position_right)
	{
		precache_model("progs/v_shot_right.mdl");
		precache_model("progs/v_nail_right.mdl");
		precache_model("progs/v_rock_right.mdl");
		precache_model("progs/v_shot2_right.mdl");
		precache_model("progs/v_nail2_right.mdl");
		precache_model("progs/v_rock2_right.mdl");
		precache_model("progs/v_light_right.mdl");
	}
	precache_model("progs/bolt.mdl");
	precache_model("progs/bolt2.mdl");
	precache_model("progs/bolt3.mdl");
	precache_model("progs/lavaball.mdl");
	precache_model("progs/missile.mdl");
	precache_model("progs/grenade.mdl");
	precache_model("progs/spike.mdl");
	precache_model("progs/bullettr.mdl");
	precache_model("progs/s_spike.mdl");
	precache_model("progs/hook.mdl");
	precache_model("progs/chain.mdl");
	precache_model("progs/backpack.mdl");
	precache_model("progs/wallsplat.mdl");
	precache_model("progs/v_light.mdl");
	precache_model("progs/v_mage1.mdl");
	lightstyle(0, "m");
	lightstyle(1, "mmnmmommommnonmmonqnmmo");
	lightstyle(2, "abcdefghijklmnopqrstuvwxyzyxwvutsrqponmlkjihgfedcba");
	lightstyle(3, "mmmmmaaaaammmmmaaaaaabcdefgabcdefg");
	lightstyle(4, "mamamamamama");
	lightstyle(5, "jklmnopqrstuvwxyzyxwvutsrqponmlkj");
	lightstyle(6, "nmonqnmomnmomomno");
	lightstyle(7, "mmmaaaabcdefgmmmmaaaammmaamm");
	lightstyle(8, "mmmaaammmaaammmabcdefaaaammmmabcdefmmmaaaa");
	lightstyle(9, "aaaaaaaazzzzzzzz");
	lightstyle(10, "mmamammmmammamamaaamammma");
	lightstyle(11, "abcdefghijklmnopqrrqponmlkjihgfedcba");
	lightstyle(63, "a");
	if (((autocvar_armor_model == 2) || (autocvar_key_icon == 1)))
	{
		foo = spawn();
		setmodel(foo, "progs/player.mdl");
		foo.customizeentityforclient = connect_me_with_client;
		foo.worldtype = world.worldtype;
		foo.SendEntity = SendWorldType;
		foo.SendFlags = (foo.SendFlags | 1);
	}
};

void() StartFrame =
{
	BotFrame();
	BM_StartFrame();
	CheckSplash();
	teamplay = autocvar_teamplay;
	skill = autocvar_skill;
	framecount = framecount + 1;
	Gyro_Run();
};

.entity bm_painskin;

void(entity attacker, float damage) bodyque_nopain =
{
};

void() bodyque_clear =
{
	self.delete_painskin = 1;
	if (self.bm_painskin && !bm_wasfreed(self.bm_painskin) && self.bm_painskin.owner == self)
		remove(self.bm_painskin);
	self.bm_painskin = world;
	if (self.classname != "bodyque")
	{
		remove(self);
		return;
	}
	self.i_am_a_corpse = 0;
	self.takedamage = DAMAGE_NO;
	self.solid = SOLID_NOT;
	self.movetype = MOVETYPE_NONE;
	self.touch = SUB_Null;
	self.th_die = SUB_Null;
	self.th_pain = bodyque_nopain;
	self.think = SUB_Null;
	self.nextthink = -1;
	self.semisolid = "n";
	self.model = string_null;
	self.modelindex = 0;
	self.traileffectnum = 0;
	self.alpha = 1;
	Gyro_Object_ClearPhysics(self);
};

void() bodyque =
{
};

void() InitBodyQue =
{
	local entity e;
	local entity prev;
	local float numBodies;
	local float num;

	numBodies = 32;
	num = 0;
	prev = world;
	bodyque_head = world;
	while ((num < numBodies))
	{
		e = spawn();
		e.classname = "bodyque";
		if ((bodyque_head == world))
		{
			bodyque_head = e;
		}
		if ((prev != world))
		{
			e.owner = prev;
		}
		prev = e;
		num = num + 1;
	}
	bodyque_head.owner = prev;
};

void() baked_explode =
{
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	ThrowBody("progs/coal.mdl", self.health);
	if (((((self.netname == "progs/h_spidbody.mdl") || (self.netname == "progs/h_dog.mdl")) || (self.netname == "progs/h_dog1.mdl")) || (self.netname == "progs/h_dog_extended.mdl")))
	{
		pointparticles(particleeffectnum(/*37082i*/"baked_explode_small"), self.origin, VEC_ORIGIN, 1);
	}
	else
	{
		if ((((((self.netname == "progs/h_shams.mdl") || (self.netname == "progs/h_shams1.mdl")) || (self.netname == "progs/h_spidbodyshamb.mdl")) || (self.netname == "progs/h_carnivean.mdl")) || (self.netname == "progs/h_yak.mdl")))
		{
			pointparticles(particleeffectnum(/*37139i*/"baked_explode_shambler"), self.origin, VEC_ORIGIN, 1);
		}
		else
		{
			if ((((((((((self.netname == "progs/h_demon.mdl") || (self.netname == "progs/h_demon1.mdl")) || (self.netname == "progs/h_hellkn.mdl")) || (self.netname == "progs/h_hellkn1.mdl")) || (self.netname == "progs/h_ogre.mdl")) || (self.netname == "progs/h_ogre1.mdl")) || (self.netname == "progs/h_shal.mdl")) || (self.netname == "progs/h_shal1.mdl")) || (self.netname == "progs/h_torment.mdl")))
			{
				pointparticles(particleeffectnum(/*37291i*/"baked_explode_large"), self.origin, VEC_ORIGIN, 1);
			}
			else
			{
				pointparticles(particleeffectnum(/*37311i*/"baked_explode"), self.origin, VEC_ORIGIN, 1);
			}
		}
	}
	sound(self, CHAN_AUTO, "ambience/coaled_monster_explode.wav", 1, ATTN_NORM);
	bodyque_clear();
};

void() touchBody =
{
	if (other.health)
	{
		self.owner = other;
	}
	if ((other == self.owner))
	{
		self.solid = SOLID_CORPSE;
	}
	else
	{
		self.solid = SOLID_SLIDEBOX;
	}
};

void() bodyCheck =
{
	pitch_roll_for_slope(VEC_ORIGIN);
};

void(entity ent, float hp, string headmdl) CopyToBodyQue =
{
	local vector minsiz;
	local vector maxsiz;
	local entity pain_skin_entity;

	pitch_roll_for_slope(VEC_ORIGIN);
	spawn_bloodpool(1);
	// Clean up any previous pain_skin_entity attached to this bodyque slot before recycling it (VEH-23)
	if (bodyque_head.bm_painskin && !bm_wasfreed(bodyque_head.bm_painskin) && bodyque_head.bm_painskin.owner == bodyque_head)
		remove(bodyque_head.bm_painskin);
	bodyque_head.bm_painskin = world;
	bodyque_head.delete_painskin = 0;
	bodyque_head.i_am_a_corpse = 1;
	bodyque_head.sizediff = self.sizediff;
	bodyque_head.painskin_helper = self.painskin_helper;
	bodyque_head.baked = self.baked;
	bodyque_head.skin = self.skin;
	bodyque_head.colormod = self.colormod;
	bodyque_head.traileffectnum = self.traileffectnum;
	bodyque_head.burnable_corpse = self.burnable_corpse;
	bodyque_head.original_frame = self.frame;
	bodyque_head.enemy = self.enemy;
	bodyque_head.scale = self.scale;
	if ((random() < 0.5))
	{
		bodyque_head.spin_direction = 0;
	}
	else
	{
		bodyque_head.spin_direction = 1;
	}
	bodyque_head.angles = ent.angles;
	bodyque_head.model = ent.model;
	bodyque_head.modelindex = ent.modelindex;
	bodyque_head.frame = ent.frame;
	bodyque_head.colormap = ent.colormap;
	bodyque_head.touch = bodyCheck;
	bodyque_head.velocity = ent.velocity;
	bodyque_head.flags = 0;
	setorigin(bodyque_head, ent.origin);
	minsiz = ent.mins;
	maxsiz = ent.maxs;
	if ((bodyque_head.baked != 1))
	{
	}
	setsize(bodyque_head, minsiz, maxsiz);
	Gyro_Object_ClearPhysics(self);
	Gyro_Object_ClearPhysics(bodyque_head);
	if ((autocvar_gyroset > 0))
	{
		Gyro_Object_Activate(bodyque_head, autocvar_corpsemass);
	}
	if (!(self.classname == "player"))
	{
		bodyque_head.health = hp;
		if ((hp == 0))
		{
			bodyque_head.takedamage = 0;
			bodyque_head.solid = 0;
		}
		else
		{
			bodyque_head.takedamage = DAMAGE_AIM;
			bodyque_head.solid = SOLID_SLIDEBOX;
		}
		if ((bodyque_head.baked == 1))
		{
			bodyque_head.th_die = baked_explode;
			bodyque_head.nextthink = (time + autocvar_coaled_monster_lifetime);
			bodyque_head.think = baked_explode;
		}
		else
		{
			bodyque_head.th_die = corpse_die;
			if (autocvar_monster_blood_puddles)
			{
				if (((((headmdl == "progs/h_spidbody.mdl") || (headmdl == "progs/h_dog.mdl")) || (headmdl == "progs/h_dog1.mdl")) || (headmdl == "progs/h_dog_extended.mdl")))
				{
					bodyque_head.create_blood_puddle = (time + 0.2);
				}
				else
				{
					if ((((((headmdl == "progs/h_shams.mdl") || (headmdl == "progs/h_shams1.mdl")) || (headmdl == "progs/h_spidbodyshamb.mdl")) || (headmdl == "progs/h_carnivean.mdl")) || (headmdl == "progs/h_yak.mdl")))
					{
						bodyque_head.create_blood_puddle = (time + 1.2);
					}
					else
					{
						if ((((((((((headmdl == "progs/h_demon.mdl") || (headmdl == "progs/h_demon1.mdl")) || (headmdl == "progs/h_hellkn.mdl")) || (headmdl == "progs/h_hellkn1.mdl")) || (headmdl == "progs/h_ogre.mdl")) || (headmdl == "progs/h_ogre1.mdl")) || (headmdl == "progs/h_shal.mdl")) || (headmdl == "progs/h_shal1.mdl")) || (headmdl == "progs/h_torment.mdl")))
						{
							bodyque_head.create_blood_puddle = (time + 1.2);
						}
						else
						{
							bodyque_head.create_blood_puddle = (time + 0.7);
						}
					}
				}
			}
			if (autocvar_painskin_transparency)
			{
				pain_skin_entity = spawn();
				bodyque_head.bm_painskin = pain_skin_entity;
				pain_skin_entity.solid = 0;
				pain_skin_entity.movetype = MOVETYPE_NOCLIP;
				pain_skin_entity.owner = bodyque_head;
				setmodel(pain_skin_entity, bodyque_head.model);
				setsize(pain_skin_entity, (VEC_HULL2_MIN - bodyque_head.sizediff), (VEC_HULL2_MAX - bodyque_head.sizediff));
				setorigin(pain_skin_entity, VEC_ORIGIN);
				pain_skin_entity.skin = bodyque_head.skin;
				pain_skin_entity.colormod_x = bodyque_head.colormod_x;
				pain_skin_entity.colormod_y = bodyque_head.colormod_y;
				pain_skin_entity.colormod_z = bodyque_head.colormod_z;
				pain_skin_entity.frame = bodyque_head.frame;
				pain_skin_entity.painskin_helper = bodyque_head.painskin_helper;
				pain_skin_entity.alpha = autocvar_painskin_transparency;
				pain_skin_entity.think = pain_skin_entity_corpse_think;
				pain_skin_entity.nextthink = time;
				local float ti;
				ti = gettagindex(bodyque_head, "test");
				if ((ti > 0))
					setattachment(pain_skin_entity, bodyque_head, /*37325i*/"test");
				else
					setattachment(pain_skin_entity, bodyque_head, "");
			}
		}
		bodyque_head.th_pain = corpse_pain;
		bodyque_head.semisolid = "y";
		has_semisolids = 1;
	}
	bodyque_head.movetype = MOVETYPE_STEP;
	bodyque_head.netname = headmdl;
	bodyque_head = bodyque_head.owner;
	bodyque_head.solid = SOLID_CORPSE;
	if ((bodyque_head.model == "progs/player_torso.mdl"))
	{
		bodyque_head.movetype = 0;
	}
};

void() rigged =
{
	local entity missile;

	if ((self.enemy.flags & FL_CLIENT))
	{
		if ((!visible(self.enemy) && (vlen((self.origin - self.enemy.origin)) > 768)))
		{
			missile = spawn();
			missile.owner = self;
			missile.movetype = MOVETYPE_BOUNCE;
			missile.solid = SOLID_BBOX;
			missile.velocity = vecrand(200, 400, TRUE);
			missile.avelocity = '300 300 300';
			missile.velocity_z = 300;
			missile.classname = "proximity_grenade";
			missile.touch = ProximityGrenadeTouch;
			missile.health = 5;
			missile.state = 0;
			missile.scale = 0.9;
			missile.nextthink = (time + 2);
			missile.delay = ((time + 9999) + (10 * random()));
			missile.think = ProximityBomb;
			missile.th_die = ProximityGrenadeExplode;
			setmodel(missile, "progs/proxbomb.mdl");
			setsize(missile, VEC_ORIGIN, VEC_ORIGIN);
			setorigin(missile, (self.origin + '0 0 10'));
		}
	}
	self.think = SUB_Null;
};

void(float hp, string headmdl) CopyMonsterToBodyQue =
{
	CopyToBodyQue(self, hp, headmdl);
	self.model = "";
	self.think = SUB_Null;
	if ((random() < 0.01))
	{
		if ((world.worldtype == 2))
		{
			self.think = rigged;
			self.nextthink = ((time + 40) + (random() * 30));
		}
	}
};

void(float maxgibs, float gibscounter) producegibs_corpse =
{
	if ((gibscounter >= maxgibs))
	{
		return;
	}
	else
	{
		if ((self.netname == "progs/h_spidbody.mdl"))
		{
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
			ThrowGibSpider("progs/gib_spidlegb.mdl", self.health);
		}
		else
		{
			if ((self.netname == "progs/h_spidbodyshamb.mdl"))
			{
				ThrowGibSpider("progs/gib_spidlegshamb.mdl", self.health);
				ThrowGibSpider("progs/gib_spidlegshamb.mdl", self.health);
			}
			else
			{
				if ((self.netname == "progs/h_knight.mdl"))
				{
					ThrowGib("progs/gib_knfoot_r.mdl", self.health);
					ThrowGib("progs/gib_knfoot_l.mdl", self.health);
					ThrowWeapon("progs/w_knightsword.mdl", self.health);
				}
				else
				{
					if ((self.netname == "progs/gib_voreleg.mdl"))
					{
						ThrowGib("progs/gib_voreleg.mdl", self.health);
						ThrowGib("progs/gib_voreleg.mdl", self.health);
					}
					else
					{
						if ((self.netname == "progs/gib_knfoot_l.mdl"))
						{
							ThrowGib("progs/gib_knfoot_r.mdl", self.health);
							ThrowWeapon("progs/w_knightsword.mdl", self.health);
						}
						else
						{
							if ((self.netname == "progs/gib_knfoot_r.mdl"))
							{
								ThrowGib("progs/gib_knfoot_l.mdl", self.health);
								ThrowWeapon("progs/w_knightsword.mdl", self.health);
							}
							else
							{
								if ((self.netname == "progs/h_guard.mdl"))
								{
									ThrowGib("progs/gib_soldarm.mdl", self.health);
									ThrowGib("progs/gib_soldfoot1.mdl", self.health);
									ThrowGib("progs/gib_soldfoot2.mdl", self.health);
									ThrowWeapon("progs/w_soldiergun.mdl", self.health);
								}
								else
								{
									if ((self.netname == "progs/h_guard1.mdl"))
									{
										ThrowGib("progs/gib_soldarm.mdl", self.health);
										ThrowGib("progs/gib_soldfoot1.mdl", self.health);
										ThrowGib("progs/gib_soldfoot2.mdl", self.health);
										ThrowWeapon("progs/w_soldiergun.mdl", self.health);
									}
									else
									{
										if ((self.netname == "progs/gib_soldfoot1.mdl"))
										{
											ThrowGib("progs/gib_soldarm.mdl", self.health);
											ThrowGib("progs/gib_soldfoot2.mdl", self.health);
											ThrowWeapon("progs/w_soldiergun.mdl", self.health);
										}
										else
										{
											if ((self.netname == "progs/gib_soldfoot2.mdl"))
											{
												ThrowGib("progs/gib_soldarm.mdl", self.health);
												ThrowGib("progs/gib_soldfoot1.mdl", self.health);
											}
											else
											{
												if ((self.netname == "progs/w_soldiergun.mdl"))
												{
													ThrowGib("progs/gib_soldfoot2.mdl", self.health);
													ThrowGib("progs/gib_soldfoot1.mdl", self.health);
												}
												else
												{
													if ((self.netname == "progs/h_dog.mdl"))
													{
														ThrowGib("progs/gib_dogleg.mdl", self.health);
														ThrowGib("progs/gib_dogleg.mdl", self.health);
													}
													else
													{
														if ((self.netname == "progs/h_mega.mdl"))
														{
															ThrowGib("progs/gib_enforcer_larm.mdl", self.health);
															ThrowGib("progs/gib_enforcer_rarm.mdl", self.health);
															ThrowWeapon("progs/gib_enforcer_pack.mdl", self.health);
															ThrowGib("progs/gib_soldfoot1.mdl", self.health);
															ThrowGib("progs/gib_soldfoot1.mdl", self.health);
														}
														else
														{
															if ((self.netname == "progs/gib_enforcer_rarm.mdl"))
															{
																ThrowWeapon("progs/w_enforcergun.mdl", self.health);
																ThrowGib("progs/gib_enforcer_rarm.mdl", self.health);
																ThrowGib("progs/gib_enforcer_legs.mdl", self.health);
															}
															else
															{
																if ((self.netname == "progs/gib_enforcer_larm.mdl"))
																{
																	ThrowWeapon("progs/w_enforcergun.mdl", self.health);
																	ThrowWeapon("progs/gib_enforcer_pack.mdl", self.health);
																	ThrowGib("progs/gib_enforcer_torso.mdl", self.health);
																	ThrowGib("progs/gib_soldfoot1.mdl", self.health);
																	ThrowGib("progs/gib_soldfoot2.mdl", self.health);
																}
																else
																{
																	if ((self.netname == "progs/gib_enforcer_head.mdl"))
																	{
																		ThrowGib("progs/gib_enforcer_rarm.mdl", self.health);
																		ThrowGib("progs/gib_enforcer_larm.mdl", self.health);
																		ThrowGib("progs/gib_enforcer_torso.mdl", self.health);
																		ThrowGib("progs/gib_enforcer_legs.mdl", self.health);
																	}
																	else
																	{
																		if ((self.netname == "progs/w_enforcergun.mdl"))
																		{
																			ThrowGib("progs/gib_enforcer_rarm.mdl", self.health);
																			ThrowGib("progs/gib_enforcer_rarm.mdl", self.health);
																			ThrowGib("progs/gib_soldfoot1.mdl", self.health);
																			ThrowGib("progs/gib_soldfoot2.mdl", self.health);
																		}
																		else
																		{
																			if ((self.netname == "progs/gib_ogre_h.mdl"))
																			{
																				ThrowGib("progs/chop.mdl", self.health);
																				ThrowGib("progs/chop.mdl", self.health);
																				ThrowGib("progs/chop.mdl", self.health);
																				ThrowGib("progs/gib_freddie_arm_sng.mdl", self.health);
																				ThrowGib("progs/gib_freddie_arm_saw.mdl", self.health);
																				ThrowHead("progs/gib_ogre_h.mdl", self.health);
																				ThrowWeapon("progs/gib_freddie_leg.mdl", self.health);
																				ThrowWeapon("progs/gib_freddie_leg.mdl", self.health);
																			}
																			else
																			{
																				if ((self.netname == "progs/h_wizard.mdl"))
																				{
																					ThrowGib("progs/gib_wzarm1.mdl", self.health);
																					ThrowGib("progs/gib_wzarm1.mdl", self.health);
																					ThrowGib("progs/gib_wztail.mdl", self.health);
																				}
																				else
																				{
																					if ((self.netname == "progs/gib_wztail.mdl"))
																					{
																						ThrowGib("progs/gib_wzarm1.mdl", self.health);
																					}
																					else
																					{
																						if ((self.netname == "progs/h_ogre.mdl"))
																						{
																							ThrowGib("progs/gib_ogfoot1.mdl", self.health);
																							ThrowGib("progs/gib_ogfoot2.mdl", self.health);
																							ThrowWeapon("progs/w_chainsaw.mdl", self.health);
																							ThrowWeapon("progs/w_ogregl.mdl", self.health);
																						}
																						else
																						{
																							if ((self.netname == "progs/h_ogre1.mdl"))
																							{
																								ThrowGib("progs/gib_ogfoot1.mdl", self.health);
																								ThrowGib("progs/gib_ogfoot2.mdl", self.health);
																								ThrowWeapon("progs/w_chainsaw.mdl", self.health);
																								ThrowWeapon("progs/w_ogregl.mdl", self.health);
																							}
																							else
																							{
																								if ((self.netname == "progs/gib_ogfoot1.mdl"))
																								{
																									ThrowGib("progs/gib_ogfoot2.mdl", self.health);
																									ThrowWeapon("progs/w_chainsaw.mdl", self.health);
																									ThrowWeapon("progs/w_ogregl.mdl", self.health);
																								}
																								else
																								{
																									if ((self.netname == "progs/gib_ogfoot2.mdl"))
																									{
																										ThrowGib("progs/gib_ogfoot1.mdl", self.health);
																										ThrowGib("progs/gib3.mdl", self.health);
																										ThrowGib("progs/gib3.mdl", self.health);
																										ThrowGib("progs/gib_ogre_h.mdl", self.health);
																										ThrowWeapon("progs/w_ogregl.mdl", self.health);
																									}
																									else
																									{
																										if ((self.netname == "progs/h_afrit.mdl"))
																										{
																											if ((self.alpha < 0.6))
																											{
																												ThrowGib("progs/gib_afrit.mdl", (self.health * 1.7));
																												ThrowGib("progs/gib_afrit.mdl", (self.health * 1.7));
																												ThrowGib("progs/chop.mdl", (self.health * 1.6));
																												ThrowGib("progs/chop.mdl", (self.health * 1.6));
																												ThrowHead("progs/h_afrit.mdl", (self.health * 1.7));
																											}
																											else
																											{
																												ThrowGib("progs/gib_gargwing2.mdl", self.health);
																												ThrowGib("progs/gib_afrit.mdl", self.health);
																												ThrowGib("progs/gib_afrit.mdl", self.health);
																												ThrowGib("progs/chop.mdl", self.health);
																												ThrowGib("progs/chop.mdl", self.health);
																												ThrowGib("progs/chop.mdl", self.health);
																												ThrowHead("progs/h_afrit.mdl", self.health);
																											}
																										}
																										else
																										{
																											if ((self.netname == "progs/h_hellkn.mdl"))
																											{
																												ThrowGib("progs/gib_knfoot_r.mdl", self.health);
																												ThrowGib("progs/gib_knfoot_l.mdl", self.health);
																												ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
																												ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
																												ThrowWeapon("progs/w_dknightsword.mdl", self.health);
																											}
																											else
																											{
																												if ((self.netname == "progs/gib_hknight_head.mdl"))
																												{
																													ThrowGib("progs/gib_knfoot_r.mdl", self.health);
																													ThrowGib("progs/gib_knfoot_l.mdl", self.health);
																													ThrowGib("progs/gib_hknight_larm.mdl", self.health);
																													ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
																												}
																												else
																												{
																													if ((self.netname == "progs/gib_hknight_larm.mdl"))
																													{
																														ThrowGib("progs/gib_knfoot_r.mdl", self.health);
																														ThrowGib("progs/gib_knfoot_l.mdl", self.health);
																														ThrowGib("progs/gib_hknight_torso.mdl", self.health);
																														ThrowGib("progs/gib_hknight_head.mdl", self.health);
																														ThrowGib("progs/gib_hknight_rarm.mdl", self.health);
																													}
																													else
																													{
																														if ((self.netname == "progs/gib3.mdl"))
																														{
																															ThrowGib("progs/gib_knfoot_r.mdl", self.health);
																															ThrowGib("progs/gib_knfoot_l.mdl", self.health);
																														}
																														else
																														{
																															if ((self.netname == "progs/h_warlord.mdl"))
																															{
																																ThrowGib("progs/gib_wararm.mdl", self.health);
																																ThrowGib("progs/gib_warleg.mdl", self.health);
																																ThrowGib("progs/gib_warleg.mdl", self.health);
																																ThrowWeapon("progs/w_wshield.mdl", self.health);
																															}
																															else
																															{
																																if ((self.netname == "progs/gib_warnail_t.mdl"))
																																{
																																	ThrowWeapon("progs/w_wsword.mdl", self.health);
																																	ThrowGib("progs/gib_warleg.mdl", self.health);
																																	ThrowGib("progs/gib_warleg.mdl", self.health);
																																	ThrowWeapon("progs/w_wshield.mdl", self.health);
																																}
																																else
																																{
																																	if ((self.netname == "progs/gib_warleg.mdl"))
																																	{
																																		ThrowGib("progs/gib_warleg.mdl", self.health);
																																		ThrowWeapon("progs/w_wshield.mdl", self.health);
																																	}
																																	else
																																	{
																																		if ((self.netname == "progs/gib_warleg1.mdl"))
																																		{
																																			ThrowGib("progs/gib_warleg.mdl", self.health);
																																		}
																																		else
																																		{
																																			if ((self.netname == "progs/h_demon.mdl"))
																																			{
																																				ThrowGib("progs/gib_dmclaw1.mdl", self.health);
																																				ThrowGib("progs/gib_dmclaw2.mdl", self.health);
																																				ThrowGib("progs/gib_dmleg1.mdl", self.health);
																																				ThrowGib("progs/gib_dmleg2.mdl", self.health);
																																			}
																																			else
																																			{
																																				if ((self.netname == "progs/h_demon1.mdl"))
																																				{
																																					ThrowGib("progs/gib_dmclaw1.mdl", self.health);
																																					ThrowGib("progs/gib_dmclaw2.mdl", self.health);
																																					ThrowGib("progs/gib_dmleg1.mdl", self.health);
																																					ThrowGib("progs/gib_dmleg2.mdl", self.health);
																																					ThrowGib("progs/gib_dmtail.mdl", self.health);
																																				}
																																				else
																																				{
																																					if ((self.netname == "progs/h_demon1.mdl"))
																																					{
																																						ThrowGib("progs/gib_dmclaw1.mdl", self.health);
																																						ThrowGib("progs/gib_dmclaw2.mdl", self.health);
																																						ThrowGib("progs/gib_dmleg1.mdl", self.health);
																																						ThrowGib("progs/gib_dmleg2.mdl", self.health);
																																						ThrowGib("progs/gib_dmtail.mdl", self.health);
																																					}
																																					else
																																					{
																																						if ((self.netname == "progs/gib_dmclaw1.mdl"))
																																						{
																																							ThrowGib("progs/gib_dmclaw2.mdl", self.health);
																																							ThrowGib("progs/gib_dmleg1.mdl", self.health);
																																							ThrowGib("progs/gib_dmleg2.mdl", self.health);
																																							ThrowGib("progs/gib_dmtail.mdl", self.health);
																																						}
																																						else
																																						{
																																							if ((self.netname == "progs/h_shams.mdl"))
																																							{
																																								ThrowGib("progs/gib_shclaw1.mdl", self.health);
																																								ThrowGib("progs/gib_shclaw2.mdl", self.health);
																																								ThrowGib("progs/gib_shfoot1.mdl", self.health);
																																								ThrowGib("progs/gib_shfoot2.mdl", self.health);
																																							}
																																							else
																																							{
																																								if ((self.netname == "progs/h_yak.mdl"))
																																								{
																																									ThrowGib("progs/gib_minoclaw1.mdl", self.health);
																																									ThrowGib("progs/gib_minoclaw2.mdl", self.health);
																																									ThrowGib("progs/gib_minoleg1.mdl", self.health);
																																									ThrowGib("progs/gib_minoleg2.mdl", self.health);
																																								}
																																								else
																																								{
																																									if ((self.netname == "progs/h_shal.mdl"))
																																									{
																																										ThrowGib("progs/gib_shalleg.mdl", self.health);
																																										ThrowGib("progs/gib_shalleg.mdl", self.health);
																																										ThrowGib("progs/gib_shalleg.mdl", self.health);
																																										ThrowGib("progs/gib_shalclaw.mdl", self.health);
																																										ThrowGib("progs/gib_shalclaw.mdl", self.health);
																																									}
																																									else
																																									{
																																										if ((self.netname == "progs/h_scourg.mdl"))
																																										{
																																											ThrowGib("progs/gib_scclaw.mdl", self.health);
																																											ThrowGib("progs/gib_scclaw.mdl", self.health);
																																											ThrowGib("progs/gib_scorpleg.mdl", self.health);
																																											ThrowGib("progs/gib_scorpleg.mdl", self.health);
																																											ThrowGib("progs/gib_scorpleg.mdl", self.health);
																																											ThrowGib("progs/gib_scorpleg.mdl", self.health);
																																											ThrowGib("progs/gib_sctail.mdl", self.health);
																																										}
																																										else
																																										{
																																											ThrowGib("progs/gib_4.mdl", self.health);
																																											ThrowGib("progs/gib_5.mdl", self.health);
																																										}
																																									}
																																								}
																																							}
																																						}
																																					}
																																				}
																																			}
																																		}
																																	}
																																}
																															}
																														}
																													}
																												}
																											}
																										}
																									}
																								}
																							}
																						}
																					}
																				}
																			}
																		}
																	}
																}
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	gibscounter = gibscounter + 1;
	producegibs_corpse(maxgibs, gibscounter);
};

void(string gibname, float dm) removehead =
{
	self.nextthink = (time + 0.001);
	self.think = bodyque_clear;
};

void() pentagram_touch_delay =
{
	self.touch = pentagram_touch;
	self.nextthink = (time + 20);
	self.think = SUB_Remove;
};

void() pentagram_touch =
{
	local string s;

	if ((other.classname != "player"))
	{
		return;
	}
	self.touch = SUB_Null;
	if (autocvar_corpseburnpentagram_health)
	{
		self.healamount_old = self.healamount;
		if (T_Heal(other, self, 0))
		{
			sound(self, CHAN_VOICE, "zombie/penttouch.wav", 1, ATTN_NORM);
			te_customflash((self.origin + '0 0 25'), 666, 0.7, '1 0 0');
			if (autocvar_lossless_health_pickup)
			{
				sprint(other, "You received ");
				if (!self.crate_is_empty)
				{
					s = ftos((self.healamount_old - self.healamount));
				}
				else
				{
					s = ftos(self.healamount_old);
				}
				sprint(other, s);
				sprint(other, " health");
				if (!self.crate_is_empty)
				{
					sprint(other, ". Max health reached. ");
					s = ftos(self.healamount);
					sprint(other, s);
					sprint(other, " health remaining.");
				}
				sprint(other, "\n");
			}
			else
			{
				sprint(other, "You receive ");
				s = ftos(self.healamount);
				sprint(other, s);
				sprint(other, " health\n");
			}
		}
		else
		{
			sprint(other, "You already have max. health.\n");
		}
		if (autocvar_lossless_health_pickup)
		{
			if ((self.crate_is_empty == 1))
			{
				self.nextthink = (time + 0.01);
				self.think = SUB_Remove;
			}
			else
			{
				self.touch = SUB_Null;
				self.nextthink = (time + 1.5);
				self.think = pentagram_touch_delay;
			}
		}
		else
		{
			sound(self, CHAN_VOICE, "zombie/penttouch.wav", 1, ATTN_NORM);
			te_customflash((self.origin + '0 0 25'), 666, 0.7, '1 0 0');
			self.nextthink = (time + 0.01);
			self.think = SUB_Remove;
		}
	}
	else
	{
		sound(self, CHAN_VOICE, "zombie/penttouch.wav", 1, ATTN_NORM);
		te_customflash((self.origin + '0 0 25'), 666, 0.7, '1 0 0');
		self.nextthink = (time + 0.01);
		self.think = SUB_Remove;
	}
};

void() control_position_pentagram =
{
	self.origin = (self.origin - '0 0 0.06');
	self.pent_counter = (self.pent_counter + 1);
	if ((self.pent_counter >= 16))
	{
		remove(self);
		return;
	}
	self.nextthink = (time + 1.3);
	self.think = control_position_pentagram;
};

void() spawn_corpse_pentagram =
{
	local entity pentagram;

	pentagram = spawn();
	pentagram.movetype = MOVETYPE_FLY;
	pentagram.solid = SOLID_TRIGGER;
	pentagram.velocity = '0 0 0.05';
	pentagram.avelocity = '0 40 0';
	pentagram.scale = 0.75;
	pentagram.touch = pentagram_touch;
	setmodel(pentagram, "progs/corpse_pent.mdl");
	setsize(pentagram, '-10 -10 -18', '10 10 40');
	setorigin(pentagram, (self.origin - '0 0 37'));
	pentagram.traileffectnum = particleeffectnum(/*38518i*/"corpse_pentagram");
	pentagram.healamount = autocvar_corpseburnpentagram_health;
	pentagram.initial_amount = self.healamount;
	pentagram.nextthink = (time + 0.1);
	pentagram.think = control_position_pentagram;
	sound(self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
	self.nextthink = (time + 0.01);
	self.think = bodyque_clear;
};

void() corpse_fade =
{
	local float countdown;

	self.magiccounter = (self.magiccounter - 1);
	if (autocvar_corpseburntime > 0)
		countdown = 1 / (autocvar_corpseburntime * 12);
	else
		countdown = 1;
	if ((self.magiccounter >= 0))
	{
		self.alpha = (self.alpha - countdown);
		self.think = corpse_fade;
		self.nextthink = (time + 0.1);
	}
	else
	{
		if ((autocvar_corpseburnpentagram == 1))
		{
			self.think = spawn_corpse_pentagram;
			self.nextthink = time;
		}
		else
		{
			sound(self, CHAN_WEAPON, "misc/null.wav", 1, ATTN_NORM);
			self.think = bodyque_clear;
			self.nextthink = time;
		}
	}
};

void() corpse_die =
{
	local float maxgibs;
	local float gibscounter;
	local vector check;

	self.delete_painskin = 1;
	if ((self.netname != "progs/gib_voreleg.mdl"))
	{
		sound7(self, CHAN_VOICE, "misc/corpsegib.wav", 1, ATTN_NORM, SNDSPD);
	}
	else
	{
		sound7(self, CHAN_VOICE, "misc/megagib.wav", 1, ATTN_NORM, SNDSPD);
	}
	self.semisolid = "n";
	if ((self.netname == "newzombie"))
	{
		self.netname = "progs/h_zombie_new.mdl";
		check = (self.origin - '0 0 20') + '0 0 1';
		if ((((autocvar_zombienewmodelburnable == 1) && (pointcontents(check) != CONTENT_WATER)) && (pointcontents(check) != CONTENT_SLIME)))
		{
			if (autocvar_corpseburntime)
			{
				self.traileffectnum = particleeffectnum(/*12498i*/"corpse_burn");
			}
			self.colormod = '0.4 0.25 0.25';
			sound(self, CHAN_VOICE, "zombie/corpse_lit.wav", 1, ATTN_NORM);
			sound(self, CHAN_WEAPON, "zombie/corpse_fire.wav", 1, ATTN_NORM);
			self.alpha = 1;
			self.magiccounter = (autocvar_corpseburntime * 10);
			self.think = corpse_fade;
			self.nextthink = time;
			return;
		}
		else
		{
			if ((autocvar_slowmotion >= 2))
			{
				if ((random() <= (autocvar_slowmotion_randomness_corpse * 0.01)))
				{
					the_matrix = 1;
					matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
				}
			}
			self.scale = 1.4;
			if ((autocvar_gibsmultiplier == 1))
			{
				ThrowHead(self.netname, self.health);
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
				}
				return;
			}
			else
			{
				ThrowHead(self.netname, self.health);
				if ((autocvar_bloodextension == 1))
				{
					pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
				}
				maxgibs = autocvar_gibsmultiplier;
				gibscounter = 0;
				producegibs_corpse(maxgibs, gibscounter);
				return;
			}
		}
	}
	else
	{
		if ((self.netname == "newzombieheadless"))
		{
			self.netname = "progs/h_zombie_new.mdl";
			check = (self.origin - '0 0 20') + '0 0 1';
			if ((((autocvar_zombienewmodelburnable == 1) && (pointcontents(check) != CONTENT_WATER)) && (pointcontents(check) != CONTENT_SLIME)))
			{
				if (autocvar_corpseburntime)
				{
					self.traileffectnum = particleeffectnum(/*12498i*/"corpse_burn");
				}
				self.colormod = '0.4 0.25 0.25';
				sound(self, CHAN_VOICE, "zombie/corpse_lit.wav", 1, ATTN_NORM);
				sound(self, CHAN_WEAPON, "zombie/corpse_fire.wav", 1, ATTN_NORM);
				self.alpha = 1;
				self.magiccounter = (autocvar_corpseburntime * 10);
				self.think = corpse_fade;
				self.nextthink = time;
				return;
			}
			else
			{
				if ((autocvar_slowmotion >= 2))
				{
					if ((random() <= (autocvar_slowmotion_randomness_corpse * 0.01)))
					{
						the_matrix = 1;
						matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
					}
				}
				if ((autocvar_gibsmultiplier == 1))
				{
					removehead(self.netname, self.health);
					ThrowGib("progs/gib1.mdl", self.health);
					ThrowGib("progs/gib2.mdl", self.health);
					ThrowGib("progs/gib3.mdl", self.health);
					if ((autocvar_bloodextension == 1))
					{
						pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
					}
					return;
				}
				else
				{
					removehead(self.netname, self.health);
					if ((autocvar_bloodextension == 1))
					{
						pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
					}
					maxgibs = autocvar_gibsmultiplier;
					gibscounter = 0;
					producegibs_corpse(maxgibs, gibscounter);
					return;
				}
			}
		}
	}
	check = (self.origin - '0 0 20') + '0 0 1';
	if ((((self.burnable_corpse == 1) && (pointcontents(check) != CONTENT_WATER)) && (pointcontents(check) != CONTENT_SLIME)))
	{
		if (autocvar_corpseburntime)
		{
			self.traileffectnum = particleeffectnum(/*12498i*/"corpse_burn");
		}
		self.colormod = '0.4 0.25 0.25';
		sound(self, CHAN_VOICE, "zombie/corpse_lit.wav", 1, ATTN_NORM);
		sound(self, CHAN_WEAPON, "zombie/corpse_fire.wav", 1, ATTN_NORM);
		self.alpha = 1;
		self.frame = self.original_frame;
		self.magiccounter = (autocvar_corpseburntime * 10);
		self.think = corpse_fade;
		self.nextthink = time;
		return;
	}
	else
	{
		if ((autocvar_slowmotion >= 2))
		{
			if ((random() <= (autocvar_slowmotion_randomness_corpse * 0.01)))
			{
				the_matrix = 1;
				matrixcounter = time + (autocvar_slowmotion_intensity * autocvar_slowmotion_duration);
			}
		}
		ThrowHead(self.netname, self.health);
		if (((autocvar_bloodextension == 1) && (self.netname != "progs/gib_voreleg.mdl")))
		{
			pointparticles(particleeffectnum(/*38568i*/"blood_corpse_gib"), self.origin, VEC_ORIGIN, 1);
		}
		if (((((self.netname != "progs/h_spidbody.mdl") && (self.netname != "progs/h_spidbodyshamb.mdl")) && (self.netname != "progs/gib_voreleg.mdl")) && (self.netname != "progs/gib3.mdl")))
		{
			if ((autocvar_heartgib == 2))
			{
				ThrowGib("progs/gibheart.mdl", self.health);
			}
			else
			{
				if ((autocvar_heartgib == 3))
				{
					ThrowHeart("progs/gibheart.mdl", self.health);
				}
			}
		}
		maxgibs = autocvar_gibsmultiplier;
		gibscounter = 0;
		producegibs_corpse(maxgibs, gibscounter);
		return;
	}
	self.takedamage = 0;
	self.th_die = SUB_Null;
};

void() corpse_pain =
{
	local float zuf;

	if ((autocvar_corpsekillexplosives == 1))
	{
		self.health = 60;
	}
	if (autocvar_monster_blood_puddles)
	{
		if (((((self.netname == "progs/h_spidbody.mdl") || (self.netname == "progs/h_dog.mdl")) || (self.netname == "progs/h_dog1.mdl")) || (self.netname == "progs/h_dog_extended.mdl")))
		{
			self.create_blood_puddle = (time + 1.2);
		}
		else
		{
			if ((((((self.netname == "progs/h_shams.mdl") || (self.netname == "progs/h_shams1.mdl")) || (self.netname == "progs/h_spidbodyshamb.mdl")) || (self.netname == "progs/h_carnivean.mdl")) || (self.netname == "progs/h_yak.mdl")))
			{
				self.create_blood_puddle = (time + 2.1);
			}
			else
			{
				if ((((((((((self.netname == "progs/h_demon.mdl") || (self.netname == "progs/h_demon1.mdl")) || (self.netname == "progs/h_hellkn.mdl")) || (self.netname == "progs/h_hellkn1.mdl")) || (self.netname == "progs/h_ogre.mdl")) || (self.netname == "progs/h_ogre1.mdl")) || (self.netname == "progs/h_shal.mdl")) || (self.netname == "progs/h_shal1.mdl")) || (self.netname == "progs/h_torment.mdl")))
				{
					self.create_blood_puddle = (time + 1.6);
				}
				else
				{
					self.create_blood_puddle = (time + 1.4);
				}
			}
		}
		self.create_blood_puddle_counter = 0;
	}
	if (((autocvar_ragdoll == 1) && (self.netname != "progs/h_afrit.mdl")))
	{
		if ((self.frame == self.original_frame))
		{
			self.frame = (self.original_frame - 1);
		}
		else
		{
			if ((self.frame == (self.original_frame - 1)))
			{
				self.frame = self.original_frame;
			}
			else
			{
				if ((self.frame == (self.original_frame - 2)))
				{
					self.frame = (self.original_frame - 1);
				}
			}
		}
	}
	else
	{
		if (((autocvar_ragdoll == 2) && (self.netname != "progs/h_afrit.mdl")))
		{
			if ((self.frame == self.original_frame))
			{
				zuf = random();
				if ((zuf > 0.7))
				{
					self.frame = (self.original_frame - 1);
				}
				else
				{
					self.frame = (self.original_frame - 2);
				}
			}
			else
			{
				if ((self.frame == (self.original_frame - 1)))
				{
					zuf = random();
					if ((zuf > 0.5))
					{
						self.frame = self.original_frame;
					}
					else
					{
						self.frame = (self.original_frame - 2);
					}
				}
				else
				{
					if ((self.frame == (self.original_frame - 2)))
					{
						zuf = random();
						if ((zuf > 0.3))
						{
							self.frame = self.original_frame;
						}
						else
						{
							self.frame = (self.original_frame - 1);
						}
					}
				}
			}
		}
		else
		{
			if (((autocvar_ragdoll == 3) && (self.netname != "progs/h_afrit.mdl")))
			{
				if ((self.frame == self.original_frame))
				{
					zuf = random();
					if ((zuf > 0.8))
					{
						self.frame = (self.original_frame - 1);
					}
					else
					{
						if ((zuf > 0.6))
						{
							self.frame = (self.original_frame - 2);
						}
						else
						{
							self.frame = (self.original_frame - 3);
						}
					}
				}
				else
				{
					if ((self.frame == (self.original_frame - 1)))
					{
						zuf = random();
						if ((zuf > 0.8))
						{
							self.frame = self.original_frame;
						}
						else
						{
							if ((zuf > 0.6))
							{
								self.frame = (self.original_frame - 2);
							}
							else
							{
								self.frame = (self.original_frame - 3);
							}
						}
					}
					else
					{
						if ((self.frame == (self.original_frame - 2)))
						{
							zuf = random();
							if ((zuf < 0.6))
							{
								self.frame = self.original_frame;
							}
							else
							{
								if ((zuf < 0.8))
								{
									self.frame = (self.original_frame - 1);
								}
								else
								{
									self.frame = (self.original_frame - 3);
								}
							}
						}
						else
						{
							if ((self.frame == (self.original_frame - 3)))
							{
								zuf = random();
								if ((zuf < 0.6))
								{
									self.frame = self.original_frame;
								}
								else
								{
									if ((zuf < 0.8))
									{
										self.frame = (self.original_frame - 1);
									}
									else
									{
										self.frame = (self.original_frame - 2);
									}
								}
							}
						}
					}
				}
			}
		}
	}
	if (autocvar_twitching_corpses)
	{
		self.twitch_finished = ((time + 2) + random());
	}
	self.just_been_shot = (time + 0.2);
};

void() SemisolidPreThink =
{
	local entity e;

	if (!has_semisolids)
		return;
	e = find(world, semisolid, "y");
	while (e)
	{
		e.oldSolid = e.solid;
		e.solid = 0;
		e = find(e, semisolid, "y");
	}
};

void() SemisolidPostThink =
{
	local entity e;
	local vector check;
	local float zuf;

	if (!has_semisolids)
		return;
	e = find(world, semisolid, "y");
	while (e)
	{
		if ((e.oldSolid != -1))
		{
			e.solid = e.oldSolid;
		}
		e.oldSolid = -1;
		if ((e.spin_direction == 1))
		{
			e.avelocity = '0 -77 0';
		}
		else
		{
			e.avelocity = '0 77 0';
		}
		check = (e.origin - '0 0 20') + '0 0 1';
		if ((autocvar_monsterlavaslime >= 1))
		{
			if ((pointcontents(check) == CONTENT_LAVA))
			{
				e.traileffectnum = particleeffectnum(/*19553i*/"monsterburn");
				e.colormod = '0.4 0.1 0.1';
			}
			if ((pointcontents(check) == CONTENT_SLIME))
			{
				e.traileffectnum = particleeffectnum(/*19565i*/"monsteracid");
				e.colormod = '0.9 1.4 0.4';
			}
			if (((pointcontents(check) != CONTENT_SLIME) && (pointcontents(check) != CONTENT_LAVA)))
			{
				e.traileffectnum = particleeffectnum(/*19577i*/"monsternull");
			}
		}
		if (autocvar_corpseflies)
		{
			if ((((pointcontents(check) != CONTENT_SLIME) && (pointcontents(check) != CONTENT_LAVA)) && (pointcontents(check) != CONTENT_WATER)))
			{
				if ((autocvar_corpseflies == 1))
				{
					e.traileffectnum = particleeffectnum(/*38603i*/"monsterfliesblack");
				}
				else
				{
					if ((autocvar_corpseflies == 2))
					{
						e.traileffectnum = particleeffectnum(/*38621i*/"monsterfliesbrown");
					}
				}
			}
		}
		if ((e.just_been_shot < time))
		{
			e.frame = e.original_frame;
			e.just_been_shot = (time + 9999);
		}
		if (autocvar_monster_blood_puddles)
		{
			if (((e.create_blood_puddle > time) && (e.create_blood_puddle_timer < time)))
			{
				traceline(e.origin, (e.origin - '0 0 66'), TRUE, self);
				if ((e.create_blood_puddle_counter == 0))
				{
					pointparticles(particleeffectnum(/*38639i*/"blood_smear"), trace_endpos, VEC_ORIGIN, 1);
				}
				e.create_blood_puddle_timer = (time + 0.1);
				e.create_blood_puddle_counter = (e.create_blood_puddle_counter + 1);
			}
		}
		if ((autocvar_twitching_corpses == 1))
		{
			if ((e.twitch_finished < time))
			{
				if (e.twitch_back)
				{
					e.frame = e.original_frame;
					e.twitch_finished = (((((time + autocvar_twitching_corpses_interval) + random()) + random()) + random()) + random());
					e.twitch_back = 0;
				}
				else
				{
					if ((e.frame == e.original_frame))
					{
						e.frame = (e.original_frame - 1);
						e.twitch_back = 1;
						e.twitch_finished = ((time + 0.2) + (random() * 0.2));
					}
				}
			}
		}
		else
		{
			if ((autocvar_twitching_corpses == 2))
			{
				if ((e.twitch_finished < time))
				{
					if (e.twitch_back)
					{
						e.frame = e.original_frame;
						e.twitch_finished = (((((time + autocvar_twitching_corpses_interval) + random()) + random()) + random()) + random());
						e.twitch_back = 0;
					}
					else
					{
						if ((e.frame == e.original_frame))
						{
							zuf = random();
							if ((zuf > 0.3))
							{
								e.frame = (e.original_frame - 1);
								e.twitch_back = 1;
								e.twitch_finished = ((time + 0.2) + (random() * 0.2));
							}
							else
							{
								e.frame = (e.original_frame - 2);
								e.twitch_back = 2;
								e.twitch_finished = ((time + 0.2) + (random() * 0.1));
							}
						}
					}
				}
			}
		}
		e = find(e, semisolid, "y");
	}
};
