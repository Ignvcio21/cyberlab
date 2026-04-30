from pydantic import BaseModel


class SolicitudInicioSesion(BaseModel):
    nombre_usuario: str
    contrasena: str