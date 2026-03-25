"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"

export default function Dashboard() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [stats, setStats] = useState({
    total_events: 0,
    total_alerts: 0,
    recent_events: [],
    recent_alerts: []
  })
  const [message, setMessage] = useState("")
  const [command, setCommand] = useState("")
  const [startTime, setStartTime] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [report, setReport] = useState(null)
  const [validCommands, setValidCommands] = useState([])
  const [terminalHistory, setTerminalHistory] = useState([
    "CyberLab Interactive Terminal v1.0",
    "Escribe 'help' para ver los comandos disponibles."
  ])
  const [activeScenario, setActiveScenario] = useState(null)
  const [missionState, setMissionState] = useState("idle")
  const [missionText, setMissionText] = useState(
    "No hay misión activa. Ejecuta una simulación para comenzar."
  )
  const [missionChecklist, setMissionChecklist] = useState({
    reviewedAlerts: false,
    reviewedEvents: false,
    blockedIp: false
  })

  const validCommandPrefixes = useMemo(
    () => [
      "help",
      "status",
      "show alerts",
      "show events",
      "show blocked",
      "block ip ",
      "unblock ip ",
      "clear"
    ],
    []
  )

  const loadStats = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/stats")
      const data = await res.json()
      setStats(data)
    } catch {
      setMessage("No se pudieron cargar las estadísticas")
    }
  }

  const startSessionIfNeeded = () => {
    if (!startTime) {
      setStartTime(Date.now())
      setReport(null)
    }
  }

  const scrollToMission = () => {
    setTimeout(() => {
      document.querySelector(".mission-panel")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      })
    }, 100)
  }

  const startScenario = (data) => {
    setActiveScenario({
      type: data.attack_type,
      ip: data.ip
    })
    setMissionState("attack_started")
    setMissionChecklist({
      reviewedAlerts: false,
      reviewedEvents: false,
      blockedIp: false
    })
    setMissionText(
      `🚨 ${data.case_title}\n\n${data.case_text}\n\nQué debes hacer ahora:\n${data.next_step}`
    )
    scrollToMission()
  }

  const simulateAttack = async () => {
    startSessionIfNeeded()

    try {
      const res = await fetch("http://127.0.0.1:8000/simulate/bruteforce", {
        method: "POST"
      })
      const data = await res.json()
      setMessage(data.message)
      loadStats()
      setTerminalHistory((prev) => [
        ...prev,
        "> system: simulación de fuerza bruta ejecutada",
        data.message
      ])
      startScenario(data)
    } catch {
      setMessage("No se pudo ejecutar la simulación")
      setTerminalHistory((prev) => [
        ...prev,
        "> system: error al ejecutar simulación de fuerza bruta"
      ])
    }
  }

  const simulatePortScan = async () => {
    startSessionIfNeeded()

    try {
      const res = await fetch("http://127.0.0.1:8000/simulate/portscan", {
        method: "POST"
      })
      const data = await res.json()
      setMessage(data.message)
      loadStats()
      setTerminalHistory((prev) => [
        ...prev,
        "> system: simulación de escaneo de puertos ejecutada",
        data.message
      ])
      startScenario(data)
    } catch {
      setMessage("No se pudo ejecutar la simulación de escaneo de puertos")
      setTerminalHistory((prev) => [
        ...prev,
        "> system: error al ejecutar simulación de escaneo de puertos"
      ])
    }
  }

  const updateMissionAfterCommand = (normalizedCommand, output) => {
    if (!activeScenario) return

    if (normalizedCommand === "show alerts") {
      setMissionChecklist((prev) => ({ ...prev, reviewedAlerts: true }))
      setMissionState("reviewing_alerts")
      setMissionText(
        `🧠 Análisis inicial completado\n\nYa revisaste las alertas del incidente.\n\nLo siguiente es revisar el detalle del comportamiento del atacante.\n\nQué debes hacer ahora:\nshow events`
      )
      return
    }

    if (normalizedCommand === "show events") {
      setMissionChecklist((prev) => ({ ...prev, reviewedEvents: true }))
      setMissionState("reviewing_events")

      const nextIp = activeScenario.ip
      const scenarioLabel =
        activeScenario.type === "Fuerza Bruta"
          ? "fuerza bruta"
          : "escaneo de puertos"

      setMissionText(
        `📊 Evidencia analizada\n\nConfirmaste que el incidente corresponde a ${scenarioLabel} desde la IP ${nextIp}.\n\nQué debes hacer ahora:\nblock ip ${nextIp}`
      )
      return
    }

    if (
      normalizedCommand.startsWith("block ip ") &&
      output.toLowerCase().includes("bloqueada correctamente")
    ) {
      setMissionChecklist((prev) => ({ ...prev, blockedIp: true }))
      setMissionState("resolved")
      setMissionText(
        `✅ Ataque contenido\n\nLa IP atacante fue bloqueada correctamente.\n\nEl caso práctico ya está resuelto.\n\nQué debes hacer ahora:\n- Usa 'show blocked' para verificar el bloqueo\n- Luego pulsa 'Generar informe de sesión'`
      )
    }
  }

  const runCommand = async (e) => {
    e.preventDefault()

    if (!command.trim()) return

    startSessionIfNeeded()

    const currentCommand = command.trim()
    const normalizedCommand = currentCommand.toLowerCase()
    setCommand("")

    try {
      const res = await fetch("http://127.0.0.1:8000/terminal", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ command: currentCommand })
      })

      const data = await res.json()

      if (data.output === "__CLEAR__") {
        setTerminalHistory([])
      } else {
        setTerminalHistory((prev) => [
          ...prev,
          `> ${currentCommand}`,
          data.output
        ])
      }

      const isValidCommand = validCommandPrefixes.some((prefix) =>
        normalizedCommand === prefix || normalizedCommand.startsWith(prefix)
      )

      if (
        isValidCommand &&
        data.output !== "__CLEAR__" &&
        !data.output.toLowerCase().includes("comando no reconocido")
      ) {
        setValidCommands((prev) => [...prev, currentCommand])
      }

      updateMissionAfterCommand(normalizedCommand, data.output)
      loadStats()
    } catch {
      setTerminalHistory((prev) => [
        ...prev,
        `> ${currentCommand}`,
        "Error al conectar con la terminal del backend"
      ])
    }
  }

  const generateReport = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/report")
      const data = await res.json()

      const currentReport = {
        username,
        durationSeconds: elapsed,
        totalEvents: data.total_events,
        totalAlerts: data.total_alerts,
        blockedIps: data.blocked_ips.map((ip) => ip.ip_address),
        successfulCommands: data.actions
          .filter((action) => action.result === "OK" && action.command !== "clear")
          .map((action) => action.command),
        achieved: [
          data.total_events > 0 ? "Se ejecutaron simulaciones correctamente" : null,
          data.total_alerts > 0 ? "Se detectaron alertas de seguridad" : null,
          data.blocked_ips.length > 0 ? "Se aplicaron bloqueos manuales de IP" : null,
          missionState === "resolved" ? "El caso guiado fue completado" : null
        ].filter(Boolean),
        missing: [
          data.total_events === 0 ? "No se ejecutaron ataques durante la sesión" : null,
          data.total_alerts === 0 ? "No se generaron alertas en la sesión" : null,
          data.blocked_ips.length === 0 ? "No se aplicaron bloqueos manuales de IP" : null,
          missionState !== "resolved" ? "El caso guiado no fue completado totalmente" : null
        ].filter(Boolean)
      }

      setReport(currentReport)
      setTerminalHistory((prev) => [
        ...prev,
        "> system: informe generado",
        "Informe de sesión disponible en pantalla."
      ])
    } catch {
      setTerminalHistory((prev) => [
        ...prev,
        "> system: error al generar informe"
      ])
    }
  }

  useEffect(() => {
    const savedUser = localStorage.getItem("username")
    if (!savedUser) {
      router.push("/")
      return
    }

    setUsername(savedUser)
    loadStats()

    const interval = setInterval(() => {
      loadStats()
    }, 2000)

    return () => clearInterval(interval)
  }, [router])

  useEffect(() => {
    if (!startTime) return

    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime])

  return (
    <main className="dashboard-page">
      <div className="dashboard-container">
        <header className="hero-panel">
          <div>
            <div className="hero-badge">CENTRO DE OPERACIONES CYBERLAB</div>
            <h1 className="hero-title">Dashboard de Ciberseguridad</h1>
            <p className="hero-subtitle">
              Operador activo: <strong>{username}</strong>
            </p>
            <div className="timer-box">
              Tiempo de sesión: <strong>{elapsed}s</strong>
            </div>
          </div>

          <button
            onClick={() => {
              localStorage.removeItem("username")
              router.push("/")
            }}
            className="logout-button"
          >
            Cerrar sesión
          </button>
        </header>

        <section className="learning-panel">
          <h2>Modo entrenamiento</h2>
          <p>
            Esta plataforma funciona como un laboratorio controlado para aprender
            ciberseguridad ofensiva y defensiva. Aquí puedes simular ataques,
            observar eventos, revisar alertas y responder manualmente desde la
            terminal interactiva.
          </p>

          <div className="learning-grid">
            <div className="learning-box">
              <strong>Objetivo del ejercicio</strong>
              <ul>
                <li>Ejecutar una simulación de ataque</li>
                <li>Analizar eventos y alertas</li>
                <li>Identificar la IP atacante</li>
                <li>Aplicar defensa manual desde la terminal</li>
                <li>Generar un informe final de la sesión</li>
              </ul>
            </div>

            <div className="learning-box">
              <strong>Comandos útiles</strong>
              <ul>
                <li>help</li>
                <li>status</li>
                <li>show events</li>
                <li>show alerts</li>
                <li>show blocked</li>
                <li>block ip 192.168.1.50</li>
                <li>unblock ip 192.168.1.50</li>
                <li>clear</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="action-panel">
          <div>
            <h2>Simulación de ataque</h2>
            <p>
              Ejecuta un escenario de entrenamiento y observa el comportamiento
              del sistema en tiempo real.
            </p>
          </div>

          <div className="status-box">
            <span className="status-label">Estado</span>
            <span className="status-value">
              {message || "Esperando acción del operador..."}
            </span>
          </div>

          <div className="attack-buttons">
            <button className="attack-button" onClick={simulateAttack}>
              Ejecutar simulación de fuerza bruta
            </button>

            <button className="attack-button secondary" onClick={simulatePortScan}>
              Ejecutar escaneo de puertos
            </button>

            <button className="report-button" onClick={generateReport}>
              Generar informe de sesión
            </button>
          </div>
        </section>

        <section className="mission-panel">
          <div className="panel-header">
            <h2>Escenario activo</h2>
            <span className="tag cyan-tag">
              {missionState === "resolved" ? "RESUELTO" : "GUIDED MODE"}
            </span>
          </div>

          <pre className="mission-text">{missionText}</pre>

          <div className="mission-progress">
            <div className={`mission-step ${missionChecklist.reviewedAlerts ? "done" : ""}`}>
              Revisar alertas
            </div>
            <div className={`mission-step ${missionChecklist.reviewedEvents ? "done" : ""}`}>
              Revisar eventos
            </div>
            <div className={`mission-step ${missionChecklist.blockedIp ? "done" : ""}`}>
              Bloquear atacante
            </div>
          </div>
        </section>

        <section className="terminal-panel">
          <div className="panel-header">
            <h2>Terminal interactiva</h2>
            <span className="tag cyan-tag">CMD MODE</span>
          </div>

          <div className="terminal-window">
            {terminalHistory.map((line, index) => (
              <div key={index} className="terminal-line">
                {line}
              </div>
            ))}
          </div>

          <form onSubmit={runCommand} className="terminal-form">
            <span className="terminal-prefix">cyberlab@console:~$</span>
            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Escribe un comando..."
              className="terminal-input"
            />
          </form>
        </section>

        {report && (
          <section className="report-panel">
            <div className="panel-header">
              <h2>Informe de sesión</h2>
              <span className="tag danger-tag">REPORT</span>
            </div>

            <div className="report-grid">
              <div className="report-box">
                <span className="report-label">Operador</span>
                <span className="report-value">{report.username}</span>
              </div>

              <div className="report-box">
                <span className="report-label">Tiempo total</span>
                <span className="report-value">{report.durationSeconds}s</span>
              </div>

              <div className="report-box">
                <span className="report-label">Eventos</span>
                <span className="report-value">{report.totalEvents}</span>
              </div>

              <div className="report-box">
                <span className="report-label">Alertas</span>
                <span className="report-value">{report.totalAlerts}</span>
              </div>
            </div>

            <div className="report-sections">
              <div className="report-box large">
                <h3>Comandos válidos utilizados</h3>
                {report.successfulCommands.length === 0 ? (
                  <p>No hay comandos registrados todavía.</p>
                ) : (
                  <ul>
                    {report.successfulCommands.map((cmd, index) => (
                      <li key={`${cmd}-${index}`}>{cmd}</li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="report-box large">
                <h3>IPs bloqueadas</h3>
                {report.blockedIps.length === 0 ? (
                  <p>No se bloquearon IPs en esta sesión.</p>
                ) : (
                  <ul>
                    {report.blockedIps.map((ip) => (
                      <li key={ip}>{ip}</li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="report-box large">
                <h3>Logros</h3>
                {report.achieved.length === 0 ? (
                  <p>No hay logros registrados.</p>
                ) : (
                  <ul>
                    {report.achieved.map((item, index) => (
                      <li key={`achieved-${index}`}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="report-box large">
                <h3>Faltó por hacer</h3>
                {report.missing.length === 0 ? (
                  <p>La sesión completó correctamente los objetivos básicos.</p>
                ) : (
                  <ul>
                    {report.missing.map((item, index) => (
                      <li key={`missing-${index}`}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </section>
        )}

        <section className="data-grid">
          <div className="panel">
            <div className="panel-header">
              <h2>Eventos recientes</h2>
              <span className="tag cyan-tag">LIVE</span>
            </div>

            <div className="event-list">
              {stats.recent_events.length === 0 ? (
                <div className="empty-box">No hay eventos aún</div>
              ) : (
                stats.recent_events.map((event) => (
                  <div className="event-card" key={event.id}>
                    <div className="event-top">
                      <h3>{event.event_type}</h3>
                      <span className="event-id">#{event.id}</span>
                    </div>
                    <p>{event.description}</p>
                    <div className="event-meta">IP: {event.source_ip}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <h2>Alertas recientes</h2>
              <span className="tag danger-tag">WARNING</span>
            </div>

            <div className="alert-list">
              {stats.recent_alerts.length === 0 ? (
                <div className="empty-box">No hay alertas aún</div>
              ) : (
                stats.recent_alerts.map((alert) => (
                  <div className="alert-card" key={alert.id}>
                    <div className="alert-top">
                      <h3>{alert.title}</h3>
                      <span className="alert-severity">{alert.severity}</span>
                    </div>
                    <p>{alert.description}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}