import { useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import DescriptionIcon from "@mui/icons-material/Description";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import ForwardToInboxIcon from "@mui/icons-material/ForwardToInbox";
import ThumbUpAltOutlinedIcon from "@mui/icons-material/ThumbUpAltOutlined";
import BlockOutlinedIcon from "@mui/icons-material/BlockOutlined";
import StarIcon from "@mui/icons-material/Star";
import VisibilityIcon from "@mui/icons-material/Visibility";
import {
  uploadJDFile,
  submitManualJD,
  generateJD,
  parseJD,
  parseResumes,
  generateEmail,
  sendEmail,
} from "../lib/api";
import { useJD } from "../store/JDContext";

const monoPaperStyle = {
  p: 2,
  whiteSpace: "pre-wrap" as const,
  maxHeight: "70vh",
  overflow: "auto" as const,
  fontFamily:
    'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
};

function isLikelyEmail(value: string | undefined | null): value is string {
  if (!value) return false;
  return /.+@.+\..+/.test(value);
}

export default function Workflow() {
  const { jdText, setJdText, parsedJD, setParsedJD } = useJD();
  const [tab, setTab] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [gen, setGen] = useState({
    job_title: "",
    years_of_experience: 0,
    must_have_skills: "",
    company_name: "",
    employment_type: "",
    industry: "",
    location: "",
    language: "English",
  });
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const [emailOpen, setEmailOpen] = useState(false);
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [emailTo, setEmailTo] = useState("");
  const [jdPreviewOpen, setJdPreviewOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState<any | null>(null);

  const bestIndex = useMemo(() => {
    if (!results.length) return -1;
    let best = -1;
    let idx = -1;
    results.forEach((r: any, i: number) => {
      const s = r?.scoring_result?.overall_score ?? -1;
      if (s > best) {
        best = s;
        idx = i;
      }
    });
    return idx;
  }, [results]);

  async function handleUploadJD() {
    try {
      if (!file) return;
      const res = await uploadJDFile(file);
      setJdText(res.text);
    } catch (e: any) {
      alert(e?.message || "Failed to upload JD file");
    }
  }
  async function handleManualJD() {
    try {
      if (!jdText.trim()) return;
      const res = await submitManualJD(jdText);
      setJdText(res.text);
    } catch (e: any) {
      alert(e?.message || "Failed to save manual JD");
    }
  }
  async function handleGenerateJD() {
    try {
      const res = await generateJD(gen);
      setJdText(res.job_description);
      setTab(0);
    } catch (e: any) {
      alert(e?.message || "Failed to generate JD");
    }
  }
  async function handleParseJD() {
    try {
      if (!jdText.trim()) return;
      const parsed = await parseJD(jdText);
      setParsedJD(parsed);
    } catch (e: any) {
      alert(e?.message || "Failed to parse JD");
    }
  }
  async function handleAnalyzeResumes() {
    if (!parsedJD || !resumeFiles.length) return;
    setLoading(true);
    try {
      const parsedJDString = JSON.stringify(parsedJD);
      const res = await parseResumes(parsedJDString, resumeFiles);
      setResults(res);
    } catch (e: any) {
      alert(e?.message || "Failed to analyze resumes");
    } finally {
      setLoading(false);
    }
  }

  async function openEmailDialog(
    type: "interview" | "rejection",
    idx: number,
    e?: React.MouseEvent
  ) {
    e?.stopPropagation();
    try {
      const r = results[idx];
      if (!r || !parsedJD) return;
      const email = r.candidate?.email?.trim();
      if (!isLikelyEmail(email)) {
        alert("Candidate email is missing or invalid. Cannot generate email.");
        return;
      }
      const overall = r.scoring_result?.overall_score;
      const scoreInt = Number.isFinite(overall)
        ? Math.round(Number(overall))
        : undefined;
      const genRes = await generateEmail({
        type,
        candidate: { name: r.candidate?.name, email },
        job_title: parsedJD.job_title,
        company_name: parsedJD.company_name,
        jd_summary: parsedJD.summary,
        score: scoreInt ?? undefined,
        remarks: (r.scoring_result?.key_strengths || []).slice(0, 3).join("; "),
        language: "English",
      });
      setEmailSubject(genRes.subject);
      setEmailBody(genRes.body_text);
      setEmailTo(email);
      setEmailOpen(true);
    } catch (e: any) {
      alert(e?.message || "Failed to generate email");
    }
  }

  async function handleSendEmail() {
    try {
      if (!emailTo || !emailSubject || !emailBody) return;
      await sendEmail({
        to_email: emailTo,
        subject: emailSubject,
        body_text: emailBody,
      });
      setEmailOpen(false);
    } catch (e: any) {
      alert(e?.message || "Failed to send email");
    }
  }

  const columnHeight = "calc(100vh - 120px)";

  return (
    <Container maxWidth={false} sx={{ py: 2, px: 2 }}>
      <Typography variant="h4" fontWeight={800} mb={2}>
        Recruitment AI Agent
      </Typography>

      <Grid container spacing={2} alignItems="stretch">
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: columnHeight }}>
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <DescriptionIcon color="primary" />
              <Typography variant="h6">1) Job Description</Typography>
            </Stack>
            <Divider sx={{ mb: 2 }} />
            <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
              <Tab
                icon={<UploadFileIcon />}
                iconPosition="start"
                label="Upload"
              />
              <Tab
                icon={<DescriptionIcon />}
                iconPosition="start"
                label="Manual"
              />
              <Tab
                icon={<AutoAwesomeIcon />}
                iconPosition="start"
                label="Generate"
              />
            </Tabs>

            {tab === 0 && (
              <Stack spacing={2}>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
                <Button
                  variant="contained"
                  startIcon={<UploadFileIcon />}
                  onClick={handleUploadJD}
                >
                  Extract
                </Button>
              </Stack>
            )}

            {tab === 1 && (
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  variant="outlined"
                  label="Paste JD"
                  placeholder="Paste or type the job description here..."
                  multiline
                  minRows={8}
                  maxRows={18}
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  sx={{
                    "& .MuiInputBase-root": { width: "100%" },
                    "& textarea": { overflow: "auto" },
                  }}
                />
                <Button variant="contained" onClick={handleManualJD}>
                  Save
                </Button>
              </Stack>
            )}

            {tab === 2 && (
              <Stack spacing={2}>
                <TextField
                  label="Job Title"
                  value={gen.job_title}
                  onChange={(e) =>
                    setGen({ ...gen, job_title: e.target.value })
                  }
                  fullWidth
                />
                <TextField
                  type="number"
                  label="Years of Experience"
                  value={gen.years_of_experience}
                  onChange={(e) =>
                    setGen({
                      ...gen,
                      years_of_experience: Number(e.target.value),
                    })
                  }
                  fullWidth
                />
                <TextField
                  label="Must-have Skills (comma)"
                  value={gen.must_have_skills}
                  onChange={(e) =>
                    setGen({ ...gen, must_have_skills: e.target.value })
                  }
                  fullWidth
                />
                <TextField
                  label="Company Name"
                  value={gen.company_name}
                  onChange={(e) =>
                    setGen({ ...gen, company_name: e.target.value })
                  }
                  fullWidth
                />
                <TextField
                  label="Employment Type"
                  value={gen.employment_type}
                  onChange={(e) =>
                    setGen({ ...gen, employment_type: e.target.value })
                  }
                  fullWidth
                />
                <TextField
                  label="Industry"
                  value={gen.industry}
                  onChange={(e) => setGen({ ...gen, industry: e.target.value })}
                  fullWidth
                />
                <TextField
                  label="Location"
                  value={gen.location}
                  onChange={(e) => setGen({ ...gen, location: e.target.value })}
                  fullWidth
                />
                <Button
                  variant="contained"
                  startIcon={<AutoAwesomeIcon />}
                  onClick={handleGenerateJD}
                >
                  Generate
                </Button>
              </Stack>
            )}

            <Stack direction="row" spacing={2} mt={2} alignItems="center">
              <Button
                variant="contained"
                onClick={handleParseJD}
                disabled={!jdText.trim()}
              >
                Parse & Save JD
              </Button>
              <Typography color={parsedJD ? "success.main" : "text.secondary"}>
                {parsedJD
                  ? `JD parsed: ${parsedJD.job_title || "Untitled"} (${
                      parsedJD.required_skills?.length || 0
                    } skills)`
                  : "No parsed JD saved"}
              </Typography>
            </Stack>

            <Stack direction="row" spacing={1} mt={2}>
              <Button
                variant="outlined"
                startIcon={<VisibilityIcon />}
                onClick={() => setJdPreviewOpen(true)}
                disabled={!jdText.trim()}
              >
                Open JD Preview
              </Button>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: columnHeight }}>
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <UploadFileIcon color="primary" />
              <Typography variant="h6">2) Upload Resumes & Analyze</Typography>
            </Stack>
            <Divider sx={{ mb: 2 }} />
            {!parsedJD ? (
              <Typography color="warning.main">
                Please parse & save JD first.
              </Typography>
            ) : (
              <>
                <Typography variant="body2" color="text.secondary" mb={1}>
                  Using JD:{" "}
                  {parsedJD.job_title || parsedJD.summary || "Untitled"}
                </Typography>
                <Stack spacing={2}>
                  <input
                    multiple
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) =>
                      setResumeFiles(Array.from(e.target.files || []))
                    }
                  />
                  <Button
                    variant="contained"
                    onClick={handleAnalyzeResumes}
                    disabled={loading || !resumeFiles.length}
                  >
                    Analyze
                  </Button>
                  {loading && <LinearProgress />}
                </Stack>
              </>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: columnHeight }}>
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <StarIcon color="primary" />
              <Typography variant="h6">3) Results</Typography>
            </Stack>
            <Divider sx={{ mb: 2 }} />
            <Box
              sx={{ height: `calc(${columnHeight} - 80px)`, overflow: "auto" }}
            >
              <Grid container spacing={2}>
                {results.map((r, idx) => {
                  const isBest = idx === bestIndex;
                  return (
                    <Grid key={idx} item xs={12}>
                      <Paper
                        onClick={() => {
                          setDetail(r);
                          setDetailOpen(true);
                        }}
                        sx={{
                          position: "relative",
                          p: 2,
                          border: isBest ? "2px solid" : "1px solid",
                          borderColor: isBest ? "success.main" : "divider",
                          boxShadow: isBest ? 6 : undefined,
                          backgroundColor: isBest
                            ? "rgba(46, 125, 50, 0.06)"
                            : undefined,
                          transition: "box-shadow 0.2s, transform 0.2s",
                          cursor: "pointer",
                        }}
                      >
                        {isBest && (
                          <Chip
                            label="Best Match"
                            color="success"
                            size="small"
                            sx={{ position: "absolute", top: 8, right: 8 }}
                          />
                        )}
                        <Typography variant="h6">
                          {r.candidate?.name || "Unknown Candidate"}
                        </Typography>
                        <Typography color="text.secondary" variant="body2">
                          {r.candidate?.email || "No email"}
                        </Typography>
                        <Typography mt={1} variant="body1">
                          Score: <b>{r.scoring_result?.overall_score ?? "-"}</b>{" "}
                          ({r.scoring_result?.hiring_decision ?? "-"})
                        </Typography>
                        <Stack
                          direction="row"
                          spacing={1}
                          mt={1}
                          flexWrap="wrap"
                        >
                          {(r.scoring_result?.keyword_matches ?? [])
                            .slice(0, 6)
                            .map((s: string) => (
                              <Chip
                                key={s}
                                color="success"
                                size="small"
                                label={s}
                              />
                            ))}
                          {(r.scoring_result?.missing_keywords ?? [])
                            .slice(0, 6)
                            .map((s: string) => (
                              <Chip
                                key={s}
                                color="warning"
                                size="small"
                                label={s}
                              />
                            ))}
                        </Stack>
                        <Stack direction="row" spacing={1} mt={2}>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<ThumbUpAltOutlinedIcon />}
                            onClick={(e) =>
                              openEmailDialog("interview", idx, e)
                            }
                          >
                            Interview Email
                          </Button>
                          <Button
                            size="small"
                            startIcon={<BlockOutlinedIcon />}
                            onClick={(e) =>
                              openEmailDialog("rejection", idx, e)
                            }
                          >
                            Rejection Email
                          </Button>
                          <Button
                            size="small"
                            variant="text"
                            startIcon={<ForwardToInboxIcon />}
                            onClick={(e) =>
                              openEmailDialog("interview", idx, e)
                            }
                          >
                            Send
                          </Button>
                        </Stack>
                      </Paper>
                    </Grid>
                  );
                })}
              </Grid>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Dialog
        fullWidth
        maxWidth="md"
        open={jdPreviewOpen}
        onClose={() => setJdPreviewOpen(false)}
      >
        <DialogTitle>Job Description Preview</DialogTitle>
        <DialogContent>
          <Paper variant="outlined" sx={monoPaperStyle}>
            {jdText || "No JD yet"}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setJdPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Dialog
        fullWidth
        maxWidth="md"
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      >
        <DialogTitle>Candidate Details</DialogTitle>
        <DialogContent>
          {detail ? (
            <Stack spacing={2} mt={1}>
              <Box>
                <Typography variant="subtitle2">Candidate</Typography>
                <Typography variant="body2">
                  Name: {detail.candidate?.name || "-"}
                </Typography>
                <Typography variant="body2">
                  Email: {detail.candidate?.email || "-"}
                </Typography>
                <Typography variant="body2">
                  Phone: {detail.candidate?.phone || "-"}
                </Typography>
                <Typography variant="body2">
                  LinkedIn: {detail.candidate?.linkedin || "-"}
                </Typography>
                <Typography variant="body2">
                  GitHub: {detail.candidate?.github || "-"}
                </Typography>
                <Typography variant="body2">
                  Location: {detail.candidate?.location || "-"}
                </Typography>
              </Box>
              <Divider />
              <Box>
                <Typography variant="subtitle2">Scores</Typography>
                <Typography variant="body2">
                  Overall Score: {detail.scoring_result?.overall_score ?? "-"}
                </Typography>
                <Typography variant="body2">
                  Basic Eligibility:{" "}
                  {detail.scoring_result?.basic_eligibility_score ?? "-"}
                </Typography>
                <Typography variant="body2">
                  Skills Match:{" "}
                  {detail.scoring_result?.skills_match_score ?? "-"}
                </Typography>
                <Typography variant="body2">
                  Experience Contextualization:{" "}
                  {detail.scoring_result?.experience_contextualization_score ??
                    "-"}
                </Typography>
                <Typography variant="body2">
                  Formatting & Completeness:{" "}
                  {detail.scoring_result?.formatting_completeness_score ?? "-"}
                </Typography>
                <Typography variant="body1" fontWeight={600}>
                  Decision: {detail.scoring_result?.hiring_decision ?? "-"}
                </Typography>
              </Box>
              <Divider />
              <Box>
                <Typography variant="subtitle2">Key Strengths</Typography>
                <ul style={{ marginTop: 4 }}>
                  {(detail.scoring_result?.key_strengths || []).map(
                    (x: string, i: number) => (
                      <li key={i}>
                        <Typography variant="body2">{x}</Typography>
                      </li>
                    )
                  )}
                </ul>
              </Box>
              <Box>
                <Typography variant="subtitle2">Areas of Concern</Typography>
                <ul style={{ marginTop: 4 }}>
                  {(detail.scoring_result?.areas_of_concern || []).map(
                    (x: string, i: number) => (
                      <li key={i}>
                        <Typography variant="body2">{x}</Typography>
                      </li>
                    )
                  )}
                </ul>
              </Box>
              <Box>
                <Typography variant="subtitle2">Keyword Matches</Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" mt={1}>
                  {(detail.scoring_result?.keyword_matches || []).map(
                    (s: string, i: number) => (
                      <Chip
                        key={`${s}-${i}`}
                        size="small"
                        color="success"
                        label={s}
                      />
                    )
                  )}
                </Stack>
              </Box>
              <Box>
                <Typography variant="subtitle2">Missing Keywords</Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" mt={1}>
                  {(detail.scoring_result?.missing_keywords || []).map(
                    (s: string, i: number) => (
                      <Chip
                        key={`${s}-${i}`}
                        size="small"
                        color="warning"
                        label={s}
                      />
                    )
                  )}
                </Stack>
              </Box>
              <Box>
                <Typography variant="subtitle2">Next Steps</Typography>
                <ul style={{ marginTop: 4 }}>
                  {(detail.scoring_result?.next_steps || []).map(
                    (x: string, i: number) => (
                      <li key={i}>
                        <Typography variant="body2">{x}</Typography>
                      </li>
                    )
                  )}
                </ul>
              </Box>
            </Stack>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Dialog
        fullWidth
        maxWidth="md"
        open={emailOpen}
        onClose={() => setEmailOpen(false)}
      >
        <DialogTitle>Review & Send Email</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="To"
              value={emailTo}
              onChange={(e) => setEmailTo(e.target.value)}
              fullWidth
            />
            <TextField
              label="Subject"
              value={emailSubject}
              onChange={(e) => setEmailSubject(e.target.value)}
              fullWidth
            />
            <TextField
              label="Body"
              value={emailBody}
              onChange={(e) => setEmailBody(e.target.value)}
              fullWidth
              multiline
              minRows={8}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEmailOpen(false)}>Close</Button>
          <Button variant="contained" onClick={handleSendEmail}>
            Send
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
