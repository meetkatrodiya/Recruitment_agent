import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import App from "./pages/App";
import JDPage from "./pages/JDPage";
import ResumesPage from "./pages/ResumesPage";
import Workflow from "./pages/Workflow";
import { JDProvider } from "./store/JDContext";

const theme = createTheme({
  palette: { mode: "light" },
});

const router = createBrowserRouter([
  { path: "/", element: <Workflow /> },
  { path: "/jd", element: <JDPage /> },
  { path: "/resumes", element: <ResumesPage /> },
  { path: "/home", element: <App /> },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <JDProvider>
        <RouterProvider router={router} />
      </JDProvider>
    </ThemeProvider>
  </React.StrictMode>
);
 