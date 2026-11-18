# HANDOFF: stop the engine probing loose folders for files that cannot be there

For whoever builds the engine (rgr4y/zircon-darkplaces, pinned at `e19de67` in `source/mac/build_app.sh`).
Evidence and numbers are in `docs/audit-2026-11-18-performance.md`.

Status 2026-11-18: built and measured on Windows (MSYS2 MINGW64, gcc 15.2, `make -f makefile DP_LINK_SDL=static
sdl-release`, no build fixes). Tree with the patch applied: `G:\Quake\_zircon_build\src`; outputs in
`G:\Quake\_zircon_build\out` (`zircon_fsdircache.exe`, `zircon_stock_rebuild.exe`, `zircon-fs-dircache.patch`).
soi6, release layout: 8.7 s shipped, 8.9 s same-compiler rebuild, 7.3 s patched. Separate user folder: 13.0 s, 12.9 s,
7.9 s. The create-then-read regression below passes; download, demo and human play tests are still open. The built
patch differs from the sketch in three places: the epoch is bumped only when mkdir succeeds, names containing `..`
skip the cache, and search paths with a pack skip it. Not installed in the game folder.

## The problem

`FS_FindFile` (fs.c) walks the search path for every name it is asked for. A pk3 is a binary search in memory.
A loose game directory is one `GetFileAttributesW` call (one `stat` on Linux/macOS) per name, hit or miss.

Loading one texture asks for about 40 names, nearly all of them missing: the optional `_norm`, `_bump`, `_glow`,
`_luma`, `_gloss`, `_pants`, `_shirt`, `_reflect` and `_mask` variants, each as `.tga`, `.png`, `.jpg` and `.pcx`.
A big map loads about 1,900 textures. That is on the order of 80,000 failed OS calls per loose directory per map load.

Measured on 2026-11-18 (Ryzen 7 7700X, NVMe, Windows 11, map `soi6`), main thread sampled every 3 ms during the load:

| layout | loose dirs searched | load | time inside `GetFileAttributesW` |
|---|---|---|---|
| `-userdir` = `-basedir` (Play.cmd) | 3 (`id1`, `quake15`, `BakersfieldQuake`) | 8.6 s | 20% |
| separate `-userdir` (macOS app, test runs) | 6 | 12.8 s | 45% |

The three extra directories cost 4.2 s although they hold no assets. On a slower disk, or with an antivirus filter on the
file system, every one of those calls costs more.

## The fix

Remember, per loose directory, which first-level folders exist. A release install has no loose `progs/`, `textures/`,
`gfx/` or `sound/` in `BakersfieldQuake/` or `id1/`, and the user directory has none of them either. If
`<dir>/progs` does not exist, `<dir>/progs/anything` cannot exist, so the OS call can be skipped.

- Only the first path component is cached, so the table stays tiny (24 entries per directory).
- Names without a `/` (config.cfg, progs.dat) are always checked the old way.
- The cache is dropped whenever the engine itself creates a directory (`FS_mkdir`) and on `FS_Rescan`, so a file the
  game just wrote (QC `fopen`, downloads into `dlcache/`, screenshots, demos) is found on the very next lookup.
- Entries also expire after 5 s, so a folder the user creates by hand while the game runs shows up without a restart.
- `fs_dircache 0` turns it off.

## Sketch against fs.c at `e19de67` (line numbers from that commit)

`searchpath_t` (line 404) gets the table. `Mem_Alloc` zero-fills, so no init is needed where search paths are created.

```c
#define FS_DIRCACHE_MAX 24
#define FS_DIRCACHE_TTL 5.0
typedef struct fs_dircache_entry_s {
	char name[32];
	qbool exists;
	double expires;
	unsigned epoch;
} fs_dircache_entry_t;

typedef struct searchpath_s {
	// only one of filename / pack will be used
	char filename[MAX_OSPATH];
	pack_t *pack;
	struct searchpath_s *next;
	fs_dircache_entry_t dircache[FS_DIRCACHE_MAX];
	int dircache_count;
} searchpath_t;

static unsigned fs_dircache_epoch = 1; // bumped whenever the engine creates a directory or rescans
cvar_t fs_dircache = {CF_CLIENT | CF_SERVER, "fs_dircache", "1", "skip loose-file lookups under top-level folders that do not exist in a game directory (0 = ask the OS for every name)"};
```

