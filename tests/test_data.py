"""Pruebas de Persona1 con archivos sintéticos aislados de los datos reales."""
import json
import sqlite3
from pathlib import Path
import pandas as pd
import pytest
from mibici_equipo39 import config as C
from mibici_equipo39.dataset import ingest, unique_chunk


def test_duplicate_conflicts_are_rejected():
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE seen (trip_id TEXT PRIMARY KEY, payload_hash TEXT)')
    frame = pd.DataFrame({'trip_id':['1','1'],'origin_id':['2','2']},dtype='string')
    result, removed = unique_chunk(frame,db)
    assert len(result)==1 and removed==1
    with pytest.raises(ValueError):
        unique_chunk(pd.DataFrame({'trip_id':['1'],'origin_id':['3']},dtype='string'),db)
    db.close()


def test_annual_ingestion_is_repeatable(tmp_path,monkeypatch):
    paths={'ROOT':tmp_path,'DATA':tmp_path/'data','RAW':tmp_path/'data/raw','EXTERNAL':tmp_path/'data/external','PROCESSED':tmp_path/'data/processed','INTERIM':tmp_path/'data/interim','REFERENCES':tmp_path/'references','REPORTS':tmp_path/'reports','FIGURES':tmp_path/'reports/figures'}
    for key,value in paths.items():monkeypatch.setattr(C,key,value)
    C.RAW.mkdir(parents=True);C.EXTERNAL.mkdir(parents=True)
    pd.DataFrame({'id':['2','3'],'name':['Dos','Tres'],'latitude':[20.6,20.7],'longitude':[-103.3,-103.4],'dpcapacity':[20,0]}).to_csv(C.EXTERNAL/Path(C.STATIONS_URL).name,index=False)
    for i,(month,url) in enumerate(C.SOURCE_URLS.items()):
        row={'Viaje_Id':str(i),'Usuario_Id':'NO_PUBLICAR','Inicio_del_viaje':month+'-02 10:00:00','Fin_del_viaje':month+'-02 10:20:00','Origen_Id':'2','Destino_Id':'3'}
        pd.DataFrame([row,row]).to_csv(C.RAW/Path(url).name,index=False)
    manifest=ingest('freeze')
    assert ingest('verify')==manifest
    quality=json.loads((C.REPORTS/'calidad_datos.json').read_text())
    assert quality['months']==12 and quality['raw_rows']==24 and quality['retained_rows']==12
    assert quality['valid_capacity_stations']==1
    frame=pd.read_parquet(next((C.PROCESSED/'trips').glob('month=*/part-*.parquet')))
    assert 'Usuario_Id' not in frame.columns
