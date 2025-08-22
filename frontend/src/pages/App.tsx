import { Box, Button, Container, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export default function App() {
  return (
    <Container maxWidth="full" sx={{ py: 6 }}>
      <Stack spacing={3} alignItems="center">
        <Typography variant="h4" fontWeight={700}>
          Recruitment AI Agent
        </Typography>
        <Typography color="text.secondary">
          Parse JDs, upload resumes, and score candidates.
        </Typography>
        <Box>
          <Button
            component={RouterLink}
            to="/jd"
            variant="contained"
            sx={{ mr: 2 }}
          >
            Job Description
          </Button>
          <Button component={RouterLink} to="/resumes" variant="outlined">
            Resumes
          </Button>
        </Box>
      </Stack>
    </Container>
  );
}
