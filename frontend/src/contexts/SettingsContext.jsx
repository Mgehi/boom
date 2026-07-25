import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "@/lib/api";

const SettingsContext = createContext(null);

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      const res = await api.get("/settings");
      setSettings(res.data);
      return res.data;
    } catch (error) {
      setSettings(null);
      return null;
    }
  }, []);

  useEffect(() => {
    refetch().finally(() => setLoading(false));
  }, [refetch]);

  return (
    <SettingsContext.Provider value={{ settings, loading, refetch, setSettings }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within a SettingsProvider");
  return ctx;
};
