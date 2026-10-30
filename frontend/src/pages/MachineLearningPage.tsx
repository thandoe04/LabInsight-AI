import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle,
  Eye,
  Layers,
  Play,
  RotateCcw,
  ScatterChart,
  ShieldAlert,
} from 'lucide-react';
import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart as RechartsScatter,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import api from '../lib/axios';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { DisclaimerBanner } from '../components/ui/DisclaimerBanner';

export const MachineLearningPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'anomaly' | 'clustering' | 'quality'>('anomaly');

  // Anomaly State
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState<any | null>(null);
  const [reviewStatus, setReviewStatus] = useState('reviewed');
  const [reviewerNotes, setReviewerNotes] = useState('');
  const [runningAnomaly, setRunningAnomaly] = useState(false);

  // Clustering State
  const [clusteringResult, setClusteringResult] = useState<any>(null);
  const [runningClustering, setRunningClustering] = useState(false);
  const [clusterAlgorithm, setClusterAlgorithm] = useState('kmeans');

  // Data Quality State
  const [dqIssues, setDqIssues] = useState<any[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<any | null>(null);
  const [resolutionStatus, setResolutionStatus] = useState('resolved');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [runningQuality, setRunningQuality] = useState(false);

  const fetchAnomalies = async () => {
    try {
      const res = await api.get('/ml/anomalies');
      setAnomalies(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchQualityIssues = async () => {
    try {
      const res = await api.get('/ml/data-quality');
      setDqIssues(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchAnomalies();
    fetchQualityIssues();
  }, []);

  const handleRunAnomaly = async () => {
    setRunningAnomaly(true);
    try {
      // 1. Create experiment
      const expRes = await api.post('/ml/experiments', {
        name: `Automated Isolation Forest Run — ${new Date().toLocaleTimeString()}`,
        experiment_type: 'anomaly_detection',
        algorithm: 'isolation_forest',
      });
      // 2. Run experiment
      await api.post(`/ml/experiments/${expRes.data.id}/run`, {});
      fetchAnomalies();
      alert('Anomaly detection model execution completed successfully.');
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to execute anomaly detection.');
    } finally {
      setRunningAnomaly(false);
    }
  };

  const handleReviewAnomaly = async () => {
    if (!selectedAnomaly || !reviewerNotes.trim()) return;
    try {
      await api.patch(`/ml/anomalies/${selectedAnomaly.id}/review`, {
        review_status: reviewStatus,
        reviewer_notes: reviewerNotes.trim(),
      });
      setSelectedAnomaly(null);
      setReviewerNotes('');
      fetchAnomalies();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to submit review.');
    }
  };

  const handleRunClustering = async () => {
    setRunningClustering(true);
    try {
      const expRes = await api.post('/ml/experiments', {
        name: `Unsupervised Clustering (${clusterAlgorithm.toUpperCase()}) — ${new Date().toLocaleTimeString()}`,
        experiment_type: 'clustering',
        algorithm: clusterAlgorithm,
      });
      const runRes = await api.post(`/ml/experiments/${expRes.data.id}/run`, {});
      setClusteringResult(runRes.data.results);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to execute clustering.');
    } finally {
      setRunningClustering(false);
    }
  };

  const handleRunQualityScan = async () => {
    setRunningQuality(true);
    try {
      const expRes = await api.post('/ml/experiments', {
        name: `Data Quality Screening Audit — ${new Date().toLocaleTimeString()}`,
        experiment_type: 'data_quality',
      });
      await api.post(`/ml/experiments/${expRes.data.id}/run`, {});
      fetchQualityIssues();
      alert('Data quality screening audit complete.');
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to run quality audit.');
    } finally {
      setRunningQuality(false);
    }
  };

  const handleResolveIssue = async () => {
    if (!selectedIssue || !resolutionNotes.trim()) return;
    try {
      await api.patch(`/ml/data-quality/${selectedIssue.id}/resolve`, {
        resolution_status: resolutionStatus,
        resolution_notes: resolutionNotes.trim(),
      });
      setSelectedIssue(null);
      setResolutionNotes('');
      fetchQualityIssues();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to submit issue resolution.');
    }
  };

  const CLUSTER_COLORS = ['#0d9488', '#6366f1', '#f59e0b', '#ec4899', '#3b82f6'];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Machine Learning & Data Intelligence</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Unsupervised pattern discovery, multivariate anomaly scoring, and intelligent data quality auditing.
        </p>
      </div>

      <DisclaimerBanner />

      {/* Mode Navigation Tabs */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab('anomaly')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'anomaly'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <BrainCircuit className="w-4 h-4" /> Anomaly Detection
        </button>

        <button
          onClick={() => setActiveTab('clustering')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'clustering'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" /> Unsupervised Clustering (PCA)
        </button>

        <button
          onClick={() => setActiveTab('quality')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
            activeTab === 'quality'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <AlertTriangle className="w-4 h-4" /> Data Quality Intelligence
        </button>
      </div>

      {/* ─── TAB 1: ANOMALY DETECTION ────────────────────────────────────── */}
      {activeTab === 'anomaly' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Multivariate Outlier Detection</h2>
              <p className="text-xs text-slate-500">Evaluates statistical anomaly scores across correlated multi-analyte panels.</p>
            </div>
            <Button onClick={handleRunAnomaly} isLoading={runningAnomaly} className="gap-2">
              <Play className="w-4 h-4" /> Execute Anomaly Model
            </Button>
          </div>

          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">Entity Type</th>
                    <th className="py-2.5 px-3 font-semibold">Anomaly Score</th>
                    <th className="py-2.5 px-3 font-semibold">Algorithm</th>
                    <th className="py-2.5 px-3 font-semibold">Contributing Features (Z-Score)</th>
                    <th className="py-2.5 px-3 font-semibold">Review Status</th>
                    <th className="py-2.5 px-3 font-semibold">Flagged Date</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {anomalies.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-6 text-slate-400">
                        No anomaly records found. Click 'Execute Anomaly Model' to score current records.
                      </td>
                    </tr>
                  ) : (
                    anomalies.map((a) => (
                      <tr key={a.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                        <td className="py-2.5 px-3 font-mono capitalize">{a.entity_type}</td>
                        <td className="py-2.5 px-3 font-mono font-bold text-rose-600 dark:text-rose-400">
                          {a.anomaly_score.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3 capitalize">{a.detection_method.replace('_', ' ')}</td>
                        <td className="py-2.5 px-3">
                          {a.contributing_features ? (
                            <div className="flex gap-1.5 flex-wrap">
                              {Object.entries(a.contributing_features).map(([feat, z]: any) => (
                                <span key={feat} className="text-[10px] bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded font-mono">
                                  {feat}: {z}σ
                                </span>
                              ))}
                            </div>
                          ) : '-'}
                        </td>
                        <td className="py-2.5 px-3">
                          <Badge
                            variant={a.review_status === 'reviewed' ? 'success' : a.review_status === 'dismissed' ? 'default' : 'warning'}
                            size="sm"
                          >
                            {a.review_status}
                          </Badge>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">{new Date(a.created_at).toLocaleDateString()}</td>
                        <td className="py-2.5 px-3 text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedAnomaly(a);
                              setReviewerNotes(a.reviewer_notes || '');
                              setReviewStatus(a.review_status === 'pending' ? 'reviewed' : a.review_status);
                            }}
                          >
                            Review
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ─── TAB 2: CLUSTERING ───────────────────────────────────────────── */}
      {activeTab === 'clustering' && (
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Clustering Algorithm:</span>
                <select
                  value={clusterAlgorithm}
                  onChange={(e) => setClusterAlgorithm(e.target.value)}
                  className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium"
                >
                  <option value="kmeans">K-Means (k=3)</option>
                  <option value="dbscan">DBSCAN (Density-Based)</option>
                  <option value="hierarchical">Hierarchical (Ward Linkage)</option>
                </select>
              </div>

              <Button onClick={handleRunClustering} isLoading={runningClustering} className="gap-2">
                <Play className="w-4 h-4" /> Run Clustering Experiment
              </Button>
            </div>
          </Card>

          {clusteringResult ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <Card className="md:col-span-2" title="Principal Component Analysis (PCA) 2D Projection">
                <div className="h-80 mt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsScatter>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" dataKey="x" name="PCA Component 1" tick={{ fontSize: 10 }} />
                      <YAxis type="number" dataKey="y" name="PCA Component 2" tick={{ fontSize: 10 }} />
                      <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                      <Scatter data={clusteringResult.coordinates_2d || []}>
                        {(clusteringResult.coordinates_2d || []).map((entry: any, index: number) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={CLUSTER_COLORS[Math.abs(entry.cluster) % CLUSTER_COLORS.length]}
                          />
                        ))}
                      </Scatter>
                    </RechartsScatter>
                  </ResponsiveContainer>
                </div>
              </Card>

              <Card title="Clustering Validation Metrics">
                <div className="space-y-4 text-xs">
                  <div>
                    <span className="text-slate-500 block">Identified Clusters</span>
                    <span className="text-2xl font-bold font-mono text-teal-600">{clusteringResult.cluster_count}</span>
                  </div>

                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500 block">Silhouette Score (-1 to 1)</span>
                    <span className="text-lg font-bold font-mono text-slate-800 dark:text-slate-200">
                      {clusteringResult.metrics?.silhouette_score !== null ? clusteringResult.metrics.silhouette_score : 'N/A'}
                    </span>
                    <p className="text-[10px] text-slate-400 mt-0.5">Higher values denote well-separated clusters.</p>
                  </div>

                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500 block">Davies-Bouldin Index</span>
                    <span className="text-lg font-bold font-mono text-slate-800 dark:text-slate-200">
                      {clusteringResult.metrics?.davies_bouldin_index !== null ? clusteringResult.metrics.davies_bouldin_index : 'N/A'}
                    </span>
                    <p className="text-[10px] text-slate-400 mt-0.5">Lower values indicate tighter clustering compactness.</p>
                  </div>
                </div>
              </Card>
            </div>
          ) : (
            <Card className="text-center py-12">
              <Layers className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-xs text-slate-400">Click 'Run Clustering Experiment' to project and cluster specimen patterns.</p>
            </Card>
          )}
        </div>
      )}

      {/* ─── TAB 3: DATA QUALITY ─────────────────────────────────────────── */}
      {activeTab === 'quality' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Data Quality Intelligence Audit</h2>
              <p className="text-xs text-slate-500">Detects impossible physiological ranges, timestamp inconsistencies, and format errors.</p>
            </div>
            <Button onClick={handleRunQualityScan} isLoading={runningQuality} className="gap-2">
              <Play className="w-4 h-4" /> Run Quality Screening
            </Button>
          </div>

          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">Severity</th>
                    <th className="py-2.5 px-3 font-semibold">Defect Type</th>
                    <th className="py-2.5 px-3 font-semibold">Entity Type</th>
                    <th className="py-2.5 px-3 font-semibold">Description</th>
                    <th className="py-2.5 px-3 font-semibold">Resolution Status</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {dqIssues.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-6 text-slate-400">
                        No active data quality defects detected. Run screening to verify dataset integrity.
                      </td>
                    </tr>
                  ) : (
                    dqIssues.map((iss) => (
                      <tr key={iss.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                        <td className="py-2.5 px-3">
                          <Badge
                            variant={
                              iss.severity === 'critical'
                                ? 'danger'
                                : iss.severity === 'warning'
                                ? 'warning'
                                : 'default'
                            }
                            size="sm"
                          >
                            {iss.severity}
                          </Badge>
                        </td>
                        <td className="py-2.5 px-3 font-mono capitalize">{iss.issue_type.replace('_', ' ')}</td>
                        <td className="py-2.5 px-3 capitalize">{iss.entity_type}</td>
                        <td className="py-2.5 px-3 max-w-sm">{iss.description}</td>
                        <td className="py-2.5 px-3">
                          <Badge variant={iss.resolution_status === 'resolved' ? 'success' : 'default'} size="sm">
                            {iss.resolution_status}
                          </Badge>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedIssue(iss);
                              setResolutionNotes(iss.resolution_notes || '');
                            }}
                          >
                            Resolve
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Review Anomaly Modal */}
      <Modal
        isOpen={Boolean(selectedAnomaly)}
        onClose={() => setSelectedAnomaly(null)}
        title="Authorised Review of Statistical Anomaly"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600 dark:text-slate-300">
            Anomaly Score: <strong className="font-mono text-rose-600">{selectedAnomaly?.anomaly_score?.toFixed(4)}</strong>
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Review Decision
            </label>
            <select
              value={reviewStatus}
              onChange={(e) => setReviewStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="reviewed">Reviewed & Verified Normal Variation</option>
              <option value="dismissed">Dismissed as Artifact / Instrument Noise</option>
              <option value="escalated">Escalated for Laboratory Repeat Analysis</option>
            </select>
          </div>

          <Input
            label="Mandatory Reviewer Audit Notes"
            required
            value={reviewerNotes}
            onChange={(e) => setReviewerNotes(e.target.value)}
            placeholder="Clinical/analytical rationale for the decision..."
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setSelectedAnomaly(null)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleReviewAnomaly}>
              Save Review Decision
            </Button>
          </div>
        </div>
      </Modal>

      {/* Resolve Quality Issue Modal */}
      <Modal
        isOpen={Boolean(selectedIssue)}
        onClose={() => setSelectedIssue(null)}
        title="Resolve Data Quality Issue"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600 dark:text-slate-300">{selectedIssue?.description}</p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Resolution Status
            </label>
            <select
              value={resolutionStatus}
              onChange={(e) => setResolutionStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="resolved">Resolved / Correction Applied</option>
              <option value="dismissed">Dismissed</option>
              <option value="false_positive">False Positive</option>
            </select>
          </div>

          <Input
            label="Resolution Action Notes"
            required
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="Action taken to address or dismiss..."
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setSelectedIssue(null)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleResolveIssue}>
              Confirm Resolution
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
