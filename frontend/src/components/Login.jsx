import React from "react";
import { Database } from "lucide-react";

export default function Login({ setToken, message, setMessage }) {
  const [username, setUsername] = React.useState("analyst");
  const [password, setPassword] = React.useState("password123");
  const [busy, setBusy] = React.useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");

    // Simulate a tiny delay for realism
    setTimeout(() => {
      if (username === "analyst" && password === "password123") {
        const dummyToken = "demo-session-token";
        localStorage.setItem("token", dummyToken);
        setToken(dummyToken);
      } else {
        setMessage("Invalid username or password.");
        setBusy(false);
      }
    }, 400);
  }

  return (
    <main className="loginPage">
      <form className="loginBox" onSubmit={submit}>
        <Database size={28} />
        <h1>Breathe ESG Review</h1>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>
        {message && <p className="formError">{message}</p>}
      </form>
    </main>
  );
}
