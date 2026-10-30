import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Lock, Mail, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { DisclaimerBanner } from '../components/ui/DisclaimerBanner';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoFill = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 rounded-xl bg-teal-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
            LI
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          LabInsight AI
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500 dark:text-slate-400">
          Healthcare Laboratory Data Analytics & Machine Learning Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-6 shadow-sm border border-slate-200 dark:border-slate-800 rounded-xl sm:px-10">
          {error && (
            <div className="mb-5 flex items-center gap-2 p-3 text-xs bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 rounded-lg">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Email Address"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@labinsight.dev"
              autoComplete="email"
            />

            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              autoComplete="current-password"
            />

            <Button type="submit" variant="primary" className="w-full mt-2" isLoading={loading}>
              Sign In to Lab Workspace
            </Button>
          </form>

          {/* Quick Demo Credentials Fill Buttons */}
          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Development Demo Accounts:
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleDemoFill('admin@labinsight.dev', 'DevAdmin@2026!')}
                className="p-2 text-left rounded border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              >
                <span className="font-semibold block text-slate-900 dark:text-slate-100">Administrator</span>
                <span className="text-[10px] text-slate-400">admin@labinsight.dev</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill('tech@labinsight.dev', 'DevTech@2026!')}
                className="p-2 text-left rounded border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              >
                <span className="font-semibold block text-slate-900 dark:text-slate-100">Technician</span>
                <span className="text-[10px] text-slate-400">tech@labinsight.dev</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill('analyst@labinsight.dev', 'DevAnalyst@2026!')}
                className="p-2 text-left rounded border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              >
                <span className="font-semibold block text-slate-900 dark:text-slate-100">Analyst</span>
                <span className="text-[10px] text-slate-400">analyst@labinsight.dev</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoFill('researcher@labinsight.dev', 'DevResearch@2026!')}
                className="p-2 text-left rounded border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              >
                <span className="font-semibold block text-slate-900 dark:text-slate-100">Researcher</span>
                <span className="text-[10px] text-slate-400">researcher@labinsight.dev</span>
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4">
          <DisclaimerBanner />
        </div>
      </div>
    </div>
  );
};
