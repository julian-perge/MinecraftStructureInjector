"""Launch an isolated, invisible Minecraft client without desktop input."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import urllib.error
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['smoke', 'lab'], default='smoke')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--jar', type=Path, help='Load this packaged mod from the isolated mods folder')
    args = parser.parse_args()
    directory = (args.directory or ROOT / 'artifacts' / ('hidden-' + time.strftime('%Y%m%d-%H%M%S'))).resolve()
    connection_file = directory / 'structurelab/connection.json'
    if connection_file.exists():
        connection = json.loads(connection_file.read_text())
        if not re.fullmatch(r'http://127\.0\.0\.1:\d+/rpc',connection['url']):raise ValueError('Invalid local connection URL')
        request = urllib.request.Request(connection['url'], data=b'{"op":"status"}',
            headers={'Authorization': 'Bearer ' + connection['token'], 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=2):
                raise RuntimeError('A client already owns this directory: ' + str(directory))
        except (urllib.error.URLError, TimeoutError):
            pass
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'config').mkdir(exist_ok=True)
    (directory / 'config/fml.toml').write_text('earlyWindowControl=false\nversionCheck=false\n')
    (directory / 'options.txt').write_text('fullscreen:false\npauseOnLostFocus:false\nnarrator:0\nonboardAccessibility:false\nsoundCategory_master:0.0\nmaxFps:30\nenableVsync:false\nrenderDistance:8\nsimulationDistance:5\nskipMultiplayerWarning:true\n')
    env = os.environ.copy()
    env['JAVA_HOME'] = env.get('STRUCTURELAB_JAVA_HOME', r'C:\Program Files\Java\jdk-21.0.11')
    if not (Path(env['JAVA_HOME']) / 'bin/java.exe').is_file():
        raise RuntimeError('Set STRUCTURELAB_JAVA_HOME to a Java 21 installation')
    subprocess.run([str(ROOT / 'gradlew.bat'), 'exportLabLaunch', '--console=plain',
                    '-PlabHidden=true', '-PlabScenario=' + args.scenario,
                    '-PlabRunDirectory=' + str(directory)], cwd=ROOT, env=env, check=True)
    spec = json.loads((directory / 'launch.json').read_text())
    if args.jar:
        jar=args.jar.resolve()
        if not jar.is_file() or jar.suffix!='.jar':raise ValueError('Expected a built mod jar')
        (directory/'mods').mkdir(exist_ok=True)
        shutil.copy2(jar,directory/'mods'/jar.name)
        source_paths={str((ROOT/'build/classes/java/main').resolve()).lower(),str((ROOT/'build/resources/main').resolve()).lower()}
        spec['command']=[a for a in spec['command'] if not a.startswith('-Dfml.modFolders=')]
        index=spec['command'].index('-cp')+1
        spec['command'][index]=os.pathsep.join(p for p in spec['command'][index].split(os.pathsep) if p.lower() not in source_paths)
        (directory/'launch-packaged.json').write_text(json.dumps(spec,indent=2))
    env.update(spec['environment'])
    with (directory / 'process.log').open('w') as log:
        process = subprocess.Popen(spec['command'], cwd=directory, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    (directory / 'process.json').write_text(json.dumps({'pid': process.pid, 'directory': str(directory), 'scenario': args.scenario}, indent=2))
    print(json.dumps({'pid': process.pid, 'directory': str(directory)}), flush=True)
    if args.scenario == 'smoke':
        try:
            code = process.wait(timeout=240)
        except subprocess.TimeoutExpired:
            process.terminate()
            raise RuntimeError('Hidden smoke timed out; inspect process.log')
        log = (directory / 'process.log').read_text(errors='replace')
        if code or 'HIDDEN_CLIENT_PASS' not in log or not (directory / 'hidden-smoke.png').is_file():
            raise RuntimeError('Hidden smoke failed; inspect ' + str(directory / 'process.log'))
        print('Hidden framebuffer verified:', directory / 'hidden-smoke.png')
    else:
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('Hidden lab exited; inspect process.log')
            log=(directory/'process.log').read_text(errors='replace')
            if 'HIDDEN_LAB_READY' in log:
                print('Hidden lab ready:',connection_file,flush=True);break
            time.sleep(1)
        else:
            process.terminate()
            raise RuntimeError('Hidden lab startup timed out; inspect process.log')


if __name__ == '__main__':
    main()
