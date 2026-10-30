import React, { useEffect, useState } from 'react';
import { ArrowRight, Clock, FlaskConical, History, Plus, Search } from 'lucide-react';
import api from '../lib/axios';
import { Sample } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';

const STATUS_NEXT_MAP: Record<string, string[]> = {
  registered: ['collected', 'rejected'],
  collected: ['received', 'rejected'],
  received: ['processing', 'rejected'],
  processing: ['completed', 'rejected'],
  completed: ['archived'],
  rejected: ['archived'],
  archived: [],
};

export const SamplesPage: React.FC = () => {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Register Modal
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [patientCode, setPatientCode] = useState('');
  const [sampleType, setSampleType] = useState('whole_blood');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Status Transition Modal
  const [selectedSample, setSelectedSample] = useState<Sample | null>(null);
  const [targetStatus, setTargetStatus] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [transitioning, setTransitioning] = useState(false);

  // History Modal
  const [historySample, setHistorySample] = useState<Sample | null>(null);
  const [historyItems, setHistoryItems] = useState<any[]>([]);

  const fetchSamples = async () => {
    setLoading(true);
    try {
      const res = await api.get('/samples', {
        params: {
          page,
          page_size: 20,
          search: search.trim() || undefined,
          status: statusFilter || undefined,
        },
      });
      setSamples(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSamples();
  }, [page, search, statusFilter]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      // Find patient ID by patient code or use first patient
      const pRes = await api.get('/patients', { params: { search: patientCode.trim() } });
      if (!pRes.data.items || pRes.data.items.length === 0) {
        alert('Patient with this code not found.');
        setSubmitting(false);
        return;
      }
      const patientId = pRes.data.items[0].id;

      await api.post('/samples', {
        patient_id: patientId,
        sample_type: sampleType,
        collection_notes: notes || null,
        collected_at: new Date().toISOString(),
      });
      setIsRegisterOpen(false);
      setPatientCode('');
      setNotes('');
      fetchSamples();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to register sample.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusTransition = async () => {
    if (!selectedSample || !targetStatus) return;
    setTransitioning(true);
    try {
      await api.patch(`/samples/${selectedSample.id}/status`, {
        new_status: targetStatus,
        rejection_reason: targetStatus === 'rejected' ? rejectReason : undefined,
      });
      setSelectedSample(null);
      setTargetStatus('');
      setRejectReason('');
      fetchSamples();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to transition status.');
    } finally {
      setTransitioning(false);
    }
  };

  const viewHistory = async (sample: Sample) => {
    setHistorySample(sample);
    try {
      const res = await api.get(`/samples/${sample.id}/history`);
      setHistoryItems(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Specimen Tracking & Management</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Strict chain of custody and state machine transitions for biological samples.
          </p>
        </div>
        <Button onClick={() => setIsRegisterOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" /> Intake Sample
        </Button>
      </div>

      <Card>
        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search sample code or type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Statuses</option>
            <option value="registered">Registered</option>
            <option value="collected">Collected</option>
            <option value="received">Received</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Sample Code</th>
                <th className="py-2.5 px-3 font-semibold">Matrix Type</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 font-semibold">Collected</th>
                <th className="py-2.5 px-3 font-semibold">Received</th>
                <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400">Loading specimen list...</td>
                </tr>
              ) : samples.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400">No samples found.</td>
                </tr>
              ) : (
                samples.map((s) => {
                  const nextStates = STATUS_NEXT_MAP[s.status] || [];
                  return (
                    <tr key={s.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="py-2.5 px-3 font-mono font-bold text-teal-600 dark:text-teal-400">{s.sample_code}</td>
                      <td className="py-2.5 px-3 capitalize">{s.sample_type.replace('_', ' ')}</td>
                      <td className="py-2.5 px-3">
                        <Badge
                          variant={
                            s.status === 'completed'
                              ? 'success'
                              : s.status === 'rejected'
                              ? 'danger'
                              : s.status === 'processing'
                              ? 'info'
                              : 'warning'
                          }
                          size="sm"
                        >
                          {s.status}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {s.collected_at ? new Date(s.collected_at).toLocaleString() : 'Pending'}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {s.received_at ? new Date(s.received_at).toLocaleString() : 'Pending'}
                      </td>
                      <td className="py-2.5 px-3 text-right space-x-1.5">
                        {nextStates.length > 0 && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                              setSelectedSample(s);
                              setTargetStatus(nextStates[0]);
                            }}
                          >
                            Advance
                          </Button>
                        )}
                        <Button variant="outline" size="sm" onClick={() => viewHistory(s)}>
                          <History className="w-3.5 h-3.5" />
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Intake Modal */}
      <Modal isOpen={isRegisterOpen} onClose={() => setIsRegisterOpen(false)} title="Register Specimen Intake">
        <form onSubmit={handleRegister} className="space-y-4 text-xs">
          <Input
            label="Patient Code"
            required
            placeholder="e.g. PAT-SYN-8812"
            value={patientCode}
            onChange={(e) => setPatientCode(e.target.value)}
            helperText="Enter exact pseudonymous patient code"
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Specimen Matrix Type
            </label>
            <select
              value={sampleType}
              onChange={(e) => setSampleType(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="whole_blood">Whole Blood (EDTA)</option>
              <option value="serum">Serum (SST)</option>
              <option value="plasma">Plasma (Heparin)</option>
              <option value="urine">Urine</option>
              <option value="csf">Cerebrospinal Fluid (CSF)</option>
            </select>
          </div>

          <Input
            label="Intake & Collection Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Hemolysis check, fasting status, volume..."
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsRegisterOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submitting}>
              Intake Specimen
            </Button>
          </div>
        </form>
      </Modal>

      {/* Transition Modal */}
      <Modal
        isOpen={Boolean(selectedSample)}
        onClose={() => setSelectedSample(null)}
        title={`Advance Status — ${selectedSample?.sample_code}`}
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600 dark:text-slate-300">
            Current stage: <strong className="uppercase font-mono text-teal-600">{selectedSample?.status}</strong>
          </p>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Select Valid Target Status
            </label>
            <select
              value={targetStatus}
              onChange={(e) => setTargetStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              {(STATUS_NEXT_MAP[selectedSample?.status || ''] || []).map((st) => (
                <option key={st} value={st}>
                  {st.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {targetStatus === 'rejected' && (
            <Input
              label="Mandatory Rejection Reason"
              required
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Clotted specimen, insufficient volume (QNS)..."
            />
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" onClick={() => setSelectedSample(null)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleStatusTransition} isLoading={transitioning}>
              Confirm Transition
            </Button>
          </div>
        </div>
      </Modal>

      {/* History Audit Modal */}
      <Modal
        isOpen={Boolean(historySample)}
        onClose={() => setHistorySample(null)}
        title={`Status Audit Trail — ${historySample?.sample_code}`}
      >
        <div className="space-y-3 text-xs">
          {historyItems.map((h, i) => (
            <div key={h.id} className="flex items-start gap-3 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
              <div className="w-5 h-5 rounded-full bg-teal-50 dark:bg-teal-950 flex items-center justify-center text-teal-600 text-[10px] font-bold mt-0.5">
                {i + 1}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                    {h.previous_status || 'INIT'} &rarr; {h.new_status}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {new Date(h.changed_at).toLocaleString()}
                  </span>
                </div>
                {h.notes && <p className="text-slate-500 mt-1">{h.notes}</p>}
                {h.changed_by_name && <p className="text-[10px] text-slate-400 mt-0.5">User: {h.changed_by_name}</p>}
              </div>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
};
