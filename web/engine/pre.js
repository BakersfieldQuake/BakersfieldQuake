// BakersfieldQuake browser client: replaces DarkPlaces' wasm/pre.js at build time (see build_wasm.sh).
//
// The page (site/index.html) downloads the game files itself (with progress and an IndexedDB cache)
// and hands them over as Module.gameFiles = { "id1/pak0.pak": Uint8Array, ... } before this script runs.
// Here they are written into the in-memory filesystem under /game without copying (canOwn), then the
// engine's main() starts with -basedir /game plus the page's own arguments.

Module['arguments'] = ['-basedir', '/game'].concat(Module['arguments'] || []);

Module['preRun'] = Module['preRun'] || [];
Module['preRun'].push(function () {
	// The engine polls stdin every frame. Emscripten's default stdin is window.prompt(), which freezes the
	// page behind an "Input" dialog, so stdin is always empty here.
	FS.init(function () { return null; }, null, null);
	FS.mkdir('/game');
	// saved settings (config.cfg) live under the home dir: keep them in the browser between visits
	FS.mount(IDBFS, {}, '/home/web_user/');

	var files = Module['gameFiles'] || {};
	var made = {};
	Object.keys(files).forEach(function (path) {
		var parts = path.split('/');
		var dir = '/game';
		for (var i = 0; i < parts.length - 1; i++) {
			dir += '/' + parts[i];
			if (!made[dir]) {
				try { FS.mkdir(dir); } catch (e) { /* exists */ }
				made[dir] = true;
			}
		}
		FS.writeFile('/game/' + path, files[path], { canOwn: true });
		delete files[path];
	});

	Module['addRunDependency']('syncfs');
	FS.syncfs(true, function (err) {
		if (err) console.warn('IDBFS load failed', err);
		Module['removeRunDependency']('syncfs');
	});
});
