from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from .models import User, Event, Alert, BlockedIP, UserAction
from .schemas import LoginRequest

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def register_action(db: Session, command: str, result: str):
    action = UserAction(command=command, result=result)
    db.add(action)
    db.commit()


@app.on_event("startup")
def startup():
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        db.add(User(username="admin", password="admin123"))
        db.commit()
    db.close()


@app.get("/")
def root():
    return {"message": "Backend funcionando"}


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == data.username,
        User.password == data.password
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return {"message": "Login correcto", "username": user.username}


@app.post("/simulate/bruteforce")
def simulate_bruteforce(db: Session = Depends(get_db)):
    ip = "192.168.1.50"

    blocked = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
    if blocked:
        return {
            "message": f"Simulación detenida: la IP {ip} está bloqueada",
            "attack_type": "Fuerza Bruta",
            "ip": ip,
            "case_title": "Intentos de autenticación sospechosos",
            "case_text": (
                f"Se detectó actividad desde la IP {ip}, pero el laboratorio ya "
                f"tiene esa dirección bloqueada. Verifica el estado con 'show blocked' "
                f"o desbloquéala con 'unblock ip {ip}' si quieres repetir el caso."
            ),
            "next_step": f"Usa 'show blocked' o 'unblock ip {ip}'"
        }

    for i in range(1, 11):
        event = Event(
            event_type="Fuerza Bruta",
            source_ip=ip,
            description=f"Intento fallido de login #{i}"
        )
        db.add(event)
        db.commit()

    attempts = db.query(Event).filter(Event.source_ip == ip).count()

    if attempts >= 5:
        alert = Alert(
            title="Ataque de fuerza bruta detectado",
            severity="Alta",
            description=f"Se detectaron {attempts} intentos fallidos desde la IP {ip}"
        )
        db.add(alert)
        db.commit()

    return {
        "message": f"Simulación ejecutada - {attempts} intentos detectados",
        "attack_type": "Fuerza Bruta",
        "ip": ip,
        "case_title": "Caso activo: fuerza bruta sobre autenticación",
        "case_text": (
            f"El sistema detectó múltiples intentos fallidos de inicio de sesión "
            f"desde la IP {ip}. Tu rol es investigar el incidente y contenerlo."
        ),
        "next_step": "Usa 'show alerts' o 'show events' para comenzar el análisis."
    }


@app.post("/simulate/portscan")
def simulate_portscan(db: Session = Depends(get_db)):
    ip = "192.168.1.99"

    blocked = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
    if blocked:
        return {
            "message": f"Simulación detenida: la IP {ip} está bloqueada",
            "attack_type": "Escaneo de Puertos",
            "ip": ip,
            "case_title": "Reconocimiento de servicios bloqueado",
            "case_text": (
                f"La IP {ip} ya se encuentra bloqueada. El escaneo no pudo continuar."
            ),
            "next_step": f"Usa 'show blocked' o 'unblock ip {ip}'"
        }

    ports = [21, 22, 25, 53, 80, 110, 139, 143, 443, 3306]

    for port in ports:
        event = Event(
            event_type="Escaneo de Puertos",
            source_ip=ip,
            description=f"Intento de escaneo al puerto {port}"
        )
        db.add(event)
        db.commit()

    total_scans = db.query(Event).filter(
        Event.source_ip == ip,
        Event.event_type == "Escaneo de Puertos"
    ).count()

    if total_scans >= 5:
        alert = Alert(
            title="Escaneo de puertos detectado",
            severity="Media",
            description=f"La IP {ip} realizó múltiples intentos de escaneo de puertos"
        )
        db.add(alert)
        db.commit()

    return {
        "message": f"Escaneo de puertos simulado - {len(ports)} puertos analizados",
        "attack_type": "Escaneo de Puertos",
        "ip": ip,
        "case_title": "Caso activo: reconocimiento de servicios",
        "case_text": (
            f"Se observó actividad de reconocimiento desde la IP {ip}. "
            f"Alguien está enumerando puertos para identificar servicios expuestos."
        ),
        "next_step": "Usa 'show events' para revisar los puertos atacados."
    }


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    total_events = db.query(Event).count()
    total_alerts = db.query(Alert).count()

    recent_events = db.query(Event).order_by(Event.id.desc()).limit(10).all()
    recent_alerts = db.query(Alert).order_by(Alert.id.desc()).limit(10).all()

    return {
        "total_events": total_events,
        "total_alerts": total_alerts,
        "recent_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "source_ip": e.source_ip,
                "description": e.description,
                "created_at": e.created_at
            }
            for e in recent_events
        ],
        "recent_alerts": [
            {
                "id": a.id,
                "title": a.title,
                "severity": a.severity,
                "description": a.description,
                "created_at": a.created_at
            }
            for a in recent_alerts
        ]
    }


