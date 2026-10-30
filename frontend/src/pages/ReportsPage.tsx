import React, { useEffect, useState } from 'react';
import { Download, FileSpreadsheet, FileText, Plus, ShieldCheck } from 'lucide-react';
import api from '../lib/axios';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New Report Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reportTitle, setReportTitle] = useState('');
  const [reportType, setReportType] = useState('results');
  const [reportFormat, setReportFormat] = useState('pdf');
  const [submitting, setSubmitting] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await api.get('/reports');
      setReports(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleCreateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/reports', {
        title: reportTitle.trim() || `Laboratory ${reportType.toUpperCase()} Report`,
        report_type: reportType,
        format: reportFormat,
      });
      setIsModalOpen(false);
      setReportTitle('');
      fetchReports();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to generate report.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownload = async (reportId: string, filename: string) => {
    try {
      const res = await api.get(`/reports/${reportId}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      alert('Failed to download report.');
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Reporting & Data Exports</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Compiled PDF summaries, CSV exports, and formula-injection sanitized Excel sheets.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" /> Generate Report
        </Button>
      </div>

      <div className="flex items-center gap-2 p-3 text-xs bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-lg text-slate-600 dark:text-slate-300">
        <ShieldCheck className="w-4 h-4 text-teal-600 flex-shrink-0" />
        <span>
          <strong>Security Control:</strong> All CSV and Excel exports are sanitized against spreadsheet formula injection (CWE-1236) by neutralizing active command symbols (=, +, -, @, \t, \r).
        </span>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Report Title</th>
                <th className="py-2.5 px-3 font-semibold">Scope / Type</th>
                <th className="py-2.5 px-3 font-semibold">Format</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 font-semibold">Generated Timestamp</th>
                <th className="py-2.5 px-3 font-semibold text-right">Download</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400">Loading reports catalog...</td>
                </tr>
              ) : reports.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400">No reports generated yet.</td>
                </tr>
              ) : (
                reports.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-semibold text-slate-900 dark:text-slate-100">{r.title}</td>
                    <td className="py-2.5 px-3 capitalize">{r.report_type}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-mono font-bold uppercase text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">
                        {r.format}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge variant="success" size="sm">{r.status}</Badge>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {r.generated_at ? new Date(r.generated_at).toLocaleString() : '-'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleDownload(r.id, `${r.title}.${r.format === 'excel' ? 'xlsx' : r.format}`)}
                        className="gap-1.5"
                      >
                        <Download className="w-3.5 h-3.5" /> Download
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Generate Report Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Generate Compliant Report">
        <form onSubmit={handleCreateReport} className="space-y-4 text-xs">
          <Input
            label="Report Title (Optional)"
            placeholder="e.g. Weekly Clinical Specimen Summary"
            value={reportTitle}
            onChange={(e) => setReportTitle(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Report Type
              </label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="results">Laboratory Test Results</option>
                <option value="samples">Specimen Tracking Records</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Export Format
              </label>
              <select
                value={reportFormat}
                onChange={(e) => setReportFormat(e.target.value)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium"
              >
                <option value="pdf">PDF Document (Formatted Print)</option>
                <option value="csv">CSV (Sanitized Flat Table)</option>
                <option value="excel">Excel (.xlsx Workbook)</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submitting}>
              Compile & Export
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
