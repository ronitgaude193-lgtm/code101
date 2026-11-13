import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { X, AlertCircle } from "lucide-react";
import { Mascot } from "./Mascot";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [fullName, setFullName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isRegister) {
        if (!fullName.trim()) {
          throw new Error("Please enter your full name.");
        }
        await register(email, password, fullName);
      } else {
        await login(email, password);
      }
      onClose();
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card auth-card">
        <button className="modal-close-btn" onClick={onClose}>
          <X size={18} />
        </button>

        <div className="modal-header auth-header">
          <div className="modal-icon">
            <Mascot size={44} />
          </div>
          <div>
            <h4>{isRegister ? "Create your account" : "Welcome back"}</h4>
            <p>Your XP, streak and course progress are saved to your account.</p>
          </div>
        </div>

        {error && (
          <div className="auth-error-banner">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {isRegister && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                placeholder="Alex Mercer"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Student Email Address</label>
            <input
              type="email"
              placeholder="student@dbce.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary-action auth-submit" disabled={isLoading}>
            {isLoading ? "Authenticating..." : isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>

        <div className="auth-switch-footer">
          {isRegister ? (
            <p>
              Already have an account?{" "}
              <button type="button" onClick={() => setIsRegister(false)}>
                Sign In
              </button>
            </p>
          ) : (
            <p>
              New to AI Coding Mentor?{" "}
              <button type="button" onClick={() => setIsRegister(true)}>
                Create Account
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