Register the cvar next to `fs_empty_files_in_pack_mark_deletions` (line 5091). In `FS_mkdir` (line 4975) add
`fs_dircache_epoch++;` after the mkdir call, and the same at the top of `FS_Rescan` (line 1515).

```c
// true when <search dir>/<name> could exist. false only when the first folder of name is known to be missing.
static qbool FS_DirMayContain (searchpath_t *search, const char *name)
{
	const char *slash = strchr(name, '/');
	size_t len;
	int i;
	double now;
	fs_dircache_entry_t *e;
	char netpath[MAX_OSPATH];

	if (!fs_dircache.integer || !slash)
		return true;
	len = slash - name;
	if (len == 0 || len >= sizeof(search->dircache[0].name))
		return true;
	now = Sys_DirtyTime();
	for (i = 0; i < search->dircache_count; i++) {
		e = &search->dircache[i];
		if (!strncasecmp(e->name, name, len) && e->name[len] == 0) {
			if (e->epoch == fs_dircache_epoch && now < e->expires && now >= e->expires - FS_DIRCACHE_TTL)
				return e->exists;
			break; // stale: ask again and reuse this slot
		}
	}
	if (i == search->dircache_count) {
		if (search->dircache_count == FS_DIRCACHE_MAX)
			return true; // table full: behave as before
		search->dircache_count++;
	}
	e = &search->dircache[i];
	memcpy(e->name, name, len);
	e->name[len] = 0;
	dpsnprintf(netpath, sizeof(netpath), "%s%s", search->filename, e->name);
	e->exists = FS_SysFileOrDirectoryType(netpath) == FS_FILETYPE_DIRECTORY_2;
	e->expires = now + FS_DIRCACHE_TTL;
	e->epoch = fs_dircache_epoch;
	return e->exists;
}
```

In `FS_FindFile` (line 2961), the directory branch becomes:

```c
		} else {
			char netpath[MAX_OSPATH];

			if (!FS_DirMayContain(search, name))
				continue;
			dpsnprintf(netpath, sizeof(netpath), "%s%s", search->filename, name);
			if (FS_SysFileExists (netpath)) {
```

`FS_SysFileOrDirectoryType` is defined after `FS_FindFile` (line 4026); add a prototype near line 425.

## Things to check when building it

- `.pk3dir` / `.dpkdir` search paths take the same branch (`search->pack->vpack`). Confirm `search->filename` is the
  directory for them, or skip the cache when `search->pack` is set.
- Case: `strncasecmp` is right for Windows and macOS. On a case-sensitive Linux file system `Progs/` and `progs/` are
  two folders; a miss on `progs` is still a correct "no" for a lookup of `progs/...`, so this is safe.
- A lookup of the folder name itself (`FS_FileExists("progs")`) has no `/` and is not cached.
- Dedicated servers gain little (they load no textures); the win is on clients.

## How to verify

`source/mm_tools/perf/loadtime.py` times a host-game load and `sampler.py` shows where the main thread is.
Expected on `soi6` with the release layout: `GetFileAttributesW` drops from about 20% of the load to a few percent
(the loose `quake15/progs/` folder is still probed for `progs/...` names), and the load from about 8.6 s towards 7 s.
With a separate user directory (the macOS app) the gain should be about 5 s. Packing the loose files of
`quake15/progs/` into a pk3 would remove the remaining probes, but that folder is Combat+'s, so ask first.

Then check that nothing regressed: a new player's first launch (config.cfg is written and read back), a QC file
written and read in the same frame, a pk3 downloaded into `dlcache/` and loaded on the next map, a screenshot, and
a demo recorded and played back without restarting.
