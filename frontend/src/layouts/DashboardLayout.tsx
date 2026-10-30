import React, { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertOctagon,
  BarChart3,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  Database,
  FileSpreadsheet,
  FileText,
  FlaskConical,
  LogOut,
  Menu,
  ShieldAlert,
  TestTubes,
  UserCheck,
  Users,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/ui/Badge';
import { DisclaimerBanner } from '../components/ui/DisclaimerBanner';

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Activity },
    { name: 'Patients', href: '/patients', icon: Users },
    { name: 'Samples', href: '/samples', icon: FlaskConical },
    { name: 'Lab Catalogue', href: '/laboratory', icon: TestTubes },
    { name: 'Results & Revisions', href: '/results', icon: FileSpreadsheet },
    { name: 'Statistical Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'ML & Data Quality', href: '/ml', icon: BrainCircuit },
    { name: 'Reports', href: '/reports', icon: FileText },
    { name: 'User Management', href: '/users', icon: UserCheck },
    { name: 'Audit Trail', href: '/audit', icon: ShieldAlert },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-all duration-300 z-20 ${
          isCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* App Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-100 dark:border-slate-800">
          {!isCollapsed && (
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold text-base shadow-sm">
                LI
              </div>
              <div>
                <span className="font-bold text-slate-900 dark:text-slate-100 text-sm tracking-tight">LabInsight AI</span>
                <span className="block text-[10px] text-teal-600 dark:text-teal-400 font-semibold tracking-wide">CLINICAL ANALYTICS</span>
              </div>
            </div>
          )}
          {isCollapsed && (
            <div className="w-8 h-8 mx-auto rounded-lg bg-teal-600 flex items-center justify-center text-white font-bold text-base">
              LI
            </div>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 font-semibold shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
                title={isCollapsed ? item.name : undefined}
              >
                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-teal-600 dark:text-teal-400' : 'text-slate-400'}`} />
                {!isCollapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User Card at bottom of sidebar */}
        <div className="p-3 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50">
            <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300 font-bold text-xs flex-shrink-0">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">{user?.full_name}</p>
                <p className="text-[10px] text-slate-500 capitalize">{user?.role || 'Guest'}</p>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 z-10 flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Environment</span>
            <Badge variant="info" size="sm">Development Mode</Badge>
            <Badge variant="success" size="sm">PostgreSQL Connected</Badge>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="block text-xs font-semibold text-slate-800 dark:text-slate-200">{user?.email}</span>
              <span className="block text-[10px] text-slate-400 capitalize">Role: {user?.role}</span>
            </div>
          </div>
        </header>

        {/* Global Mandatory Clinical Disclaimer Banner */}
        <div className="px-6 pt-3">
          <DisclaimerBanner />
        </div>

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
