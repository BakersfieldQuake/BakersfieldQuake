// written by mm_tools/build_megaman_weapon.py (glow dimmed for combat clarity)

progs/mmw_gun_metal
{
	cull none
	{
		map progs/mmw_gun_metal
		rgbGen lightingDiffuse
	}
}

progs/mmw_chrome_axle
{
	cull none
	{
		map progs/mmw_chrome_axle
		rgbGen lightingDiffuse
	}
}

progs/mmw_wheel
{
	cull none
	{
		map progs/mmw_wheel
		rgbGen lightingDiffuse
	}
}

progs/mmw_hand
{
	cull none
	{
		map progs/mmw_hand
		rgbGen lightingDiffuse
	}
}

progs/mmw_gauge_glow
{
	cull none
	{
		map progs/mmw_gauge_glow
		rgbGen const ( 0.35 0.35 0.35 )
	}
}

progs/mmw_fx
{
	cull none
	{
		map progs/mmw_fx
		blendfunc add
		rgbGen const ( 0.25 0.25 0.25 )
	}
}
