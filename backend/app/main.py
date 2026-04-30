from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import SesionLocal, engine, Base
from .models import Usuario, Evento, Alerta, IpBloqueada, AccionUsuario
from .schemas import SolicitudInicioSesion

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def obtener_bd():
    bd = SesionLocal()
    try:
        yield bd
    finally:
        bd.close()


def registrar_accion(bd: Session, comando: str, resultado: str):
    accion = AccionUsuario(comando=comando, resultado=resultado)
    bd.add(accion)
    bd.commit()


@app.on_event("startup")
def iniciar_sistema():
    bd = SesionLocal()
    usuario = bd.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
    if not usuario:
        bd.add(Usuario(nombre_usuario="admin", contrasena="admin123"))
        bd.commit()
    bd.close()


@app.get("/")
def raiz():
    return {"mensaje": "Backend funcionando"}


@app.post("/iniciar-sesion")
def iniciar_sesion(datos: SolicitudInicioSesion, bd: Session = Depends(obtener_bd)):
    usuario = bd.query(Usuario).filter(
        Usuario.nombre_usuario == datos.nombre_usuario,
        Usuario.contrasena == datos.contrasena
    ).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return {
        "mensaje": "Inicio de sesión correcto",
        "nombre_usuario": usuario.nombre_usuario
    }


@app.post("/simular/fuerza-bruta")
def simular_fuerza_bruta(bd: Session = Depends(obtener_bd)):
    ip = "192.168.1.50"

    bloqueada = bd.query(IpBloqueada).filter(IpBloqueada.direccion_ip == ip).first()
    if bloqueada:
        return {
            "mensaje": f"Simulación detenida: la IP {ip} está bloqueada",
            "tipo_ataque": "Fuerza Bruta",
            "ip": ip,
            "titulo_caso": "Intentos de autenticación sospechosos",
            "texto_caso": (
                f"Se detectó actividad desde la IP {ip}, pero el laboratorio ya "
                f"tiene esa dirección bloqueada. Verifica el estado con 'ver bloqueadas' "
                f"o desbloquéala con 'desbloquear ip {ip}' si quieres repetir el caso."
            ),
            "siguiente_paso": f"Usa 'ver bloqueadas' o 'desbloquear ip {ip}'"
        }

    for i in range(1, 11):
        evento = Evento(
            tipo_evento="Fuerza Bruta",
            ip_origen=ip,
            descripcion=f"Intento fallido de inicio de sesión #{i}"
        )
        bd.add(evento)
        bd.commit()

    intentos = bd.query(Evento).filter(Evento.ip_origen == ip).count()

    if intentos >= 5:
        alerta = Alerta(
            titulo="Ataque de fuerza bruta detectado",
            severidad="Alta",
            descripcion=f"Se detectaron {intentos} intentos fallidos desde la IP {ip}"
        )
        bd.add(alerta)
        bd.commit()

    return {
        "mensaje": f"Simulación ejecutada - {intentos} intentos detectados",
        "tipo_ataque": "Fuerza Bruta",
        "ip": ip,
        "titulo_caso": "Caso activo: fuerza bruta sobre autenticación",
        "texto_caso": (
            f"El sistema detectó múltiples intentos fallidos de inicio de sesión "
            f"desde la IP {ip}. Tu rol es investigar el incidente y contenerlo."
        ),
        "siguiente_paso": "Usa 'ver alertas' o 'ver eventos' para comenzar el análisis."
    }


@app.post("/simular/escaneo-puertos")
def simular_escaneo_puertos(bd: Session = Depends(obtener_bd)):
    ip = "192.168.1.99"

    bloqueada = bd.query(IpBloqueada).filter(IpBloqueada.direccion_ip == ip).first()
    if bloqueada:
        return {
            "mensaje": f"Simulación detenida: la IP {ip} está bloqueada",
            "tipo_ataque": "Escaneo de Puertos",
            "ip": ip,
            "titulo_caso": "Reconocimiento de servicios bloqueado",
            "texto_caso": (
                f"La IP {ip} ya se encuentra bloqueada. El escaneo no pudo continuar."
            ),
            "siguiente_paso": f"Usa 'ver bloqueadas' o 'desbloquear ip {ip}'"
        }

    puertos = [21, 22, 25, 53, 80, 110, 139, 143, 443, 3306]

    for puerto in puertos:
        evento = Evento(
            tipo_evento="Escaneo de Puertos",
            ip_origen=ip,
            descripcion=f"Intento de escaneo al puerto {puerto}"
        )
        bd.add(evento)
        bd.commit()

    total_escaneos = bd.query(Evento).filter(
        Evento.ip_origen == ip,
        Evento.tipo_evento == "Escaneo de Puertos"
    ).count()

    if total_escaneos >= 5:
        alerta = Alerta(
            titulo="Escaneo de puertos detectado",
            severidad="Media",
            descripcion=f"La IP {ip} realizó múltiples intentos de escaneo de puertos"
        )
        bd.add(alerta)
        bd.commit()

    return {
        "mensaje": f"Escaneo de puertos simulado - {len(puertos)} puertos analizados",
        "tipo_ataque": "Escaneo de Puertos",
        "ip": ip,
        "titulo_caso": "Caso activo: reconocimiento de servicios",
        "texto_caso": (
            f"Se observó actividad de reconocimiento desde la IP {ip}. "
            f"Alguien está enumerando puertos para identificar servicios expuestos."
        ),
        "siguiente_paso": "Usa 'ver eventos' para revisar los puertos atacados."
    }


