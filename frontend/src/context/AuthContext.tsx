import React, { createContext, useContext, useState, useEffect } from "react";
import { StudentProfile } from "../types";
import { api } from "../api/client";

interface AuthContextType {
  token: string | null;
  profile: StudentProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (email: string, pass: string, name: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("mentor_token"));
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshProfile = async () => {
    if (!localStorage.getItem("mentor_token")) {
      setProfile(null);
      setIsLoading(false);
      return;
    }
    try {
      const data = await api.getProfile();
      setProfile(data);
    } catch {
      // Token might be expired
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, [token]);

  const login = async (email: string, pass: string) => {
    const res = await api.login({ email, password: pass });
    localStorage.setItem("mentor_token", res.access_token);
    setToken(res.access_token);
    await refreshProfile();
  };

  const register = async (email: string, pass: string, name: string) => {
    const res = await api.register({ email, password: pass, full_name: name });
    localStorage.setItem("mentor_token", res.access_token);
    setToken(res.access_token);
    await refreshProfile();
  };

  const logout = () => {
    localStorage.removeItem("mentor_token");
    setToken(null);
    setProfile(null);
    setIsLoading(false);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        profile,
        isAuthenticated: !!token && !!profile,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
