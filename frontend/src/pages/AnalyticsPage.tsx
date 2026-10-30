import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { BarChart3, Binary, Flame, TrendingUp } from 'lucide-react';
import api from '../lib/axios';
import { LaboratoryTest } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { DisclaimerBanner } from '../components/ui/DisclaimerBanner';

export const AnalyticsPage: React.FC = () => {
  const [tests, setTests] = useState<LaboratoryTest[]>([]);
  const [selectedTestId, setSelectedTestId] = useState<string>('');
  const [stats, setStats] = useState<any>(null);
  const [distribution, setDistribution] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'stats' | 'distribution' | 'trends'>('stats');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get('/laboratory/tests').then((res) => {
      setTests(res.data);
      if (res.data.length > 0) {
        setSelectedTestId(res.data[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (!selectedTestId) return;
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const [sRes, dRes, tRes] = await Promise.all([
          api.get(`/analytics/statistics/${selectedTestId}`),
          api.get(`/analytics/distribution/${selectedTestId}`),
          api.get(`/analytics/trends/${selectedTestId}`),
        ]);
        setStats(sRes.data);
        setDistribution(dRes.data);
        setTrends(tRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [selectedTestId]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Statistical Laboratory Analytics Workspace</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Descriptive statistics, empirical distributions, parametric trends, and variance characteristics.
        </p>
      </div>

      <DisclaimerBanner />

      {/* Assay Selector */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Select Laboratory Assay:</span>
            <select
              value={selectedTestId}
              onChange={(e) => setSelectedTestId(e.target.value)}
              className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium"
            >
              {tests.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.test_code}) — {t.measurement_unit || 'Unitless'}
                </option>
              ))}
            </select>
          </div>

          <div className="flex gap-1 border border-slate-200 dark:border-slate-800 rounded-lg p-1 bg-slate-50 dark:bg-slate-900">
            <button
              onClick={() => setActiveTab('stats')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'stats'
                  ? 'bg-white dark:bg-slate-800 text-teal-600 dark:text-teal-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Descriptive Statistics
            </button>
            <button
              onClick={() => setActiveTab('distribution')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'distribution'
                  ? 'bg-white dark:bg-slate-800 text-teal-600 dark:text-teal-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Distribution Histogram
            </button>
            <button
              onClick={() => setActiveTab('trends')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'trends'
                  ? 'bg-white dark:bg-slate-800 text-teal-600 dark:text-teal-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Time-Series Trends
            </button>
          </div>
        </div>
      </Card>

      {/* Tab 1: Descriptive Stats */}
      {activeTab === 'stats' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Card className="md:col-span-2" title="Parametric & Non-Parametric Summary">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Mean (Average)</p>
                <p className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.mean !== null ? `${stats?.mean} ${stats?.measurement_unit || ''}` : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Median (P50)</p>
                <p className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.median !== null ? `${stats?.median} ${stats?.measurement_unit || ''}` : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Std Deviation (s)</p>
                <p className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.std_dev !== null ? stats?.std_dev : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Variance (s²)</p>
                <p className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.variance !== null ? stats?.variance : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Interquartile Range (IQR)</p>
                <p className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.iqr !== null ? stats?.iqr : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Range (Min - Max)</p>
                <p className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100 mt-2">
                  {stats?.min !== null ? `${stats?.min} – ${stats?.max}` : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Skewness</p>
                <p className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.skewness !== null ? stats?.skewness : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Kurtosis</p>
                <p className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.kurtosis !== null ? stats?.kurtosis : '-'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Quartiles (Q1 – Q3)</p>
                <p className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                  {stats?.q1 !== null ? `${stats?.q1} – ${stats?.q3}` : '-'}
                </p>
              </div>
            </div>
          </Card>

          {/* Data Completeness & Population Card */}
          <Card title="Sample Size & Completeness">
            <div className="space-y-4 text-xs">
              <div>
                <span className="text-slate-500 block">Valid Specimen Observations</span>
                <span className="text-2xl font-bold font-mono text-teal-600">{stats?.sample_count ?? 0}</span>
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                <span className="text-slate-500 block">Missing or Null Values</span>
                <span className="text-lg font-bold font-mono text-amber-600">{stats?.missing_count ?? 0}</span>
                <span className="text-[10px] text-slate-400 ml-1">({stats?.missing_percentage ?? 0}%)</span>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-[11px] text-slate-500 space-y-1">
                <p className="font-semibold text-slate-700 dark:text-slate-300">Data Limitations:</p>
                <p>Calculations exclude qualitative results and pending specimens.</p>
                <p>Variance degrees of freedom: N - 1 (unbiased sample estimator).</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 2: Distribution Histogram */}
      {activeTab === 'distribution' && (
        <Card title={`Empirical Distribution — ${stats?.test_name}`} subtitle="Frequency distribution across discretized numeric measurement bins">
          <div className="h-80 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution?.bins || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis
                  dataKey="bin_start"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(val, i) => {
                    const b = distribution?.bins[i];
                    return b ? `${b.bin_start}-${b.bin_end}` : String(val);
                  }}
                />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                <Bar dataKey="count" name="Frequency Count" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      {/* Tab 3: Time Series Trends */}
      {activeTab === 'trends' && (
        <Card title={`Longitudinal Mean Trends — ${stats?.test_name}`} subtitle="Monthly average values across all reported specimens">
          <div className="h-80 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends?.points || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                <Line type="monotone" dataKey="average_value" name="Monthly Average" stroke="#0d9488" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
};