@app.get("/report")
def report(db: Session = Depends(get_db)):
    total_events = db.query(Event).count()
    total_alerts = db.query(Alert).count()
    blocked_ips = db.query(BlockedIP).order_by(BlockedIP.id.desc()).all()
    actions = db.query(UserAction).order_by(UserAction.id.asc()).all()

    return {
        "total_events": total_events,
        "total_alerts": total_alerts,
        "blocked_ips": [
            {
                "ip_address": ip.ip_address,
                "reason": ip.reason,
                "created_at": ip.created_at
            }
            for ip in blocked_ips
        ],
        "actions": [
            {
                "command": action.command,
                "result": action.result,
                "created_at": action.created_at
            }
            for action in actions
        ]
    }


@app.post("/terminal")
def terminal_command(command_data: dict, db: Session = Depends(get_db)):
    command = command_data.get("command", "").strip().lower()

    if not command:
        return {"output": "Comando vacío"}

    if command == "help":
        register_action(db, command, "OK")
        return {
            "output": (
                "Comandos disponibles:\n"
                "help\n"
                "status\n"
                "show alerts\n"
                "show events\n"
                "show blocked\n"
                "block ip <ip>\n"
                "unblock ip <ip>\n"
                "clear"
            )
        }

    if command == "status":
        total_events = db.query(Event).count()
        total_alerts = db.query(Alert).count()
        total_blocked = db.query(BlockedIP).count()

        register_action(db, command, "OK")
        return {
            "output": (
                f"Estado del sistema:\n"
                f"- Eventos registrados: {total_events}\n"
                f"- Alertas generadas: {total_alerts}\n"
                f"- IPs bloqueadas: {total_blocked}\n"
                f"- Laboratorio: operativo"
            )
        }

    if command == "show alerts":
        alerts = db.query(Alert).order_by(Alert.id.desc()).limit(5).all()
        register_action(db, command, "OK")

        if not alerts:
            return {"output": "No hay alertas registradas"}

        lines = ["Últimas alertas:"]
        for alert in alerts:
            lines.append(f"[{alert.severity}] {alert.title} - {alert.description}")

        return {"output": "\n".join(lines)}

    if command == "show events":
        events = db.query(Event).order_by(Event.id.desc()).limit(10).all()
        register_action(db, command, "OK")

        if not events:
            return {"output": "No hay eventos registrados"}

        lines = ["Últimos eventos:"]
        for event in events:
            lines.append(f"{event.event_type} | {event.source_ip} | {event.description}")

        return {"output": "\n".join(lines)}

    if command == "show blocked":
        blocked = db.query(BlockedIP).order_by(BlockedIP.id.desc()).all()
        register_action(db, command, "OK")

        if not blocked:
            return {"output": "No hay IPs bloqueadas"}

        lines = ["IPs bloqueadas:"]
        for ip in blocked:
            lines.append(f"{ip.ip_address} - {ip.reason}")

        return {"output": "\n".join(lines)}

    if command.startswith("block ip "):
        ip = command.replace("block ip ", "").strip()

        if not ip:
            return {"output": "Debes indicar una IP"}

        existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
        if existing:
            return {"output": f"La IP {ip} ya está bloqueada"}

        db.add(BlockedIP(ip_address=ip, reason="Bloqueo manual"))
        db.commit()
        register_action(db, command, "OK")

        return {"output": f"IP {ip} bloqueada correctamente"}

    if command.startswith("unblock ip "):
        ip = command.replace("unblock ip ", "").strip()

        existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
        if not existing:
            return {"output": f"La IP {ip} no está bloqueada"}

        db.delete(existing)
        db.commit()
        register_action(db, command, "OK")

        return {"output": f"IP {ip} desbloqueada correctamente"}

    if command == "clear":
        register_action(db, command, "OK")
        return {"output": "__CLEAR__"}

    return {"output": f"Comando no reconocido: {command}"}