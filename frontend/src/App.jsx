import { useEffect, useState } from "react";
import { getSession, onAuthChange, isSupabaseConfigured } from "./api.js";
import Login from "./components/Login.jsx";
import ApplicationQueue from "./components/ApplicationQueue.jsx";

export default function App() {
  const [session, setSession] = useState(undefined); // undefined = still checking

  useEffect(() => {
    getSession().then(setSession);
    const sub = onAuthChange(setSession);
    return () => sub.unsubscribe();
  }, []);

  if (session === undefined) return <div className="muted center">Loading…</div>;
  if (!session && isSupabaseConfigured) return <Login onLoggedIn={() => getSession().then(setSession)} />;
  return <ApplicationQueue />;
}
