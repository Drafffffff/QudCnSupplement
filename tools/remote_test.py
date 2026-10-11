#!/usr/bin/env python3
"""Start/stop the isolated official-runtime test session, or capture its window."""
import argparse,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=r'''
import pathlib,subprocess,json
h=pathlib.Path.home();p=h/'qud-cn-supplement-test';game=h/'.local/share/Steam/steamapps/common/Caves of Qud';steam=game.parent
if action=='start':
 a=['systemd-run','--user','--unit=qud-cn-test','--collect','--working-directory='+str(game),'--setenv=DISPLAY=:1','--setenv=XDG_RUNTIME_DIR=/run/user/1000','--setenv=SteamAppId=333640','--setenv=SteamGameId=333640',str(steam/'SteamLinuxRuntime_soldier/_v2-entry-point'),'--verb=waitforexitandrun','--',str(steam/'SteamLinuxRuntime/scout-on-soldier-entry-point-v2'),'--',str(game/'CoQ.x86_64'),'-savepath',str(p),'-sharedpath',str(p/'Local'),'-syncedpath',str(p/'Synced'),'-logFile',str(p/'Player.log'),'-screen-fullscreen','0','-screen-width','1920','-screen-height','1080']
 subprocess.run(a,check=True)
elif action=='stop':subprocess.run(['systemctl','--user','stop','qud-cn-test'],check=True)
elif action=='capture':
 import os
 env=os.environ.copy();env['DISPLAY']=':1'
 wins=subprocess.check_output(['xdotool','search','--name','^CavesOfQud$'],env=env,text=True).split()
 if len(wins)!=1:raise SystemExit('Expected exactly one game window')
 subprocess.run(['import','-window',wins[0],'/tmp/qud-cn-test.png'],env=env,check=True)
else:
 for n in ['build_log.txt','Player.log']:
  f=p/n
  if f.exists():
   print(n)
   for l in f.read_text().splitlines():
    if n=='build_log.txt' or '[QudCn' in l or '[CN-QA]' in l or 'ERROR' in l:print(l)
'''
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['start','stop','capture','logs']);a.add_argument('--host',default='bazzite');args=a.parse_args()
 subprocess.run(['ssh',args.host,'python3','-'],input='action='+repr(args.action)+'\n'+SCRIPT,text=True,check=True)
 if args.action=='capture':subprocess.run(['scp','-q',args.host+':/tmp/qud-cn-test.png',str(ROOT/'analysis/test-current.png')],check=True)
