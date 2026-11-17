//Decompiled code. Please respect the original copyright.
float(string extname) checkextension = #99; 
__variant(...) setattachment = #443; 
__variant(...) asin = #471; 
__variant(...) acos = #472; 
__variant(...) atan = #473; 
__variant(...) atan2 = #474; 
__variant(...) tan = #475; 
__variant(...) changepitch = #63; 
__variant(...) copyentity = #400; 
__variant(...) crc16 = #494; 
__variant(...) cvar_defstring = #482; 
__variant(...) cvar_description = #518; 
string(string cvarname) cvar_string = #448; 
__variant(...) cvar_type = #495; 
__variant(...) digest_hex = #639; 
__variant(...) edict_num = #459; 
__variant(...) wasfreed = #353; 
__variant(...) numentityfields = #496; 
__variant(...) entityfieldname = #497; 
__variant(...) entityfieldtype = #498; 
__variant(...) getentityfieldstring = #499; 
__variant(...) putentityfieldstring = #500; 
__variant(...) loadfromdata = #529; 
__variant(...) loadfromfile = #530; 
__variant(...) callfunction = #605; 
__variant(...) writetofile = #606; 
__variant(...) isfunction = #607; 
__variant(...) parseentitydata = #608; 
__variant(...) etos = #65; 
__variant(...) getextresponse = #624; 
__variant(...) findchain = #402; 
entity (vector org, float rad) findradius_tofield = #22; 
__variant(...) findchain_tofield = #402; 
__variant(...) findchainflags_tofield = #450; 
__variant(...) findchainfloat_tofield = #403; 
__variant(...) findchainflags = #450; 
__variant(...) findchainentity = #403; 
__variant(...) findchainfloat = #403; 
__variant(...) findflags = #449; 
entity(entity start, .__variant fld, __variant match) findentity = #98; 
entity(entity start, .__variant fld, __variant match) findfloat = #98; 
__variant(...) search_begin = #444; 
__variant(...) search_end = #445; 
__variant(...) search_getsize = #446; 
__variant(...) search_getfilename = #447; 
vector(vector org) getlight = #92; 
__variant(...) getsurfacenumpoints = #434; 
__variant(...) getsurfacepoint = #435; 
__variant(...) getsurfacenormal = #436; 
__variant(...) getsurfacetexture = #437; 
__variant(...) getsurfacenearpoint = #438; 
__variant(...) getsurfaceclippedpoint = #439; 
__variant(...) getsurfacepointattribute = #486; 
__variant(...) getsurfacenumtriangles = #628; 
__variant(...) getsurfacetriangle = #629; 
__variant(...) gettagindex = #451; 
__variant(...) gettaginfo = #452; 
__variant(...) gettime = #519; 
__variant(...) log = #532; 
float(float a, float b, ...) min = #94; 
float(float a, float b, ...) min3 = #94; 
float(float a, float b, ...) min4 = #94; 
float(float a, float b, ...) min5 = #94; 
float(float a, float b, ...) min6 = #94; 
float(float a, float b, ...) min7 = #94; 
float(float a, float b, ...) min8 = #94; 
float(float a, float b, ...) max = #95; 
float(float a, float b, ...) max3 = #95; 
float(float a, float b, ...) max4 = #95; 
float(float a, float b, ...) max5 = #95; 
float(float a, float b, ...) max6 = #95; 
float(float a, float b, ...) max7 = #95; 
float(float a, float b, ...) max8 = #95; 
float(float minimum, float val, float maximum) bound = #96; 
__variant(...) num_for_edict = #512; 
vector() randomvec = #91; 
__variant(...) sin = #60; 
__variant(...) cos = #61; 
__variant(...) sqrt = #62; 
float(float value, float exp) pow = #97; 
__variant(...) sprintf = #627; 
__variant(...) strftime = #478; 
__variant(...) strlennocol = #476; 
__variant(...) strdecolorize = #477; 
__variant(...) strtolower = #480; 
__variant(...) strtoupper = #481; 
__variant(...) tokenizebyseparator = #479; 
__variant(...) tokenize_console = #514; 
__variant(...) argv_start_index = #515; 
__variant(...) argv_end_index = #516; 
void(vector start, vector mins, vector maxs, vector end, float nomonsters, entity ent) tracebox = #90; 
__variant(...) tracetoss = #64; 
vector (vector v, ...) vectoangles2 = #51; 
__variant(...) vectorvectors = #432; 
__variant(...) whichpack = #503; 
__variant(...) uri_escape = #510; 
__variant(...) uri_unescape = #511; 
__variant(...) uri_get = #513; 
__variant(...) uri_post = #513; 
__variant(...) uri_postbuf = #513; 
float(string cvarname, string defaultvalue) registercvar = #93; 
void (entity e, float chan, string samp, float vol, float atten, ...) sound7 = #8; 
__variant(...) getsoundtime = #533; 
__variant(...) soundlength = #534; 
__variant(...) spawnclient = #454; 
__variant(...) clienttype = #455; 
__variant(...) dropclient = #453; 
__variant(...) effect = #404; 
__variant(...) pointsound = #483; 
float(string effectname) particleeffectnum = #335; 
__variant(...) trailparticles = #336; 
__variant(...) pointparticles = #337; 
__variant(...) physics_enable = #540; 
__variant(...) physics_addforce = #541; 
__variant(...) physics_addtorque = #542; 
__variant(...) print = #339; 
__variant(...) setcolor = #401; 
__variant(...) WritePicture = #501; 
__variant(...) WriteUnterminatedString = #456; 
__variant(...) te_blood = #405; 
__variant(...) te_bloodshower = #406; 
__variant(...) te_customflash = #417; 
__variant(...) te_explosionrgb = #407; 
__variant(...) te_flamejet = #457; 
__variant(...) te_particlecube = #408; 
__variant(...) te_particlerain = #409; 
__variant(...) te_particlesnow = #410; 
__variant(...) te_plasmaburn = #433; 
__variant(...) te_gunshotquad = #412; 
__variant(...) te_spikequad = #413; 
__variant(...) te_superspikequad = #414; 
__variant(...) te_explosionquad = #415; 
__variant(...) te_smallflash = #416; 
__variant(...) te_spark = #411; 
__variant(...) te_gunshot = #418; 
__variant(...) te_spike = #419; 
__variant(...) te_superspike = #420; 
__variant(...) te_explosion = #421; 
__variant(...) te_tarexplosion = #422; 
__variant(...) te_wizspike = #423; 
__variant(...) te_knightspike = #424; 
__variant(...) te_lavasplash = #425; 
__variant(...) te_teleport = #426; 
__variant(...) te_explosion2 = #427; 
__variant(...) te_lightning1 = #428; 
__variant(...) te_lightning2 = #429; 
__variant(...) te_lightning3 = #430; 
__variant(...) te_beam = #431; 
__variant(...) bitshift = #218; 
float(string s) stof = #81; 
float(string filename, float mode, optional float mmapminsize) fopen = #110; 
void(float fhandle) fclose = #111; 
string(float fhandle) fgets = #112; 
void(float fhandle, string s, optional string s2, optional string s3, optional string s4, optional string s5, optional string s6, optional string s7) fputs = #113; 
float(string s) strlen = #114; 
string(string s, float start, float length) substring = #116; 
vector(string s) stov = #117; 
string(string s, ...) strzone = #118; 
void(string s) strunzone = #119; 
__variant(...) skel_create = #263; 
__variant(...) skel_build = #264; 
__variant(...) skel_get_numbones = #265; 
__variant(...) skel_get_bonename = #266; 
__variant(...) skel_get_boneparent = #267; 
float(...) skel_find_bone = #268; 
__variant(...) skel_get_bonerel = #269; 
__variant(...) skel_get_boneabs = #270; 
__variant(...) skel_set_bone = #271; 
__variant(...) skel_mul_bone = #272; 
__variant(...) skel_mul_bones = #273; 
__variant(...) skel_copybones = #274; 
__variant(...) skel_delete = #275; 
__variant(...) frameforname = #276; 
__variant(...) frameduration = #277; 

