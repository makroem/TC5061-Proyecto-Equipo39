"""Ejecuta un protocolo local acotado y registra recursos sin rutas privadas."""
import argparse
import hashlib
import csv
import json
import os
from pathlib import Path
import subprocess
import threading
import time
from datetime import datetime, timezone
from scripts.summarize_load import parse_report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--docker',default='docker')
    parser.add_argument('--seconds',type=int,default=90)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--output',default='private_results/etapa6/load')
    args=parser.parse_args()
    if args.seconds<30 or not 1<=args.repeats<=5:
        raise SystemExit('Duración mínima 30 segundos; entre una y cinco repeticiones.')
    destination=Path(args.output)
    if destination.is_absolute() or '..' in destination.parts or destination.parts[:2]!=('private_results','etapa6'):
        raise SystemExit('El destino debe quedar dentro de private_results/etapa6.')
    if destination.exists():
        raise SystemExit('El destino existe; elegir otro para conservar las mediciones.')
    destination.mkdir(parents=True)
    def docker(*command,**kwargs):
        return subprocess.run([args.docker,*command],check=True,text=True,capture_output=True,**kwargs)
    manifest=json.loads(Path('references/etapa4/model_manifest.json').read_text(encoding='utf8'))
    engine=json.loads(docker('info','--format','{{json .}}').stdout)
    profiles=[(1,1),(10,2),(30,5)]
    commit=subprocess.check_output(['git','-c','safe.directory='+Path.cwd().as_posix(),'rev-parse','HEAD'],text=True).strip()
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('docker-compose.yml'),Path('tests/load/locustfile.py'),Path('scripts/run_load.py')]}
    protocol={'source_commit':commit,'source_sha256':hashes,'api_image_id':docker('image','inspect','mibici-equipo39:etapa6','--format','{{.Id}}').stdout.strip(),'created_utc':datetime.now(timezone.utc).isoformat(),'duration_seconds':args.seconds,
              'repeats':args.repeats,'profiles':[{'users':u,'spawn_rate':s} for u,s in profiles],
              'warmup_seconds':30,'think_time_seconds':[.1,.5], 'task_weights':{'one':4,'ten':1},
              'model_bundle_sha256':manifest['bundle_sha256'],'model_version':manifest['model_version'],
              'docker_version':engine['ServerVersion'],'engine_cpus':engine['NCPU'],
              'engine_memory_bytes':engine['MemTotal'],'metrics_interval_target_seconds':2,
              'slo_failure_ratio':.001,'slo_nominal_p95_ms':250,'slo_peak_p95_ms':1000,
              'scope':'medición local exploratoria; no equivale a capacidad de nube',
              'generator_shares_host':True}
    (destination/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf8')
    def load(name,users,spawn,seconds):
        prefix='/results/'+destination.relative_to('private_results/etapa6').as_posix()+'/'+name
        command=[args.docker,'compose','--profile','load','run','--rm','--no-deps',
                 '-e','LOAD_SUMMARY='+prefix+'_summary.json',
                 '-e','EXPECTED_MODEL_NAME='+manifest['model_name'],
                 '-e','EXPECTED_MODEL_VERSION='+str(manifest['model_version']),
                 '-e','EXPECTED_BUNDLE_SHA256='+manifest['bundle_sha256'],
                 'locust','-f','tests/load/locustfile.py','--host','http://api:8000',
                 '--headless','--users',str(users),'--spawn-rate',str(spawn),'--run-time',str(seconds)+'s',
                 '--stop-timeout','10','--html',prefix+'.html']
        with (destination/(name+'.log')).open('w',encoding='utf8') as log:
            code=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
        report_path=destination/(name+'.html')
        if report_path.exists():
            final=parse_report(report_path)['requests_statistics']
            with (destination/(name+'_stats.csv')).open('w',encoding='utf8',newline='') as out:
                writer=csv.DictWriter(out,fieldnames=list(final[0]));writer.writeheader();writer.writerows(final)
        return code
    print('Calentamiento de 30 segundos.',flush=True)
    if load('warmup',1,1,30)!=0:
        raise SystemExit('Falló el calentamiento; revisar su registro.')
    results=[]
    for repeat in range(1,args.repeats+1):
        for users,spawn in profiles:
            name=f'u{users:02d}_r{repeat}'
            stop=threading.Event()
            def sample():
                with (destination/(name+'_resources.jsonl')).open('w',encoding='utf8') as output:
                    while not stop.is_set():
                        try:
                            ids=docker('ps','--filter','label=com.docker.compose.project=e39-etapa6','--format','{{.ID}}').stdout.split()
                            if ids:
                                raw=docker('stats','--no-stream','--format','{{json .}}',*ids).stdout
                                now=time.time()
                                for line in raw.splitlines():
                                    value=json.loads(line);value['timestamp_epoch']=now
                                    output.write(json.dumps(value)+'\n')
                                output.flush()
                        except (subprocess.SubprocessError,ValueError) as error:
                            output.write(json.dumps({'sampling_error':type(error).__name__,'timestamp_epoch':time.time()})+'\n')
                        stop.wait(2)
            worker=threading.Thread(target=sample,daemon=True);worker.start()
            print(f'Perfil {users} usuarios, repetición {repeat}.',flush=True)
            code=load(name,users,spawn,args.seconds)
            stop.set();worker.join(timeout=30)
            summary=destination/(name+'_summary.json')
            results.append({'run':name,'users':users,'repeat':repeat,'exit_code':code,'summary_exists':summary.exists()})
            (destination/'runs.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print(json.dumps(results),flush=True)
    if any(r['exit_code']!=0 or not r['summary_exists'] for r in results):
        raise SystemExit('Hay ejecuciones con errores; no declarar aprobación global.')

if __name__=='__main__':
    main()
