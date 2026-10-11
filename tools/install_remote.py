#!/usr/bin/env python3
"""Install the independent local mod with hashes, configuration backup and rollback."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import pathlib,json,base64,hashlib,shutil,datetime,os,subprocess
h=pathlib.Path.home();root=h/'.config/unity3d/Freehold Games/CavesOfQud';dest=root/'Mods/QudCnSupplement';options=root/'Local/PlayerOptions.json'
# Match the actual executable name; do not match this SSH command line.
if subprocess.run(['pgrep','-x','CoQ.x86_64'],capture_output=True,text=True).stdout.strip():raise SystemExit('Game is running: save and exit first.')
state=root/'cn-supplement-install.json'
if payload['action']=='install':
 if state.exists():raise SystemExit('Managed installation exists; uninstall before replacing it.')
 if dest.exists():raise SystemExit('Unmanaged destination exists; refusing to overwrite.')
 stamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
 backup=root/'cn-supplement-backups'/stamp;backup.mkdir(parents=True,exist_ok=False)
 before=options.read_bytes() if options.exists() else None
 if before is not None:(backup/'PlayerOptions.json.before').write_bytes(before)
 settings=json.loads(before) if before else {};prev=settings.get('OptionAllowCSMods');settings['OptionAllowCSMods']='Yes'
 info={'version':payload['version'],'destination':str(dest),'backup':str(backup),'original_options_existed':before is not None,'previous_allow_scripts':prev,'files':payload['hashes']}
 try:
  dest.mkdir(parents=True)
  for name,blob in payload['data'].items():
   rel=pathlib.PurePosixPath(name)
   if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe relative file path')
   b=base64.b64decode(blob)
   if hashlib.sha256(b).hexdigest()!=payload['hashes'][name]:raise ValueError('Payload hash mismatch')
   p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  options.parent.mkdir(parents=True,exist_ok=True);tmp=options.with_suffix('.json.cn-tmp');tmp.write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,options)
  for name,digest in payload['hashes'].items():
   if hashlib.sha256((dest/name).read_bytes()).hexdigest()!=digest:raise ValueError('Installed hash mismatch')
  (backup/'install.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n');state.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
 except:
  if before is not None:options.write_bytes(before)
  elif options.exists():options.unlink()
  if dest.exists():shutil.rmtree(dest)
  raise
 print(json.dumps(info,ensure_ascii=False,indent=2))
else:
 info=json.loads(state.read_text());backup=pathlib.Path(info['backup'])
 for name,digest in info['files'].items():
  p=dest/name
  if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise SystemExit('Installed mod was modified; refusing automatic removal: '+name)
 allowed=set(info['files']);extra=[str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and str(p.relative_to(dest)) not in allowed]
 if extra:raise SystemExit('Destination has extra files; review before uninstall: '+str(extra))
 settings=json.loads(options.read_text())
 if settings.get('OptionAllowCSMods')!='Yes':raise SystemExit('Scripting setting changed; review before rollback')
 if info['previous_allow_scripts'] is None:settings.pop('OptionAllowCSMods',None)
 else:settings['OptionAllowCSMods']=info['previous_allow_scripts']
 options.write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n')
 shutil.rmtree(dest);state.rename(backup/'uninstalled.json');print(json.dumps({'status':'uninstalled','backup':str(backup)}))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--host',default='bazzite');p.add_argument('--uninstall',action='store_true');args=p.parse_args()
 files={str(p.relative_to(ROOT/'mod')):p.read_bytes() for p in sorted((ROOT/'mod').rglob('*')) if p.is_file()}
 payload={'action':'uninstall' if args.uninstall else 'install','version':'0.1.0','hashes':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},'data':{n:base64.b64encode(b).decode() for n,b in files.items()}}
 code='payload='+repr(payload)+'\n'+REMOTE
 r=subprocess.run(['ssh',args.host,'python3','-'],input=code,text=True,capture_output=True)
 if r.returncode:raise SystemExit(r.stdout+r.stderr)
 print(r.stdout.strip())
 if not args.uninstall:(ROOT/'analysis/install.json').write_text(r.stdout)
if __name__=='__main__':main()
