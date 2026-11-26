// Player hats: the list shared by the server and CSQC (zz_hats.pk3). 0 is no hat.
float BM_HAT_COUNT = 8;

string(float h) BM_HatModel =
{
	if (h == 1) return "progs/hat_fedora.md3";
	if (h == 2) return "progs/hat_maga.md3";
	if (h == 3) return "progs/hat_wizard.md3";
	if (h == 4) return "progs/hat_afro.md3";
	if (h == 5) return "progs/hat_dildo.md3";
	if (h == 6) return "progs/hat_megaman.md3";
	if (h == 7) return "progs/hat_ghost.md3";
	if (h == 8) return "progs/hat_tophat.md3";
	return "";
};

// the ghost sheet flutters and the dildo wobbles; the others have a single frame
float(float h, float t) BM_HatAnimFrame =
{
	local float f, n, fps;
	n = 1; fps = 1;
	if (h == 5) { n = 16; fps = 14; }
	if (h == 7) { n = 12; fps = 10; }
	f = floor (t * fps);
	return f - n * floor (f / n);
};
