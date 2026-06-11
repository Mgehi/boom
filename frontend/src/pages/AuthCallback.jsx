import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { AlertCircle, ArrowLeft } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processCallback = async () => {
      const hash = window.location.hash;
      const match = hash.match(/session_id=([^&]+)/);
      
      if (!match) {
        navigate("/login");
        return;
      }
      
      const sessionId = match[1];
      
      try {
        const response = await axios.post(
          `${API}/auth/session`,
          {},
          {
            headers: { "X-Session-ID": sessionId },
            withCredentials: true,
          }
        );
        
        window.history.replaceState(null, "", "/");
        navigate("/", { state: { user: response.data } });
      } catch (err) {
        console.error("Auth callback failed:", err);
        if (err.response?.status === 403) {
          setError(err.response.data.detail || "Access denied. Your email is not authorized.");
        } else {
          navigate("/login");
        }
      }
    };
    
    processCallback();
  }, [navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white p-6" data-testid="access-denied-page">
        <div className="max-w-md w-full text-center border border-zinc-200 rounded-sm bg-white p-8">
          <div className="w-14 h-14 bg-red-50 border border-red-200 rounded-sm flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7 text-red-600" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight mb-3" data-testid="access-denied-title">Access Denied</h1>
          <p className="text-sm text-zinc-600 mb-6" data-testid="access-denied-message">{error}</p>
          <button
            onClick={() => {
              window.history.replaceState(null, "", "/login");
              navigate("/login");
            }}
            data-testid="back-to-login-btn"
            className="inline-flex items-center gap-2 bg-zinc-900 text-white px-6 py-3 rounded-sm font-medium hover:bg-zinc-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Sign In
          </button>
          <p className="text-xs text-zinc-400 mt-6">
            If you believe this is a mistake, please contact your administrator to whitelist your email.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white" data-testid="auth-callback">
      <div className="text-center">
        <div className="inline-block w-8 h-8 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-zinc-600 text-sm">Signing you in...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
