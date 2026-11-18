"""Gráficas de resultados medidos sin alterar los reportes originales."""
import argparse
import csv
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--input",default="references/etapa6/mediciones_marco")
    args=parser.parse_args();root=Path(args.input)
    rows=list(csv.DictReader((root/"performance.csv").open(encoding="utf8")))
    resources=list(csv.DictReader((root/"resources.csv").open(encoding="utf8")))
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    users=[1,10,30];colors=["#145A86","#16837C","#B45F28"]
    fig,axes=plt.subplots(2,2,figsize=(11,7.5),layout="constrained")
    for ax,key,title,ylabel in [(axes[0,0],"requests_per_second","Rendimiento de solicitudes","Solicitudes por segundo"),
            (axes[0,1],"predictions_per_second","Inferencias útiles","Predicciones por segundo"),
            (axes[1,0],"p95_ms","Latencia p95 de todas las solicitudes","Milisegundos"),
            (axes[1,1],"failures","Fallos observados","Número de fallos")]:
        values=[[float(r[key]) for r in rows if int(r["users"])==u] for u in users]
        for i,(group,color) in enumerate(zip(values,colors)):
            ax.scatter([i]*len(group),group,color=color,s=25,zorder=3)
            ax.plot([i-.17,i+.17],[statistics.median(group)]*2,color=color,lw=3)
            ax.vlines(i,min(group),max(group),color=color,alpha=.6)
        ax.set_xticks(range(3),[str(u) for u in users]);ax.set_xlabel("Usuarios concurrentes")
        ax.set_ylabel(ylabel);ax.set_title(title);ax.set_ylim(bottom=0);ax.grid(axis="y",alpha=.2)
        if key=="failures":ax.set_ylim(-.05,1);ax.set_yticks([0,1])
    fig.suptitle("P1 en Compose — tres repeticiones por perfil",fontsize=15)
    fig.savefig(root/"rendimiento_latencia.png",dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),layout="constrained")
    for service,color in zip(["api","mlflow","locust"],colors):
        for ax,key in [(axes[0],"cpu_mean_sample"),(axes[1],"memory_max_mib")]:
            groups=[[float(r[key]) for r in resources if r["service"]==service and int(r["users"])==u] for u in users]
            median=[statistics.median(g) for g in groups]
            ax.plot(users,median,"o-",color=color,label=service)
            ax.fill_between(users,[min(g) for g in groups],[max(g) for g in groups],color=color,alpha=.12)
    axes[0].set_title("CPU media de las muestras");axes[0].set_ylabel("Porcentaje informado por Docker")
    axes[1].set_title("Máximo de memoria por ejecución");axes[1].set_ylabel("MiB")
    for ax in axes:
        ax.set_xlabel("Usuarios concurrentes");ax.set_xticks(users);ax.set_ylim(bottom=0);ax.grid(alpha=.2);ax.legend()
    fig.suptitle("Recursos locales — mediana y rango de tres repeticiones",fontsize=14)
    fig.savefig(root/"recursos.png",dpi=160);plt.close(fig)
    report=json.loads((root/"locust/u30_r1.json").read_text())
    history=report["history"]
    fig,axes=plt.subplots(2,1,figsize=(11,6),sharex=True,layout="constrained")
    x=list(range(len(history)))
    for ax,key,label,color in [(axes[0],"current_rps","Solicitudes/s en ventana móvil",colors[0]),
                              (axes[1],"response_time_percentile_0.95","Latencia p95 en ms en ventana móvil",colors[2])]:
        ax.plot(x,[h[key][1] or 0 for h in history],color=color,lw=1.8);ax.set_ylabel(label);ax.grid(alpha=.2)
    labels=[h["time"][11:19] for h in history];ticks=list(range(0,len(x),max(1,len(x)//6)))
    axes[1].set_xticks(ticks,[labels[i] for i in ticks]);axes[1].set_xlabel("Hora UTC del reporte original")
    fig.suptitle("Locust — perfil de 30 usuarios, repetición 1",fontsize=14)
    fig.savefig(root/"locust_serie_30_usuarios.png",dpi=160);plt.close(fig)
    print("Tres gráficas guardadas a partir de los resultados verificados.")

if __name__=="__main__":main()
