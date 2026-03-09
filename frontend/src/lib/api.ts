import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth ────────────────────────────────────────────
export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const { data } = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data as { access_token: string; token_type: string };
}

export async function register(body: {
  name: string;
  email: string;
  password: string;
}) {
  const { data } = await api.post("/auth/register", body);
  return data;
}

export async function getMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

// ── Master Resumes ──────────────────────────────────
export async function getMasterResumes() {
  const { data } = await api.get("/resumes/master");
  return data;
}

export async function createMasterResume(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/resumes/master", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getMasterResume(id: string) {
  const { data } = await api.get(`/resumes/master/${id}`);
  return data;
}

// ── Jobs ────────────────────────────────────────────
export async function getJobs() {
  const { data } = await api.get("/jobs");
  return data;
}

export async function createJob(body: {
  title?: string;
  company?: string;
  description?: string;
  url?: string;
  file?: File;
}) {
  if (body.file) {
    const form = new FormData();
    form.append("file", body.file);
    if (body.title) form.append("title", body.title);
    if (body.company) form.append("company", body.company);
    const { data } = await api.post("/jobs", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  }
  const { data } = await api.post("/jobs", body);
  return data;
}

export async function getJob(id: string) {
  const { data } = await api.get(`/jobs/${id}`);
  return data;
}

// ── Tailored Resumes ────────────────────────────────
export async function tailorResume(body: {
  master_resume_id: string;
  job_id: string;
}) {
  const { data } = await api.post("/resumes/tailor", body);
  return data;
}

export async function getTailoredResumes() {
  const { data } = await api.get("/resumes/tailored");
  return data;
}

export async function getTailoredResume(id: string) {
  const { data } = await api.get(`/resumes/tailored/${id}`);
  return data;
}

export async function downloadPdf(id: string) {
  const { data } = await api.get(`/resumes/tailored/${id}/pdf`, {
    responseType: "blob",
  });
  return data;
}

export default api;
