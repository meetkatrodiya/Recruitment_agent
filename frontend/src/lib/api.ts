import axios from "axios";

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_BASE });

export type ApiResponse<T> = {
  success: boolean;
  message?: string;
  data?: T;
};

function unwrapOrThrow<T>(resp: ApiResponse<T>): T {
  if (!resp?.success) {
    throw new Error(resp?.message || "Request failed");
  }
  if (resp.data === undefined) {
    throw new Error("Empty response");
  }
  return resp.data as T;
}

export async function uploadJDFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/jd/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  const resp = data as ApiResponse<{
    source: string;
    filename: string;
    text: string;
    length: number;
  }>;
  return unwrapOrThrow(resp);
}

export async function submitManualJD(text: string) {
  const { data } = await api.post("/jd/manual", { text });
  const resp = data as ApiResponse<{
    source: string;
    text: string;
    length: number;
  }>;
  return unwrapOrThrow(resp);
}

export async function generateJD(payload: {
  job_title: string;
  years_of_experience: number;
  must_have_skills: string;
  company_name: string;
  employment_type: string;
  industry: string;
  location: string;
  language?: string;
}) {
  const { data } = await api.post("/jd/generate", payload);
  const resp = data as ApiResponse<{
    job_description: string;
    length: number;
    inputs: any;
  }>;
  return unwrapOrThrow(resp);
}

export type Candidate = {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
  github?: string | null;
  location?: string | null;
};

export type Scoring = {
  overall_score: number;
  basic_eligibility_score: number;
  skills_match_score: number;
  experience_contextualization_score: number;
  formatting_completeness_score: number;
  recommendation: string;
  key_strengths: string[];
  areas_of_concern: string[];
  category_breakdown: Record<string, any>;
  role_specific_experience: number;
  average_tenure_per_company: number;
  highest_education_level: string;
  hiring_decision: string;
  keyword_matches: string[];
  missing_keywords: string[];
  alternative_keywords: string[];
  risk_factors: string[];
  next_steps: string[];
};

export type ResumeScoringResult = {
  candidate: Candidate;
  scoring_result: Scoring;
};

export type JobDescriptionParsed = {
  job_title?: string | null;
  years_of_experience?: number | null;
  required_skills: string[];
  nice_to_have_skills?: string[];
  company_name?: string | null;
  employment_type?: string | null;
  industry?: string | null;
  location?: string | null;
  summary?: string | null;
};

export async function parseJD(text: string) {
  const { data } = await api.post("/jd/parse", { text });
  const resp = data as ApiResponse<JobDescriptionParsed>;
  return unwrapOrThrow(resp);
}

export async function parseResumes(parsed_jd_json: string, files: File[]) {
  const form = new FormData();
  form.append("parsed_jd_json", parsed_jd_json);
  files.forEach((f) => form.append("files", f));
  const { data } = await api.post("/resumes/parse", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  const resp = data as ApiResponse<ResumeScoringResult[]>;
  return unwrapOrThrow(resp);
}

export async function generateEmail(payload: {
  type: "interview" | "rejection";
  candidate: { name?: string | null; email: string };
  job_title?: string | null;
  company_name?: string | null;
  jd_summary?: string | null;
  score?: number | null;
  remarks?: string | null;
  language?: string;
}) {
  const { data } = await api.post("/email/generate", payload);
  const resp = data as ApiResponse<{ subject: string; body_text: string }>;
  return unwrapOrThrow(resp);
}

export async function sendEmail(payload: {
  to_email: string;
  subject: string;
  body_text: string;
  from_name?: string;
}) {
  const { data } = await api.post("/email/send", payload);
  const resp = data as ApiResponse<{ status: string }>;
  return unwrapOrThrow(resp);
}