float(float skel, float bonenum, string g1, string g2, string g3, string g4, string g5, string g6) example_skel_findbonegroup =
{
	local string bonename;

	while ((bonenum >= 0))
	{
		bonename = skel_get_bonename(skel, bonenum);
		if ((bonename == g1))
		{
			return (1);
		}
		if ((bonename == g2))
		{
			return (2);
		}
		if ((bonename == g3))
		{
			return (3);
		}
		if ((bonename == g4))
		{
			return (4);
		}
		if ((bonename == g5))
		{
			return (5);
		}
		if ((bonename == g6))
		{
			return (6);
		}
		bonenum = skel_get_boneparent(skel, bonenum);
	}
	return (0);
};

void() example_skel_player_setup =
{
	self.skeletonindex = skel_create(self.modelindex);
};

void(float animmodelindex, float framegroup, float framegroupstarttime) example_skel_player_update_begin =
{
	self.frame = framegroup;
	self.frame2 = 0;
	self.frame3 = 0;
	self.frame4 = 0;
	self.frame1time = framegroupstarttime;
	self.frame2time = 0;
	self.frame3time = 0;
	self.frame4time = 0;
	self.lerpfrac = 0;
	self.lerpfrac3 = 0;
	self.lerpfrac4 = 0;
	skel_build(self.skeletonindex, self, animmodelindex, 0, 0, 100000);
};

