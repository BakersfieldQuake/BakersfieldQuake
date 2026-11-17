// BakersfieldQuake MenuQC definitions & Zircon mvm_builtin bindings

#pragma target dp
#pragma flag enable assumeint
#pragma warning disable F313
#pragma warning disable F333
#pragma warning disable Q208

// Required MenuQC system globals
entity self;
entity other;
entity world;
float time;
float frametime;
float drawfont;
vector drawfontscale;
void end_sys_globals;
void end_sys_fields;

// Constants
float FALSE = 0;
float TRUE = 1;

float KEY_GAME = 0;
float KEY_CONSOLE = 1;
float KEY_MENU = 2;
float KEY_MENU_GRABBED = 3;

// Zircon mouse targets: 1 sets relative/warped mouse mode (pulls back to 0,0);
// 2 sets free cursor mode (VID_SetMouse relative=0, absolute window coords in getmousepos).
float MT_WARPED = 1;
float MT_FREE = 2;

float FILE_READ = 0;
float FILE_APPEND = 1;
float FILE_WRITE = 2;

// Zircon clientstate() values
float CS_DEDICATED    = 0;
float CS_DISCONNECTED = 1;
float CS_CONNECTED    = 2;

// Key codes (Zircon / DP)
float K_TAB = 9;
float K_ENTER = 13;
float K_ESCAPE = 27;
float K_SPACE = 32;
float K_BACKSPACE = 127;
float K_UPARROW = 128;
float K_DOWNARROW = 129;
float K_LEFTARROW = 130;
float K_RIGHTARROW = 131;
float K_ALT = 132;
float K_CTRL = 133;
float K_SHIFT = 134;
float K_F1 = 135;
float K_F2 = 136;
float K_F3 = 137;
float K_F4 = 138;
float K_F5 = 139;
float K_F6 = 140;
float K_F7 = 141;
float K_F8 = 142;
float K_F9 = 143;
float K_F10 = 144;
float K_F11 = 145;
float K_F12 = 146;
float K_INS = 147;
float K_DEL = 148;
float K_PGDN = 149;
float K_PGUP = 150;
float K_HOME = 151;
float K_END = 152;
float K_KP_ENTER = 172;
float K_BACKQUOTE = 96;
float K_TILDE = 126;
float K_MOUSE1 = 512;
float K_MOUSE2 = 513;
float K_MOUSE3 = 514;
float K_MWHEELUP = 515;
float K_MWHEELDOWN = 516;
float K_MOUSE4 = 517;
float K_MOUSE5 = 518;

