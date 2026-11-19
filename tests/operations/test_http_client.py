import json
import pytest
from mibici_equipo39.operations import http_client

@pytest.mark.parametrize("url",["file:///tmp/model","ftp://localhost","http:///missing","https://u:p@localhost","http://localhost?secret=x","http://localhost#x","localhost:8006","data:text/plain,test"])
def test_rejects_non_http_or_ambiguous_urls_before_connecting(url,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError("No debe abrir una conexión")
    monkeypatch.setattr(http_client.http.client,"HTTPConnection",forbidden)
    monkeypatch.setattr(http_client.http.client,"HTTPSConnection",forbidden)
    with pytest.raises(ValueError):http_client.json_request(url,"/ready")

@pytest.mark.parametrize("status",[200,422])
def test_post_uses_requested_host_and_closes_connection(status,monkeypatch):
    calls=[]
    class Response:
        def read(self,limit):return b'{"status":"ok"}'
    response=Response();response.status=status
    class Connection:
        def __init__(self,host,port,timeout):calls.append((host,port,timeout))
        def request(self,method,path,body,headers):calls.append((method,path,json.loads(body)))
        def getresponse(self):return response
        def close(self):calls.append("closed")
    monkeypatch.setattr(http_client.http.client,"HTTPConnection",Connection)
    if status==200:assert http_client.json_request("http://127.0.0.1:8006","/predict",{"instances":[]})=={"status":"ok"}
    else:
        with pytest.raises(http_client.HTTPStatusError) as error:http_client.json_request("http://127.0.0.1:8006","/predict",{"instances":[]})
        assert error.value.status==422
    assert calls[0]==("127.0.0.1",8006,20)
    assert calls[1]==("POST","/predict",{"instances":[]})
    assert calls[-1]=="closed"
