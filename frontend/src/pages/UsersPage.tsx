import React, { useEffect, useState } from 'react';
import { Plus, Shield, UserCheck, Users } from 'lucide-react';
import api from '../lib/axios';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';

export const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New User Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRoleId, setSelectedRoleId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [uRes, rRes] = await Promise.all([
        api.get('/users'),
        api.get('/users/roles'),
      ]);
      setUsers(uRes.data);
      setRoles(rRes.data);
      if (rRes.data.length > 0 && !selectedRoleId) {
        setSelectedRoleId(rRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/users', {
        email,
        username,
        full_name: fullName,
        password,
        role_id: selectedRoleId,
      });
      setIsModalOpen(false);
      setEmail('');
      setUsername('');
      setFullName('');
      setPassword('');
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create user account.');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleStatus = async (user: any) => {
    try {
      await api.patch(`/users/${user.id}`, {
        is_active: !user.is_active,
      });
      fetchData();
    } catch (err: any) {
      alert('Failed to update account status.');
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">User Access & Role Management</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Role-based access control (RBAC), fine-grained permissions, and credential security.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" /> Provision User Account
        </Button>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">User</th>
                <th className="py-2.5 px-3 font-semibold">Username</th>
                <th className="py-2.5 px-3 font-semibold">Assigned Role</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 font-semibold">Created Date</th>
                <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400">Loading user registry...</td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-slate-900 dark:text-slate-100 block">{u.full_name}</span>
                      <span className="text-[11px] text-slate-400">{u.email}</span>
                    </td>
                    <td className="py-2.5 px-3 font-mono font-medium">{u.username}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold capitalize text-teal-600 dark:text-teal-400">
                        {u.role_display || u.role_name || 'No Role'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge variant={u.is_active ? 'success' : 'danger'} size="sm">
                        {u.is_active ? 'Active' : 'Disabled'}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="py-2.5 px-3 text-right">
                      <Button
                        variant={u.is_active ? 'secondary' : 'primary'}
                        size="sm"
                        onClick={() => toggleStatus(u)}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Provision User Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Provision Laboratory User Account">
        <form onSubmit={handleCreate} className="space-y-4 text-xs">
          <Input
            label="Full Name"
            required
            placeholder="e.g. Dr. Jane Smith"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Email Address"
              type="email"
              required
              placeholder="jane@labinsight.dev"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Input
              label="Username"
              required
              placeholder="jsmith"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Password (min 12 characters)"
              type="password"
              required
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              helperText="Hashed with Argon2id memory-hard algorithm"
            />
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Assign System Role
              </label>
              <select
                value={selectedRoleId}
                onChange={(e) => setSelectedRoleId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium"
              >
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.display_name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submitting}>
              Provision Account
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