// Verified Zircon mvm_builtin bindings
void(...) print = #4;
float() random = #12;
void(...) localcmd = #13;
float(...) cvar = #14;
void(...) cvar_set = #15;
string(float f) ftos = #17;
float(float f) fabs = #18;
string(vector v) vtos = #19;
float(string s) stof = #21;
float(float f) rint = #34;
float(float f) floor = #35;
float(float f) ceil = #36;
float(float f) sin = #38;
float(float f) cos = #39;
float(float f) sqrt = #40;
float(string name, string val, ...) registercvar = #42;
float(float a, float b, ...) min = #43;
float(float a, float b, ...) max = #44;
float(float minimum, float val, float maximum) bound = #45;
float(float base, float exp) pow = #46;
float(string filename, float mode) fopen = #48;
void(float handle) fclose = #49;
string(float handle) fgets = #50;
void(float handle, string s) fputs = #51;
float(string s) strlen = #52;
string(...) strcat = #53;
string(string s, float start, float length) substring = #54;
string(string s) strzone = #56;
void(string s) strunzone = #57;
float(string s) tokenize = #58;
string(float n) argv = #59;
float() isserver = #60;
float() clientcount = #61;
float() clientstate = #62;
void(string s) localsound = #65;
vector() getmousepos = #66;
float() gettime = #67;
float(float a, float b) modulo = #70;
string(...) cvar_string = #71;
float(string pattern, float caseinsensitive, float quiet) search_begin = #74;
void(float handle) search_end = #75;
float(float handle) search_getsize = #76;
string(float handle, float num) search_getfilename = #77;
float() getkeysshiftstate = #94;
string() clipboard_get = #95;
void(string s) clipboard_set = #96;
float(string s, string sub, ...) strstrofs = #221;
float(string s, float ofs) str2chr = #222;
string(...) chr2str = #223;
float(string a, string b, float len) strncmp = #228;
float(string a, string b, ...) strcasecmp = #229;
float(string a, string b, float len) strncasecmp = #230;
string(float keynum) keynumtostring = #340;
float(string keyname) stringtokeynum = #341;
string(float keynum, ...) getkeybind = #342;
void(string cmd) registercommand = #352;
string(string cmd, ...) findkeysforcommand = #610;
void(float key, string cmd, ...) setkeybind = #630;
float(...) buf_create = #440;
void(float bufhandle) buf_del = #441;
float(float bufhandle) buf_getsize = #442;
string(float bufhandle, float string_index) bufstr_get = #446;
void(float bufhandle, float string_index, string str) bufstr_set = #447;
float(float bufhandle, string str, float order) bufstr_add = #448;
void(float bufhandle, float string_index) bufstr_free = #449;
float(string pic) iscachedpic = #451;
string(string pic, ...) precache_pic = #452;
void(string pic) freepic = #453;
float(vector pos, float ch, vector scale, vector rgb, float alpha, float flag) drawcharacter = #454;
float(vector pos, string text, vector scale, vector rgb, float alpha, ...) drawstring = #455;
float(vector pos, string pic, vector size, vector rgb, float alpha, ...) drawpic = #456;
float(vector pos, vector size, vector rgb, float alpha, float flag) drawfill = #457;
void(float x, float y, float w, float h) drawsetcliparea = #458;
void() drawresetcliparea = #459;
vector(string pic) getimagesize = #460;
float(vector pos, string text, vector scale, float alpha, ...) drawcolorcodedstring = #467;
float(string text, float useColors, ...) stringwidth = #468;
float(string s) strlennocol = #476;
string(string s) strdecolorize = #477;
string(string s) strtolower = #480;
string(string s) strtoupper = #481;
void(float dest) setkeydest = #601;
float() getkeydest = #602;
void(float target) setmousetarget = #603;
float() getmousetarget = #604;
vector(float mode) getresolution = #608;
float(float type) getserverliststat = #611;
string(float fld, float hostnr) getserverliststring = #612;
void() resetserverlistmasks = #615;
void(float mask, float fld, string str, float op) setserverlistmaskstring = #616;
void(float mask, float fld, float num, float op) setserverlistmasknumber = #617;
void() resortserverlist = #618;
void(float fld, float flags) setserverlistsort = #619;
void(...) refreshserverlist = #620;
float(float fld, float hostnr) getserverlistnumber = #621;
float(string key) getserverlistindexforkey = #622;
void(string key) addwantedserverlistkey = #623;
string(string fmt, ...) sprintf = #627;

// Serverlist field indices (resolved dynamically in BM_InitServerListKeys)
var float SLIST_CNAME = 0;
var float SLIST_PING = 1;
var float SLIST_GAME = 2;
var float SLIST_MOD = 3;
var float SLIST_MAP = 4;
var float SLIST_NAME = 5;
var float SLIST_MAXPLAYERS = 6;
var float SLIST_NUMPLAYERS = 7;
var float SLIST_NUMBOTS = 9;
var float SLIST_ISFAVORITE = 15;

// getserverliststat types
float SLSTAT_VIEWCOUNT = 0;
float SLSTAT_TOTALCOUNT = 1;
float SLSTAT_MASTERQUERY = 2;
float SLSTAT_MASTERREPLY = 3;
float SLSTAT_SERVERQUERY = 4;
float SLSTAT_SERVERREPLY = 5;

// Pages
float PAGE_MAIN = 0;
float PAGE_BROWSER = 1;
float PAGE_HOST = 2;
float PAGE_OPTIONS = 3;

// Active text input IDs
float INPUT_NONE = 0;
float INPUT_PLAYERNAME = 1;
float INPUT_DIRECTIP = 2;
float INPUT_HOSTNAME = 3;

// Shared MenuQC state
float g_menu_open;
float g_page;
float g_vw;
float g_vh;
float g_mx;
float g_my;
float g_mouse_moved;
float g_last_mx;
float g_last_my;
float g_focus_input;
float g_click_consumed;
string g_levelshot_known;
string g_name_buf;
string g_ip_buf;
string g_host_buf;
float g_bg_slide_idx;
float g_bg_slide_prev;
float g_bg_slide_t;
float g_bg_slide_count;
float g_bg_buf;
float g_opt_tab;
float g_opt_scroll;
float g_bind_listen_idx;

// Required entrypoint forward declarations
void() m_init;
void() m_shutdown;
void() m_draw;
void(float key, float ascii) m_keydown;
void(float key, float ascii) m_keyup;
void(float mode) m_toggle;
void() m_newmap;
float(float entry) m_gethostcachecategory;
void(float width, float height, float defwidth, float defheight) m_drawloading;