void(float animmodelindex, float framegroup, float framegroupstarttime, float blendalpha, string groupbonename, string excludegroupname1, string excludegroupname2) example_skel_player_update_applyoverride =
{
	local float bonenum;
	local float numbones;

	self.frame = framegroup;
	self.frame2 = 0;
	self.frame3 = 0;
	self.frame4 = 0;
	self.frame1time = framegroupstarttime;
	self.frame2time = 0;
	self.frame3time = 0;
	self.frame4time = 0;
	self.lerpfrac = 0;
	self.lerpfrac3 = 0;
	self.lerpfrac4 = 0;
	bonenum = 0;
	numbones = skel_get_numbones(self.skeletonindex);
	while ((bonenum < numbones))
	{
		if ((example_skel_findbonegroup(self.skeletonindex, bonenum, groupbonename, excludegroupname1, excludegroupname2, "", "", "") == 1))
		{
			skel_build(self.skeletonindex, self, animmodelindex, (1 - blendalpha), bonenum, (bonenum + 1));
		}
		bonenum = bonenum + 1;
	}
};

void(vector eyetarget, string bonename) example_skel_player_update_eyetarget =
{
	local float bonenum;
	local vector ang;
	local vector oldforward;
	local vector oldright;
	local vector oldup;
	local vector relforward;
	local vector relright;
	local vector relup;
	local vector relorg;
	local vector boneforward;
	local vector boneright;
	local vector boneup;
	local vector boneorg;
	local vector parentforward;
	local vector parentright;
	local vector parentup;
	local vector parentorg;
	local vector u;
	local vector v;
	local vector modeleyetarget;

	bonenum = skel_find_bone(self.skeletonindex, bonename) - 1;
	if ((bonenum < 0))
	{
		return;
	}
	oldforward = v_forward;
	oldright = v_right;
	oldup = v_up;
	v = eyetarget - self.origin;
	modeleyetarget_x = v * v_forward;
	relorg = skel_get_bonerel(self.skeletonindex, bonenum);
	relforward = v_forward;
	relright = v_right;
	relup = v_up;
	boneorg = skel_get_boneabs(self.skeletonindex, bonenum);
	boneforward = v_forward;
	boneright = v_right;
	boneup = v_up;
	parentorg = skel_get_boneabs(self.skeletonindex, skel_get_boneparent(self.skeletonindex, bonenum));
	parentforward = v_forward;
	parentright = v_right;
	parentup = v_up;
	u = modeleyetarget - boneorg;
	v_x = u * parentforward;
	ang = vectoangles2(v, relup);
	ang_x = 0 - ang_x;
	makevectors(ang);
	skel_set_bone(self.skeletonindex, bonenum, relorg);
	v_forward = oldforward;
	v_right = oldright;
	v_up = oldup;
};

void() example_skel_player_delete =
{
	skel_delete(self.skeletonindex);
	self.skeletonindex = 0;
};
__variant(...) clientcommand = #440; 
__variant(...) tokenize = #441; 
__variant(...) argv = #442; 
__variant(...) checkpvs = #240; 
__variant(...) strstrofs = #221; 
__variant(...) str2chr = #222; 
__variant(...) chr2str = #223; 
__variant(...) strconv = #224; 
__variant(...) strpad = #225; 
__variant(...) infoadd = #226; 
__variant(...) infoget = #227; 
__variant(...) strncmp = #228; 
__variant(...) strcasecmp = #229; 
__variant(...) strncasecmp = #230; 
__variant(...) buf_create = #460; 
__variant(...) buf_del = #461; 
__variant(...) buf_getsize = #462; 
__variant(...) buf_copy = #463; 
__variant(...) buf_sort = #464; 
__variant(...) buf_implode = #465; 
__variant(...) bufstr_get = #466; 
__variant(...) bufstr_set = #467; 
__variant(...) bufstr_add = #468; 
__variant(...) bufstr_free = #469; 
__variant(...) buf_cvarlist = #517; 
__variant(...) buf_loadfile = #535; 
__variant(...) buf_writefile = #536; 
__variant(...) bufstr_find = #537; 
__variant(...) matchpattern = #538; 
__variant(...) matchpatternofs = #538; 
__variant(...) strreplace = #484; 
__variant(...) strireplace = #485; 
__variant(...) addstat = #232; 
__variant(...) setpause = #531; 
__variant(...) crypto_uri_postbuf = #513; 
