// written by mm_tools/build_megaman_arsenal_4v.py (glow dimmed for combat clarity)

progs/mma_wheel
{
	cull none
	{
		map progs/mma_wheel
		rgbGen lightingDiffuse
	}
}

progs/mma_arsenal
{
	cull none
	{
		map progs/mma_arsenal
		rgbGen lightingDiffuse
	}
}

progs/mma_fx
{
	cull none
	{
		map progs/mma_fx
		blendfunc add
		rgbGen const ( 0.25 0.25 0.25 )
	}
}
