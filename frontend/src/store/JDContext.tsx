import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { JobDescriptionParsed } from "../lib/api";

interface JDState {
  jdText: string;
  setJdText: (t: string) => void;
  parsedJD: JobDescriptionParsed | null;
  setParsedJD: (p: JobDescriptionParsed | null) => void;
}

const Ctx = createContext<JDState | undefined>(undefined);

export function JDProvider({ children }: { children: React.ReactNode }) {
  const [jdText, setJdText] = useState<string>(
    () => localStorage.getItem("jdText") || ""
  );
  const [parsedJD, setParsedJD] = useState<JobDescriptionParsed | null>(() => {
    const raw = localStorage.getItem("parsedJD");
    return raw ? JSON.parse(raw) : null;
  });

  useEffect(() => {
    localStorage.setItem("jdText", jdText);
  }, [jdText]);
  useEffect(() => {
    parsedJD
      ? localStorage.setItem("parsedJD", JSON.stringify(parsedJD))
      : localStorage.removeItem("parsedJD");
  }, [parsedJD]);

  const value = useMemo(
    () => ({ jdText, setJdText, parsedJD, setParsedJD }),
    [jdText, parsedJD]
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useJD() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useJD must be used within JDProvider");
  return v;
}
 