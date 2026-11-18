"""Cliente de comprobación limitado a HTTP y HTTPS, sin redirecciones."""
import http.client
import json
from urllib.parse import urlsplit

class HTTPStatusError(RuntimeError):
    def __init__(self, status):
        self.status=status
        super().__init__(f"Respuesta HTTP {status}")

def json_request(base_url, path, data=None):
    url=urlsplit(base_url)
    if url.scheme not in ("http","https") or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Se requiere una URL HTTP o HTTPS sin credenciales, consulta ni fragmento.")
    if not path.startswith("/"):
        raise ValueError("El endpoint debe comenzar por una diagonal.")
    factory=http.client.HTTPSConnection if url.scheme=="https" else http.client.HTTPConnection
    connection=factory(url.hostname,url.port,timeout=20)
    try:
        payload=None if data is None else json.dumps(data).encode()
        connection.request("GET" if data is None else "POST",url.path.rstrip("/")+path,body=payload,
                           headers={"Content-Type":"application/json"})
        response=connection.getresponse()
        if not 200<=response.status<300:
            raise HTTPStatusError(response.status)
        body=response.read(1048577)
        if len(body)>1048576:raise ValueError("Respuesta demasiado grande.")
        return json.loads(body)
    finally:
        connection.close()
