#!/bin/bash
# usage: build.sh <srcdir>   (run inside MSYS2 MINGW64). SDL2 2.28.3 linked statically, like the shipped zircon_beta_gcc.exe.
set -e
cd "$1"
SDL=/g/Quake/zircon-fscache/deps/SDL2-2.28.3/x86_64-w64-mingw32
rm -f zircon_beta_windows_sdl.exe
make -f makefile -j16 DP_LINK_SDL=static \
  SDLCONFIG_UNIXCFLAGS="-I$SDL/include/SDL2 -Dmain=SDL_main" \
  SDLCONFIG_UNIXSTATICLIBS="-L$SDL/lib -lmingw32 -lSDL2main -Wl,-Bstatic -lSDL2 -Wl,-Bdynamic -mwindows -lm -ldinput8 -ldxguid -ldxerr8 -luser32 -lgdi32 -lwinmm -limm32 -lole32 -loleaut32 -lshell32 -lsetupapi -lversion -luuid" \
  sdl-release
