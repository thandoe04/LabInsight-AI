import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart2,
  CheckCircle2,
  Clock,
  FileCheck2,
  FlaskConical,
  TestTubes,
  Users,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import api from '../lib/axios';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [charts, setCharts] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumRes, chartRes, actRes] = await Promise.all([
          api.get('/dashboard/summary'),
          api.get('/dashboard/charts'),
          api.get('/dashboard/activity'),
        ]);
        setSummary(sumRes.data);
        setCharts(chartRes.data);
        setActivities(actRes.data);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  const statCards = [
    { title: 'Registered Patients', val: summary?.total_patients ?? 0, icon: Users, color: 'text-blue-600' },
    { title: 'Total Samples', val: summary?.total_samples ?? 0, icon: FlaskConical, color: 'text-teal-600' },
    { title: 'Active Tests', val: summary?.total_tests ?? 0, icon: TestTubes, color: 'text-indigo-600' },
    { title: 'Completed Tests', val: summary?.completed_tests ?? 0, icon: CheckCircle2, color: 'text-emerald-600' },
    { title: 'Pending Tests', val: summary?.pending_tests ?? 0, icon: Clock, color: 'text-amber-600' },
    { title: 'Verified Results', val: summary?.verified_results ?? 0, icon: FileCheck2, color: 'text-cyan-600' },
    { title: 'Data Quality Issues', val: summary?.data_quality_issues ?? 0, icon: AlertTriangle, color: 'text-rose-600' },
    { title: 'Statistical Anomalies', val: summary?.statistical_anomalies ?? 0, icon: Activity, color: 'text-purple-600' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Operational Laboratory Dashboard</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Real-time metrics, test throughput, specimen pipeline status, and quality monitoring.
        </p>
      </div>

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((c) => {
          const Icon = c.icon;
          return (
            <Card key={c.title} className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{c.title}</p>
                  <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{c.val}</p>
                </div>
                <div className={`p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800 ${c.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Activity Trend */}
        <Card title="Monthly Laboratory Activity" subtitle="Specimen intake and test completion trends over time">
          <div className="h-64 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={charts?.monthly_activity || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="samples" name="Samples Registered" stroke="#0d9488" strokeWidth={2} />
                <Line type="monotone" dataKey="results" name="Results Logged" stroke="#6366f1" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Sample Status Distribution */}
        <Card title="Specimen Pipeline Distribution" subtitle="Active sample inventory categorized by processing stage">
          <div className="h-64 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts?.sample_status_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Bar dataKey="count" name="Sample Count" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Recent Laboratory Activity Stream */}
      <Card title="Recent Laboratory Activity" subtitle="Live timeline of specimen intake and stage progression">
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {activities.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No recent activity recorded.</p>
          ) : (
            activities.map((act) => (
              <div key={act.id} className="py-3 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-teal-500" />
                  <span className="font-medium text-slate-800 dark:text-slate-200">{act.description}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="default" size="sm">{act.status}</Badge>
                  <span className="text-[11px] text-slate-400">
                    {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};
