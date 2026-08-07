// Data layer: talks to Supabase in production, or to the local helper server
// (scripts/local_server.py) when no Supabase project is configured yet —
// see README for how to switch over once you've created one.
//
// Resume upload always goes through the local server regardless of mode:
// it needs GEMINI_API_KEY to structure the resume, and that key must never
// ship in the deployed frontend's JS bundle. Run `python -m scripts.local_server`
// on your machine whenever you want to upload or replace your resume.

import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;
const LOCAL_API_BASE = "https://localhost:8787";

export const isSupabaseConfigured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

export const supabase = isSupabaseConfigured
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

export async function login(email, password) {
  if (!isSupabaseConfigured) return { data: { session: "dev" }, error: null };
  return supabase.auth.signInWithPassword({ email, password });
}

export async function logout() {
  if (!isSupabaseConfigured) return;
  await supabase.auth.signOut();
}

export async function getSession() {
  if (!isSupabaseConfigured) return "dev"; // dev shim has no auth
  const { data } = await supabase.auth.getSession();
  return data.session;
}

export function onAuthChange(callback) {
  if (!isSupabaseConfigured) return { unsubscribe() {} };
  const { data } = supabase.auth.onAuthStateChange((_event, session) => callback(session));
  return data.subscription;
}

export async function listApplications(status) {
  if (!isSupabaseConfigured) {
    const url = new URL(`${LOCAL_API_BASE}/applications`);
    if (status) url.searchParams.set("status", status);
    const resp = await fetch(url);
    return resp.json();
  }
  let query = supabase
    .from("tailored_applications")
    .select("*, jobs(title, company, url, location, posted_at)")
    .order("ats_score", { ascending: false });
  if (status) query = query.eq("status", status);
  const { data, error } = await query;
  if (error) throw error;
  return data.map((row) => ({ ...row, ...row.jobs }));
}

export async function updateApplicationStatus(id, status) {
  if (!isSupabaseConfigured) {
    return fetch(`${LOCAL_API_BASE}/applications/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
  }
  const { error } = await supabase
    .from("tailored_applications")
    .update({ status })
    .eq("id", id);
  if (error) throw error;
}

export function resumePdfUrl(app) {
  if (!isSupabaseConfigured || !app.resume_pdf_path) return null;
  const { data } = supabase.storage.from("resumes").getPublicUrl(app.resume_pdf_path);
  return data.publicUrl;
}

export async function getResume() {
  if (!isSupabaseConfigured) {
    const resp = await fetch(`${LOCAL_API_BASE}/resume`);
    const data = await resp.json();
    return data?.id ? data : null;
  }
  const { data, error } = await supabase
    .from("resumes")
    .select("*")
    .order("uploaded_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw error;
  return data;
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",", 2)[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// Always via the local server, regardless of mode — see the note at the top of this file.
export async function uploadResume(file) {
  const content_base64 = await fileToBase64(file);
  let resp;
  try {
    resp = await fetch(`${LOCAL_API_BASE}/resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, content_base64 }),
    });
  } catch {
    throw new Error(
      "Can't reach the local server. Run: python -m scripts.local_server"
    );
  }
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || "Upload failed");
  return data;
}
