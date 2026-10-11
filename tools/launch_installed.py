#!/usr/bin/env python3
"""Launch the installed mod with the normal user profile and official Steam runtime."""
import subprocess
subprocess.run(['ssh','bazzite','python3','-'],input=r'''
import pathlib,subprocess
h=pathlib.Path.home();game=h/'.local/share/Steam/steamapps/common/Caves of Qud';steam=game.parent
if subprocess.run(['pgrep','-x','CoQ.x86_64'],capture_output=True,text=True).stdout.strip():raise SystemExit('Game is already running')
a=['systemd-run','--user','--unit=qud-cn-installed','--collect','--working-directory='+str(game),'--setenv=DISPLAY=:1','--setenv=XDG_RUNTIME_DIR=/run/user/1000','--setenv=SteamAppId=333640','--setenv=SteamGameId=333640',str(steam/'SteamLinuxRuntime_soldier/_v2-entry-point'),'--verb=waitforexitandrun','--',str(steam/'SteamLinuxRuntime/scout-on-soldier-entry-point-v2'),'--',str(game/'CoQ.x86_64'),'-logFile',str(h/'.config/unity3d/Freehold Games/CavesOfQud/cn-supplement-player.log')]
subprocess.run(a,check=True)
''',text=True,check=True)
