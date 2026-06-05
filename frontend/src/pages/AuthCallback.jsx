import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AuthCallback = () => {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Use useRef synchronously to avoid race conditions under StrictMode
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
        
        // Clear hash and navigate to dashboard with user data
        window.history.replaceState(null, "", "/");
        navigate("/", { state: { user: response.data } });
      } catch (error) {
        console.error("Auth callback failed:", error);
        navigate("/login");
      }
    };
    
    processCallback();
  }, [navigate]);

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
