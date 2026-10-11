#!/usr/bin/env python3
"""Read-only hashes of the normal profile's save files; never prints save contents."""
import argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args()
r=subprocess.run(['ssh','bazzite','python3','-'],input=r'''
import pathlib,hashlib,json
r=pathlib.Path.home()/'.config/unity3d/Freehold Games/CavesOfQud/Synced/Saves'
a={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(r.rglob('*')) if p.is_file()}
print(json.dumps(a,indent=2))
''',capture_output=True,text=True,check=True)
Path(a.output).write_text(r.stdout)
