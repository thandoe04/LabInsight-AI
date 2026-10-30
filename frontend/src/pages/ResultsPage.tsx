import React, { useEffect, useState } from 'react';
import { CheckCheck, Edit3, FileSpreadsheet, History, Plus, Search } from 'lucide-react';
import api from '../lib/axios';
import { LaboratoryTest, Sample, TestResult } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';

export const ResultsPage: React.FC = () => {
  const [results, setResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  // Record Modal
  const [isRecordOpen, setIsRecordOpen] = useState(false);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [tests, setTests] = useState<LaboratoryTest[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState('');
  const [selectedTestId, setSelectedTestId] = useState('');
  const [numericVal, setNumericVal] = useState('');
  const [submittingResult, setSubmittingResult] = useState(false);

  // Revise Modal
  const [selectedResultForRevise, setSelectedResultForRevise] = useState<TestResult | null>(null);
  const [revisedVal, setRevisedVal] = useState('');
  const [revisionReason, setRevisionReason] = useState('');
  const [revising, setRevising] = useState(false);

  // History Modal
  const [historyResult, setHistoryResult] = useState<TestResult | null>(null);
  const [historyItems, setHistoryItems] = useState<any[]>([]);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const res = await api.get('/results', {
        params: { status: statusFilter || undefined, page_size: 30 },
      });
      setResults(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [statusFilter]);

  const openRecordModal = async () => {
    try {
      const [sRes, tRes] = await Promise.all([
        api.get('/samples', { params: { page_size: 50 } }),
        api.get('/laboratory/tests'),
      ]);
      setSamples(sRes.data.items);
      setTests(tRes.data);
      if (sRes.data.items.length > 0) setSelectedSampleId(sRes.data.items[0].id);
      if (tRes.data.length > 0) setSelectedTestId(tRes.data[0].id);
      setIsRecordOpen(true);
    } catch (err) {
      alert('Failed to load specimen and assay options.');
    }
  };

  const handleRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingResult(true);
    try {
      await api.post('/results', {
        sample_id: selectedSampleId,
        test_id: selectedTestId,
        numeric_value: numericVal ? parseFloat(numericVal) : null,
      });
      setIsRecordOpen(false);
      setNumericVal('');
      fetchResults();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to record test result.');
    } finally {
      setSubmittingResult(false);
    }
  };

  const handleVerify = async (resId: string) => {
    if (!confirm('Verify this laboratory result? Verified results cannot be overwritten without revision auditing.')) return;
    try {
      await api.post(`/results/${resId}/verify`, {});
      fetchResults();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to verify result.');
    }
  };

  const handleRevise = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedResultForRevise || !revisionReason.trim()) return;
    setRevising(true);
    try {
      await api.patch(`/results/${selectedResultForRevise.id}/revise`, {
        new_numeric_value: revisedVal ? parseFloat(revisedVal) : null,
        reason: revisionReason.trim(),
      });
      setSelectedResultForRevise(null);
      setRevisedVal('');
      setRevisionReason('');
      fetchResults();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to revise result.');
    } finally {
      setRevising(false);
    }
  };

  const openHistory = async (res: TestResult) => {
    setHistoryResult(res);
    try {
      const hRes = await api.get(`/results/${res.id}/history`);
      setHistoryItems(hRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Laboratory Results & Revisions</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Test results with verified state enforcement and immutable correction histories.
          </p>
        </div>
        <Button onClick={openRecordModal} className="gap-2">
          <Plus className="w-4 h-4" /> Enter Test Result
        </Button>
      </div>

      <Card>
        {/* Filter bar */}
        <div className="flex gap-3 mb-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Result Statuses</option>
            <option value="pending">Pending Verification</option>
            <option value="verified">Verified</option>
            <option value="corrected">Corrected / Revised</option>
          </select>
        </div>

        {/* Results Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Specimen Code</th>
                <th className="py-2.5 px-3 font-semibold">Assay / Test</th>
                <th className="py-2.5 px-3 font-semibold">Measurement</th>
                <th className="py-2.5 px-3 font-semibold">Reference Flag</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 font-semibold">Measured At</th>
                <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">Loading laboratory results...</td>
                </tr>
              ) : results.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">No test results found.</td>
                </tr>
              ) : (
                results.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-mono font-bold text-teal-600 dark:text-teal-400">{r.sample_code}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-slate-900 dark:text-slate-100">{r.test_name}</span>
                      <span className="text-[10px] text-slate-400 ml-1.5 font-mono">({r.test_code})</span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-bold">
                      {r.numeric_value !== null ? `${r.numeric_value} ${r.measurement_unit || ''}` : r.qualitative_value}
                    </td>
                    <td className="py-2.5 px-3">
                      {r.is_above_upper_limit ? (
                        <Badge variant="danger" size="sm">HIGH</Badge>
                      ) : r.is_below_lower_limit ? (
                        <Badge variant="warning" size="sm">LOW</Badge>
                      ) : (
                        <Badge variant="success" size="sm">NORMAL</Badge>
                      )}
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge variant={r.status === 'verified' ? 'success' : r.status === 'corrected' ? 'info' : 'warning'} size="sm">
                        {r.status}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{new Date(r.measured_at).toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-right space-x-1.5">
                      {r.status !== 'verified' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleVerify(r.id)}
                          className="gap-1"
                        >
                          <CheckCheck className="w-3.5 h-3.5" /> Verify
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedResultForRevise(r);
                          setRevisedVal(r.numeric_value !== null ? String(r.numeric_value) : '');
                        }}
                        className="gap-1"
                      >
                        <Edit3 className="w-3.5 h-3.5" /> Revise
                      </Button>
                      {r.revisions_count > 0 && (
                        <Button variant="ghost" size="sm" onClick={() => openHistory(r)} className="text-teal-600">
                          {r.revisions_count} revs
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Enter Result Modal */}
      <Modal isOpen={isRecordOpen} onClose={() => setIsRecordOpen(false)} title="Record Laboratory Test Result">
        <form onSubmit={handleRecord} className="space-y-4 text-xs">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Select Sample
            </label>
            <select
              value={selectedSampleId}
              onChange={(e) => setSelectedSampleId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              {samples.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.sample_code} ({s.sample_type}) — Status: {s.status}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Select Test Definition
            </label>
            <select
              value={selectedTestId}
              onChange={(e) => setSelectedTestId(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              {tests.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.test_code}) — {t.measurement_unit || 'No unit'}
                </option>
              ))}
            </select>
          </div>

          <Input
            label="Numeric Measured Value"
            type="number"
            step="any"
            required
            value={numericVal}
            onChange={(e) => setNumericVal(e.target.value)}
            placeholder="e.g. 14.2"
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsRecordOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submittingResult}>
              Log Result
            </Button>
          </div>
        </form>
      </Modal>

      {/* Controlled Revision Modal */}
      <Modal
        isOpen={Boolean(selectedResultForRevise)}
        onClose={() => setSelectedResultForRevise(null)}
        title={`Controlled Result Correction — ${selectedResultForRevise?.test_name}`}
      >
        <form onSubmit={handleRevise} className="space-y-4 text-xs">
          <p className="text-slate-600 dark:text-slate-300">
            Original recorded value:{' '}
            <strong className="font-mono">{selectedResultForRevise?.numeric_value} {selectedResultForRevise?.measurement_unit}</strong>
          </p>

          <Input
            label="New Corrected Numeric Value"
            type="number"
            step="any"
            required
            value={revisedVal}
            onChange={(e) => setRevisedVal(e.target.value)}
          />

          <Input
            label="Mandatory Clinical Audit Reason for Revision"
            required
            value={revisionReason}
            onChange={(e) => setRevisionReason(e.target.value)}
            placeholder="e.g. Repeat run on dilution, transcription error correction..."
            helperText="Never silently overwrites. All revisions are permanently logged with operator signature."
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setSelectedResultForRevise(null)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={revising}>
              Commit Audited Revision
            </Button>
          </div>
        </form>
      </Modal>

      {/* Revision History Modal */}
      <Modal
        isOpen={Boolean(historyResult)}
        onClose={() => setHistoryResult(null)}
        title={`Revision History — ${historyResult?.test_name} (${historyResult?.sample_code})`}
      >
        <div className="space-y-3 text-xs">
          {historyItems.length === 0 ? (
            <p className="text-slate-400 py-4 text-center">No revision history found.</p>
          ) : (
            historyItems.map((rev) => (
              <div key={rev.revision_number} className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg">
                <div className="flex items-center justify-between pb-1.5 border-b border-slate-100 dark:border-slate-800">
                  <span className="font-bold text-slate-800 dark:text-slate-200">Revision #{rev.revision_number}</span>
                  <span className="text-[10px] text-slate-400">{new Date(rev.revised_at).toLocaleString()}</span>
                </div>
                <div className="mt-2 space-y-1">
                  <p>
                    <span className="text-slate-400">Previous:</span> <span className="line-through font-mono text-rose-500">{rev.previous_numeric_value}</span>{' '}
                    &rarr; <span className="font-mono font-bold text-emerald-600">{rev.new_numeric_value}</span>
                  </p>
                  <p><span className="text-slate-400">Reason:</span> <span className="font-medium">{rev.reason}</span></p>
                  {rev.revised_by_name && <p className="text-[10px] text-slate-400">By: {rev.revised_by_name}</p>}
                </div>
              </div>
            ))
          )}
        </div>
      </Modal>
    </div>
  );
};