@app.get("/estadisticas")
def obtener_estadisticas(bd: Session = Depends(obtener_bd)):
    total_eventos = bd.query(Evento).count()
    total_alertas = bd.query(Alerta).count()

    eventos_recientes = bd.query(Evento).order_by(Evento.id.desc()).limit(10).all()
    alertas_recientes = bd.query(Alerta).order_by(Alerta.id.desc()).limit(10).all()

    return {
        "total_eventos": total_eventos,
        "total_alertas": total_alertas,
        "eventos_recientes": [
            {
                "id": evento.id,
                "tipo_evento": evento.tipo_evento,
                "ip_origen": evento.ip_origen,
                "descripcion": evento.descripcion,
                "fecha_creacion": evento.fecha_creacion
            }
            for evento in eventos_recientes
        ],
        "alertas_recientes": [
            {
                "id": alerta.id,
                "titulo": alerta.titulo,
                "severidad": alerta.severidad,
                "descripcion": alerta.descripcion,
                "fecha_creacion": alerta.fecha_creacion
            }
            for alerta in alertas_recientes
        ]
    }


@app.get("/reporte")
def obtener_reporte(bd: Session = Depends(obtener_bd)):
    total_eventos = bd.query(Evento).count()
    total_alertas = bd.query(Alerta).count()
    ips_bloqueadas = bd.query(IpBloqueada).order_by(IpBloqueada.id.desc()).all()
    acciones = bd.query(AccionUsuario).order_by(AccionUsuario.id.asc()).all()

    return {
        "total_eventos": total_eventos,
        "total_alertas": total_alertas,
        "ips_bloqueadas": [
            {
                "direccion_ip": ip.direccion_ip,
                "motivo": ip.motivo,
                "fecha_creacion": ip.fecha_creacion
            }
            for ip in ips_bloqueadas
        ],
        "acciones": [
            {
                "comando": accion.comando,
                "resultado": accion.resultado,
                "fecha_creacion": accion.fecha_creacion
            }
            for accion in acciones
        ]
    }


@app.post("/terminal")
def ejecutar_comando_terminal(datos_comando: dict, bd: Session = Depends(obtener_bd)):
    comando = datos_comando.get("comando", "").strip().lower()

    if not comando:
        return {"salida": "Comando vacío"}

    if comando == "ayuda":
        registrar_accion(bd, comando, "OK")
        return {
            "salida": (
                "Comandos disponibles:\n"
                "ayuda\n"
                "estado\n"
                "ver alertas\n"
                "ver eventos\n"
                "ver bloqueadas\n"
                "bloquear ip <ip>\n"
                "desbloquear ip <ip>\n"
                "limpiar"
            )
        }

    if comando == "estado":
        total_eventos = bd.query(Evento).count()
        total_alertas = bd.query(Alerta).count()
        total_bloqueadas = bd.query(IpBloqueada).count()

        registrar_accion(bd, comando, "OK")
        return {
            "salida": (
                f"Estado del sistema:\n"
                f"- Eventos registrados: {total_eventos}\n"
                f"- Alertas generadas: {total_alertas}\n"
                f"- IPs bloqueadas: {total_bloqueadas}\n"
                f"- Laboratorio: operativo"
            )
        }

    if comando == "ver alertas":
        alertas = bd.query(Alerta).order_by(Alerta.id.desc()).limit(5).all()
        registrar_accion(bd, comando, "OK")

        if not alertas:
            return {"salida": "No hay alertas registradas"}

        lineas = ["Últimas alertas:"]
        for alerta in alertas:
            lineas.append(f"[{alerta.severidad}] {alerta.titulo} - {alerta.descripcion}")

        return {"salida": "\n".join(lineas)}

    if comando == "ver eventos":
        eventos = bd.query(Evento).order_by(Evento.id.desc()).limit(10).all()
        registrar_accion(bd, comando, "OK")

        if not eventos:
            return {"salida": "No hay eventos registrados"}

        lineas = ["Últimos eventos:"]
        for evento in eventos:
            lineas.append(f"{evento.tipo_evento} | {evento.ip_origen} | {evento.descripcion}")

        return {"salida": "\n".join(lineas)}

    if comando == "ver bloqueadas":
        bloqueadas = bd.query(IpBloqueada).order_by(IpBloqueada.id.desc()).all()
        registrar_accion(bd, comando, "OK")

        if not bloqueadas:
            return {"salida": "No hay IPs bloqueadas"}

        lineas = ["IPs bloqueadas:"]
        for ip in bloqueadas:
            lineas.append(f"{ip.direccion_ip} - {ip.motivo}")

        return {"salida": "\n".join(lineas)}

    if comando.startswith("bloquear ip "):
        ip = comando.replace("bloquear ip ", "").strip()

        if not ip:
            return {"salida": "Debes indicar una IP"}

        existente = bd.query(IpBloqueada).filter(IpBloqueada.direccion_ip == ip).first()
        if existente:
            return {"salida": f"La IP {ip} ya está bloqueada"}

        bd.add(IpBloqueada(direccion_ip=ip, motivo="Bloqueo manual"))
        bd.commit()
        registrar_accion(bd, comando, "OK")

        return {"salida": f"IP {ip} bloqueada correctamente"}

    if comando.startswith("desbloquear ip "):
        ip = comando.replace("desbloquear ip ", "").strip()

        existente = bd.query(IpBloqueada).filter(IpBloqueada.direccion_ip == ip).first()
        if not existente:
            return {"salida": f"La IP {ip} no está bloqueada"}

        bd.delete(existente)
        bd.commit()
        registrar_accion(bd, comando, "OK")

        return {"salida": f"IP {ip} desbloqueada correctamente"}

    if comando == "limpiar":
        registrar_accion(bd, comando, "OK")
        return {"salida": "__LIMPIAR__"}

    return {"salida": f"Comando no reconocido: {comando}"}