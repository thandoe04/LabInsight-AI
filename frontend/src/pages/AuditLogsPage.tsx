import React, { useEffect, useState } from 'react';
import { Eye, Filter, Lock, Search, ShieldAlert } from 'lucide-react';
import api from '../lib/axios';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState<any | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/audit-logs', {
        params: {
          action: actionFilter || undefined,
          outcome: outcomeFilter || undefined,
          page_size: 50,
        },
      });
      setLogs(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, outcomeFilter]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">System Security Audit Trail</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Tamper-evident, append-only operational log recording authentication events and record modifications.
        </p>
      </div>

      <div className="flex items-center gap-2 p-3 text-xs bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-lg text-slate-600 dark:text-slate-300">
        <Lock className="w-4 h-4 text-teal-600 flex-shrink-0" />
        <span>
          <strong>Append-Only Integrity:</strong> Audit log entries are immutable once written. Sensitive authentication tokens, passwords, and PII are redacted prior to persistence.
        </span>
      </div>

      <Card>
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <input
            type="text"
            placeholder="Filter by action (e.g. login, verify)..."
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 flex-1 max-w-xs"
          />

          <select
            value={outcomeFilter}
            onChange={(e) => setOutcomeFilter(e.target.value)}
            className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Outcomes</option>
            <option value="success">Success</option>
            <option value="failure">Failure / Denied</option>
          </select>
        </div>

        {/* Audit Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Timestamp (UTC)</th>
                <th className="py-2.5 px-3 font-semibold">Actor</th>
                <th className="py-2.5 px-3 font-semibold">Action</th>
                <th className="py-2.5 px-3 font-semibold">Outcome</th>
                <th className="py-2.5 px-3 font-semibold">Entity</th>
                <th className="py-2.5 px-3 font-semibold">Source IP</th>
                <th className="py-2.5 px-3 font-semibold text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">Loading audit trail records...</td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">No matching audit events recorded.</td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-mono text-slate-500">
                      {new Date(log.occurred_at).toISOString().replace('T', ' ').slice(0, 19)}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-800 dark:text-slate-200">
                      {log.actor_username || 'Anonymous'}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-teal-600 dark:text-teal-400 font-medium">
                      {log.action}
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge variant={log.outcome === 'success' ? 'success' : 'danger'} size="sm">
                        {log.outcome}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 capitalize">{log.entity_type || '-'}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-400">{log.ip_address || '127.0.0.1'}</td>
                    <td className="py-2.5 px-3 text-right">
                      {log.metadata_ && (
                        <Button variant="outline" size="sm" onClick={() => setSelectedLog(log)}>
                          <Eye className="w-3.5 h-3.5" />
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

      {/* Metadata Detail Modal */}
      <Modal
        isOpen={Boolean(selectedLog)}
        onClose={() => setSelectedLog(null)}
        title={`Audit Event Details — ${selectedLog?.action}`}
      >
        <div className="space-y-3 text-xs">
          <div className="grid grid-cols-2 gap-2 text-slate-600 dark:text-slate-300">
            <div>
              <span className="font-semibold block text-slate-800 dark:text-slate-200">Actor:</span>
              <span>{selectedLog?.actor_username || 'System / Unauthenticated'}</span>
            </div>
            <div>
              <span className="font-semibold block text-slate-800 dark:text-slate-200">Request ID:</span>
              <span className="font-mono text-[10px]">{selectedLog?.request_id || 'N/A'}</span>
            </div>
          </div>

          <div>
            <span className="font-semibold block text-slate-800 dark:text-slate-200 mb-1">Payload Metadata:</span>
            <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-[11px] overflow-x-auto font-mono">
              {JSON.stringify(selectedLog?.metadata_, null, 2)}
            </pre>
          </div>
        </div>
      </Modal>
    </div>
  );
};
