import { useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Container,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { parseResumes, ResumeScoringResult } from "../lib/api";
import { useJD } from "../store/JDContext";

export default function ResumesPage() {
  const { parsedJD } = useJD();
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<ResumeScoringResult[]>([]);
  const [loading, setLoading] = useState(false);

  const parsedJDString = useMemo(
    () => JSON.stringify(parsedJD || {}),
    [parsedJD]
  );

  async function handleSubmit() {
    if (!parsedJD) return;
    if (!files.length) return;
    setLoading(true);
    try {
      const res = await parseResumes(parsedJDString, files);
      setResults(res);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h5" mb={2}>
        Resumes
      </Typography>

      {!parsedJD ? (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography color="warning.main">
            Please parse and save a Job Description first on the JD page.
          </Typography>
        </Paper>
      ) : (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle1" mb={1}>
            JD: {parsedJD.job_title || parsedJD.summary || "Untitled"}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Required skills:{" "}
            {(parsedJD.required_skills || []).join(", ") || "—"}
          </Typography>
          <Stack spacing={2} mt={2}>
            <input
              multiple
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
            />
            <Button
              variant="contained"
              disabled={loading || !files.length}
              onClick={handleSubmit}
            >
              {loading ? "Analyzing..." : "Analyze"}
            </Button>
          </Stack>
        </Paper>
      )}

      <Grid container spacing={2}>
        {results.map((r, idx) => (
          <Grid key={idx} item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6">
                {r.candidate?.name || "Unknown Candidate"}
              </Typography>
              <Typography color="text.secondary" variant="body2">
                {r.candidate?.email || "No email"}
              </Typography>
              <Typography mt={1} variant="body1">
                Score: <b>{r.scoring_result?.overall_score ?? "-"}</b> (
                {r.scoring_result?.hiring_decision ?? "-"})
              </Typography>
              <Stack direction="row" spacing={1} mt={1} flexWrap="wrap">
                {(r.scoring_result?.keyword_matches ?? [])
                  .slice(0, 6)
                  .map((s) => (
                    <Chip key={s} color="success" size="small" label={s} />
                  ))}
                {(r.scoring_result?.missing_keywords ?? [])
                  .slice(0, 6)
                  .map((s) => (
                    <Chip key={s} color="warning" size="small" label={s} />
                  ))}
              </Stack>
              {r.scoring_result?.areas_of_concern?.length ? (
                <Box mt={1}>
                  <Typography variant="subtitle2">Remarks</Typography>
                  <ul style={{ marginTop: 4 }}>
                    {r.scoring_result.areas_of_concern.slice(0, 4).map((x, i) => (
                      <li key={i}>
                        <Typography variant="body2">{x}</Typography>
                      </li>
                    ))}
                  </ul>
                </Box>
              ) : null}
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Container>
  );
}
