import React, { useEffect, useState } from 'react';
import { Eye, Plus, Search, UserCheck, Users } from 'lucide-react';
import api from '../lib/axios';
import { Patient } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';

export const PatientsPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Registration modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formBirth, setFormBirth] = useState('');
  const [formSex, setFormSex] = useState('female');
  const [formFirst, setFormFirst] = useState('');
  const [formLast, setFormLast] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // History modal
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const res = await api.get('/patients', {
        params: { page, page_size: 15, search: search.trim() || undefined },
      });
      setPatients(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, [page, search]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/patients', {
        date_of_birth: formBirth || null,
        biological_sex: formSex,
        first_name: formFirst || null,
        last_name: formLast || null,
        is_synthetic: true,
      });
      setIsModalOpen(false);
      setFormBirth('');
      setFormFirst('');
      setFormLast('');
      fetchPatients();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create patient.');
    } finally {
      setSubmitting(false);
    }
  };

  const openHistory = async (patient: Patient) => {
    setSelectedPatient(patient);
    setHistoryLoading(true);
    try {
      const res = await api.get(`/patients/${patient.id}/history`);
      setHistory(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setHistoryLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Patient Profile Management</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Pseudonymous patient index with minimal identifiable demographics.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" /> Register Patient
        </Button>
      </div>

      <Card>
        {/* Search Bar */}
        <div className="mb-4 max-w-sm">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by code or name..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Patient Code</th>
                <th className="py-2.5 px-3 font-semibold">Name</th>
                <th className="py-2.5 px-3 font-semibold">Sex</th>
                <th className="py-2.5 px-3 font-semibold">Birth Date</th>
                <th className="py-2.5 px-3 font-semibold">Dataset Type</th>
                <th className="py-2.5 px-3 font-semibold">Registered</th>
                <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">Loading patients...</td>
                </tr>
              ) : patients.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">No patient records found.</td>
                </tr>
              ) : (
                patients.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-mono font-bold text-teal-600 dark:text-teal-400">{p.patient_code}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-900 dark:text-slate-100">
                      {p.first_name || p.last_name ? `${p.first_name || ''} ${p.last_name || ''}` : 'Pseudonymous'}
                    </td>
                    <td className="py-2.5 px-3 capitalize">{p.biological_sex || 'Unspecified'}</td>
                    <td className="py-2.5 px-3">{p.date_of_birth || '-'}</td>
                    <td className="py-2.5 px-3">
                      <Badge variant={p.is_synthetic ? 'info' : 'default'} size="sm">
                        {p.is_synthetic ? 'Synthetic' : 'Authorized'}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{new Date(p.created_at).toLocaleDateString()}</td>
                    <td className="py-2.5 px-3 text-right">
                      <Button variant="outline" size="sm" onClick={() => openHistory(p)} className="gap-1">
                        <Eye className="w-3.5 h-3.5" /> History
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Registration Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Register Patient Record">
        <form onSubmit={handleCreate} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <Input label="First Name (Optional)" value={formFirst} onChange={(e) => setFormFirst(e.target.value)} />
            <Input label="Last Name (Optional)" value={formLast} onChange={(e) => setFormLast(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Date of Birth"
              type="date"
              value={formBirth}
              onChange={(e) => setFormBirth(e.target.value)}
              helperText="Used strictly for age-specific reference interval matching"
            />
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Biological Sex
              </label>
              <select
                value={formSex}
                onChange={(e) => setFormSex(e.target.value)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="intersex">Intersex</option>
                <option value="not_specified">Not Specified</option>
              </select>
            </div>
          </div>

          <p className="text-[11px] text-slate-400">
            Note: A pseudonymous patient code (e.g. PAT-XXXX-XXXX) will be generated automatically.
          </p>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submitting}>
              Register Patient
            </Button>
          </div>
        </form>
      </Modal>

      {/* History Drawer Modal */}
      <Modal
        isOpen={Boolean(selectedPatient)}
        onClose={() => setSelectedPatient(null)}
        title={`Laboratory History — ${selectedPatient?.patient_code}`}
        maxWidth="xl"
      >
        {historyLoading ? (
          <div className="py-6 text-center text-xs text-slate-400">Loading specimen history...</div>
        ) : history.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-400">No samples registered for this patient.</div>
        ) : (
          <div className="space-y-4 text-xs">
            {history.map((s) => (
              <div key={s.id} className="border border-slate-200 dark:border-slate-800 rounded-lg p-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-teal-600">{s.sample_code}</span>
                    <Badge variant="default" size="sm">{s.sample_type}</Badge>
                  </div>
                  <Badge variant={s.status === 'completed' ? 'success' : 'warning'} size="sm">
                    {s.status}
                  </Badge>
                </div>

                {s.results.length === 0 ? (
                  <p className="text-[11px] text-slate-400">No results recorded yet for this sample.</p>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800">
                    {s.results.map((r: any) => (
                      <div key={r.id} className="py-1.5 flex items-center justify-between">
                        <div>
                          <span className="font-semibold text-slate-800 dark:text-slate-200">{r.test_name}</span>
                          <span className="text-[11px] text-slate-400 ml-1.5">({r.test_code})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold">
                            {r.numeric_value !== null ? `${r.numeric_value} ${r.measurement_unit || ''}` : r.qualitative_value}
                          </span>
                          {r.is_above_upper_limit && <Badge variant="danger" size="sm">HIGH</Badge>}
                          {r.is_below_lower_limit && <Badge variant="warning" size="sm">LOW</Badge>}
                          {!r.is_above_upper_limit && !r.is_below_lower_limit && <Badge variant="success" size="sm">NORMAL</Badge>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};
