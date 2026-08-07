import { useState } from "react";
import { login } from "../api.js";

export default function Login({ onLoggedIn }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const { error } = await login(email, password);
    setLoading(false);
    if (error) setError(error.message);
    else onLoggedIn();
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-mark">🎯</div>
        <h1>Job Search Agent</h1>
        <p className="muted">Sign in with the Supabase Auth user you created for yourself.</p>
        <label className="field">
          <span>Email</span>
          <input
            type="email" value={email}
            onChange={(e) => setEmail(e.target.value)} required autoFocus
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password" value={password}
            onChange={(e) => setPassword(e.target.value)} required
          />
        </label>
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</button>
      </form>
    </div>
  );
}
