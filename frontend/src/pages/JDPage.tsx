import { useState } from "react";
import {
  Box,
  Button,
  Container,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { uploadJDFile, submitManualJD, generateJD, parseJD } from "../lib/api";
import { useJD } from "../store/JDContext";

export default function JDPage() {
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

  async function handleUpload() {
    if (!file) return;
    const res = await uploadJDFile(file);
    setJdText(res.text);
  }

  async function handleManual() {
    if (!jdText.trim()) return;
    const res = await submitManualJD(jdText);
    setJdText(res.text);
  }

  async function handleGenerate() {
    const res = await generateJD(gen);
    setJdText(res.job_description);
    setTab(0);
  }

  async function handleParse() {
    if (!jdText.trim()) return;
    const parsed = await parseJD(jdText);
    setParsedJD(parsed);
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h5" mb={2}>
        Job Description
      </Typography>
      <Paper sx={{ p: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label="Upload" />
          <Tab label="Manual" />
          <Tab label="Generate" />
        </Tabs>

        {tab === 0 && (
          <Stack spacing={2}>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <Button variant="contained" onClick={handleUpload}>
              Extract
            </Button>
          </Stack>
        )}

        {tab === 1 && (
          <Stack spacing={2}>
            <TextField
              label="Paste JD"
              multiline
              minRows={8}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
            <Button variant="contained" onClick={handleManual}>
              Save
            </Button>
          </Stack>
        )}

        {tab === 2 && (
          <Stack spacing={2}>
            <TextField
              label="Job Title"
              value={gen.job_title}
              onChange={(e) => setGen({ ...gen, job_title: e.target.value })}
            />
            <TextField
              type="number"
              label="Years of Experience"
              value={gen.years_of_experience}
              onChange={(e) =>
                setGen({ ...gen, years_of_experience: Number(e.target.value) })
              }
            />
            <TextField
              label="Must-have Skills (comma)"
              value={gen.must_have_skills}
              onChange={(e) =>
                setGen({ ...gen, must_have_skills: e.target.value })
              }
            />
            <TextField
              label="Company Name"
              value={gen.company_name}
              onChange={(e) => setGen({ ...gen, company_name: e.target.value })}
            />
            <TextField
              label="Employment Type"
              value={gen.employment_type}
              onChange={(e) =>
                setGen({ ...gen, employment_type: e.target.value })
              }
            />
            <TextField
              label="Industry"
              value={gen.industry}
              onChange={(e) => setGen({ ...gen, industry: e.target.value })}
            />
            <TextField
              label="Location"
              value={gen.location}
              onChange={(e) => setGen({ ...gen, location: e.target.value })}
            />
            <Button variant="contained" onClick={handleGenerate}>
              Generate
            </Button>
          </Stack>
        )}
      </Paper>

      <Stack direction="row" spacing={2} mt={2}>
        <Button
          variant="contained"
          onClick={handleParse}
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

      <Typography variant="h6" mt={3} mb={1}>
        Preview
      </Typography>
      <Paper sx={{ p: 2, whiteSpace: "pre-wrap" }}>
        {jdText || "No JD yet"}
      </Paper>
    </Container>
  );
}
