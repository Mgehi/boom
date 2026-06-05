import { useState } from "react";
import { Package, LogIn, Truck, BarChart3, Upload, Calendar } from "lucide-react";

export const Login = () => {
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = () => {
    setLoading(true);
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const features = [
    { icon: Truck, label: "Automated Manifestation" },
    { icon: Package, label: "Bulk CSV Upload" },
    { icon: BarChart3, label: "Real-time Dashboard" },
    { icon: Upload, label: "Reverse Pickups" },
    { icon: Calendar, label: "Pickup Scheduling" },
  ];

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left: Brand & features */}
      <div className="hidden lg:flex lg:w-1/2 bg-zinc-900 text-white p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Package className="w-8 h-8" />
            <h1 className="text-2xl font-bold tracking-tight">Delhivery Logistics</h1>
          </div>
          <p className="text-zinc-400">Automation platform for small businesses</p>
        </div>
        
        <div>
          <h2 className="text-4xl font-bold tracking-tight mb-6 leading-tight">
            Automate every shipment.<br />
            <span className="text-zinc-500">From order to delivery.</span>
          </h2>
          <div className="space-y-3">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <div key={i} className="flex items-center gap-3 text-zinc-300">
                  <Icon className="w-5 h-5 text-zinc-500" />
                  <span className="text-sm">{f.label}</span>
                </div>
              );
            })}
          </div>
        </div>
        
        <div className="text-xs text-zinc-500">
          Trusted by small businesses across India
        </div>
      </div>

      {/* Right: Login */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="max-w-md w-full">
          <div className="lg:hidden mb-8 text-center">
            <div className="flex items-center justify-center gap-3 mb-2">
              <Package className="w-8 h-8" />
              <h1 className="text-2xl font-bold tracking-tight">Delhivery Logistics</h1>
            </div>
            <p className="text-zinc-500 text-sm">Automation platform for small businesses</p>
          </div>
          
          <div className="border border-zinc-200 rounded-sm bg-white p-8">
            <h2 className="text-3xl font-bold tracking-tight mb-2" data-testid="login-title">Sign in</h2>
            <p className="text-zinc-500 mb-8">
              Access your dashboard and manage shipments
            </p>
            
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              data-testid="google-login-btn"
              className="w-full flex items-center justify-center gap-3 bg-zinc-900 text-white px-6 py-4 rounded-sm font-medium hover:bg-zinc-800 transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#fff"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#fff"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#fff"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#fff"/>
              </svg>
              {loading ? "Redirecting..." : "Sign in with Google"}
            </button>
            
            <p className="text-xs text-zinc-500 mt-6 text-center">
              By signing in, you agree to use this platform for legitimate logistics operations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
