"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function Home() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [message, setMessage] = useState("")

  const handleLogin = async (e) => {
    e.preventDefault()

    try {
      const res = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
      })

      const data = await res.json()

      if (!res.ok) {
        setMessage(data.detail || "Error al iniciar sesión")
        return
      }

      localStorage.setItem("username", data.username)
      router.push("/dashboard")
    } catch {
      setMessage("No se pudo conectar con el backend")
    }
  }

  return (
    <main className="login-page">
      <div className="bg-orb orb-1"></div>
      <div className="bg-orb orb-2"></div>

      <section className="login-card">
        <div className="login-badge">CYBERLAB TRAINER</div>
        <h1 className="login-title">Acceso al sistema</h1>
        <p className="login-subtitle">
          Plataforma de simulación de ciberataques
        </p>

        <form onSubmit={handleLogin} className="login-form">
          <input
            type="text"
            placeholder="Usuario"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="cyber-input"
          />

          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="cyber-input"
          />

          <button type="submit" className="cyber-button">
            Ingresar al laboratorio
          </button>
        </form>

        <div className="login-message">{message}</div>

        <div className="demo-box">
          <div className="demo-title">Credenciales demo</div>
          <div>Usuario: <strong>admin</strong></div>
          <div>Clave: <strong>admin123</strong></div>
        </div>
      </section>
    </main>
  )
}