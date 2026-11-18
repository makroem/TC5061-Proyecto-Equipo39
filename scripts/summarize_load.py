"""Consolida los resultados finales del HTML de Locust y las muestras Docker."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
from mibici_equipo39.operations.finops import estimate


def parse_report(path):
    text=path.read_text(encoding="utf8")
    matches=list(re.finditer(r"window\.templateArgs\s*=",text))
    if len(matches)!=1:
        raise ValueError("No se identificó el bloque único de resultados Locust.")
    return json.JSONDecoder().raw_decode(text[matches[0].end():].lstrip())[0]


def memory_mib(text):
    value,unit=re.fullmatch(r"([0-9.]+)([A-Za-z]+)",text.strip().split(" / ")[0]).groups()
    factors={"B":1/2**20,"kB":1000/2**20,"MB":1000**2/2**20,"GB":1000**3/2**20,
             "KiB":1/1024,"MiB":1,"GiB":1024}
    return float(value)*factors[unit]


def write_csv(path,rows):
    with path.open("w",encoding="utf8",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="private_results/etapa6/load")
    parser.add_argument("--output",default="references/etapa6/mediciones_marco")
    args=parser.parse_args();source=Path(args.input);out=Path(args.output)
    out.mkdir(parents=True,exist_ok=False)
    (out/"locust").mkdir()
    runs=json.loads((source/"runs.json").read_text())
    protocol=json.loads((source/"protocol.json").read_text())
    if len(runs)!=len(protocol["profiles"])*protocol["repeats"]:
        raise ValueError("El protocolo está incompleto.")
    performance=[];resources=[];costs=[];hashes={};series={}
    for run in runs:
        name=run["run"]
        if not run["summary_exists"]:
            raise ValueError("Falta el resumen de "+name)
        summary=json.loads((source/(name+"_summary.json")).read_text())
        report=parse_report(source/(name+".html"))
        stats={s["name"]:s for s in report["requests_statistics"]}
        total=stats["Aggregated"]
        if total["num_requests"]!=summary["requests"] or total["num_failures"]!=summary["failures"]:
            raise ValueError("Discrepancia entre los resultados finales en "+name)
        row=dict(run= name,users=run["users"],repeat=run["repeat"],exit_code=run["exit_code"],
                 duration_seconds=summary["duration_seconds"],requests=summary["requests"],
                 failures=summary["failures"],successful_predictions=summary["successful_predictions"],
                 requests_per_second=summary["requests"]/summary["duration_seconds"],
                 predictions_per_second=summary["successful_predictions"]/summary["duration_seconds"],
                 p50_ms=summary["latency_p50_ms"],p95_ms=summary["latency_p95_ms"],
                 individual_p95_ms=stats["/predict lote=1"]["response_time_percentile_0.95"],
                 batch10_p95_ms=stats["/predict lote=10"]["response_time_percentile_0.95"],
                 batch10_request_share=stats["/predict lote=10"]["num_requests"]/summary["requests"])
        target=protocol["slo_peak_p95_ms"] if run["users"]==30 else protocol["slo_nominal_p95_ms"]
        row["slo_passed"]=(summary["failure_ratio"]<=protocol["slo_failure_ratio"] and max(row["individual_p95_ms"],row["batch10_p95_ms"])<=target)
        performance.append(row)
        samples=[]
        for line in (source/(name+"_resources.jsonl")).read_text().splitlines():
            sample=json.loads(line)
            if "sampling_error" in sample:continue
            if not summary["start_epoch"]<=sample["timestamp_epoch"]<=summary["end_epoch"]:continue
            service="locust" if "-locust-run-" in sample["Name"] else sample["Name"].split("-")[-2]
            samples.append(dict(service=service,seconds=sample["timestamp_epoch"]-summary["start_epoch"],
                                cpu_percent=float(sample["CPUPerc"].rstrip("%")),memory_mib=memory_mib(sample["MemUsage"])))
        if not samples:raise ValueError("No hay muestras de recursos en "+name)
        for service in ("api","mlflow","locust"):
            selected=[s for s in samples if s["service"]==service]
            if not selected:raise ValueError("Faltan recursos de "+service)
            resources.append(dict(run=name,users=run["users"],service=service,samples=len(selected),
                cpu_mean_sample=statistics.mean(s["cpu_percent"] for s in selected),
                cpu_max=max(s["cpu_percent"] for s in selected),memory_max_mib=max(s["memory_mib"] for s in selected)))
        series[name]=samples
        (out/"locust"/(name+".json")).write_text(json.dumps(report,indent=2),encoding="utf8")
        if run["repeat"]==1:shutil.copy2(source/(name+".html"),out/"locust"/(name+".html"))
        for utilization in (.1,.5,1.0):
            for tariff in (12,24,44):
                costs.append(dict(run=name,users=run["users"],slo_passed=row["slo_passed"],**estimate(tariff,summary["successful_predictions"],summary["duration_seconds"],utilization)))
        for file in sorted(source.glob(name+"*")):
            hashes[file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
    write_csv(out/"performance.csv",performance);write_csv(out/"resources.csv",resources);write_csv(out/"finops_sensitivity.csv",costs)
    shutil.copy2(source/"protocol.json",out/"protocol.json")
    (out/"source_sha256.json").write_text(json.dumps(hashes,indent=2),encoding="utf8")
    (out/"resource_series.json").write_text(json.dumps(series,indent=2),encoding="utf8")
    (out/"summary.json").write_text(json.dumps(dict(runs=performance,total_requests=sum(r["requests"] for r in performance),
        total_failures=sum(r["failures"] for r in performance),all_slo_passed=all(r["slo_passed"] for r in performance),
        status="medición de Marco pendiente de revisión independiente",cost_source="https://aws.amazon.com/lightsail/pricing/",
        tariff_checked="2026-11-17",cost_note="Los escenarios de tarifa mantienen rendimiento constante para aislar sensibilidad; no predicen capacidad de otra instancia.",
        data_note="Estadísticas finales del HTML y resumen al cierre; los CSV periódicos pueden terminar antes de las últimas respuestas."),indent=2,ensure_ascii=False),encoding="utf8")
    print(json.dumps(performance,indent=2))

if __name__=="__main__":main()
