"""Servicio local de demanda P1; carga una versión verificada al iniciar el proceso."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .model_loader import load_model
from .predictor import predict_request
from .schemas import PredictionRequest, PredictionResponse, ServiceError, ValidationResponse
from .settings import Settings

logger = logging.getLogger(__name__)


def create_app(settings=None, model_loader=load_model):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(service):
        service.state.model = None
        try:
            service.state.model = model_loader(settings.model_dir, settings.model_manifest)
        except Exception as exc:
            # El cliente recibe 503; el operador identifica el tipo sin publicar rutas o secretos.
            logger.error('Modelo no disponible al iniciar (%s).', type(exc).__name__)
        try:
            yield
        finally:
            service.state.model = None

    service = FastAPI(title='MiBici Equipo39 - Demanda P1', version='1.0.0', lifespan=lifespan)
    service.state.model = None

    @service.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # No reflejar el cuerpo recibido ni valores no finitos en la respuesta de error.
        errors = [{key: error[key] for key in ('loc', 'msg', 'type')}
                  for error in exc.errors()]
        return JSONResponse(status_code=422, content={'detail': errors})

    @service.get('/health')
    def health():
        return {'status': 'ok'}

    @service.get('/ready', responses={503: {'model': ServiceError}})
    def ready():
        loaded = service.state.model
        if loaded is None:
            raise HTTPException(status_code=503, detail='Modelo no disponible.')
        return {'status': 'ready', 'model_name': loaded.manifest['model_name'],
                'model_version': str(loaded.manifest['model_version']),
                'model_bundle_sha256': loaded.manifest['bundle_sha256']}

    @service.post('/predict', response_model=PredictionResponse, responses={
        422: {'model': ValidationResponse}, 503: {'model': ServiceError}, 500: {'model': ServiceError}})
    def predict(body: PredictionRequest):
        loaded = service.state.model
        if loaded is None:
            raise HTTPException(status_code=503, detail='Modelo no disponible.')
        try:
            return predict_request(loaded, body)
        except Exception as exc:
            logger.error('Prediccion no completada (%s).', type(exc).__name__)
            raise HTTPException(status_code=500, detail='No se pudo completar la prediccion.') from None

    return service


app = create_app()
