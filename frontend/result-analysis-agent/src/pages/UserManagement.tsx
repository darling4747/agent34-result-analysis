import { useState, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Key,
  Copy,
  Check,
  ShieldAlert,
  Search,
  CheckCircle2,
  XCircle,
  X,
  Loader2,
  RefreshCw,
  Building2,
  UserCheck,
  ShieldCheck,
} from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import {
  listUsers,
  createUser,
  deactivateUser,
  activateUser,
  forcePasswordReset,
  adminResetMfa,
  type CreateUserRequest,
} from '@/api/authApi';
import { DEPARTMENTS } from '@/utils/constants';

interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  department: string | null;
  is_active: boolean;
  must_change_password: boolean;
  mfa_enabled?: boolean;
  created_at: string;
}

const ROLES = [
  { name: 'DEAN', label: 'Dean of Academic Affairs', desc: 'University-wide academic oversight', color: 'bg-purple-100 text-purple-800 border-purple-200' },
  { name: 'HOD', label: 'Head of Department', desc: 'Departmental results & faculty management', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  { name: 'FACULTY', label: 'Faculty Member', desc: 'Course results & section analysis', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  { name: 'IQAC', label: 'Internal Quality Assurance', desc: 'Quality audit & compliance reporting', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  { name: 'MANAGEMENT', label: 'Executive Management', desc: 'Strategic analytics & executive summaries', color: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  { name: 'AUDITOR', label: 'Academic Auditor', desc: 'Read-only audit & data verification', color: 'bg-slate-100 text-slate-800 border-slate-200' },
  { name: 'PLATFORM_ADMIN', label: 'Platform Administrator', desc: 'Full system administration & user access', color: 'bg-rose-100 text-rose-800 border-rose-200' },
];

export default function UserManagement() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');

  // Create User Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<CreateUserRequest>({
    email: '',
    full_name: '',
    role: 'FACULTY',
    department: DEPARTMENTS[0],
  });
  const [submitting, setSubmitting] = useState(false);

  // Temporary Password Modal state (shows generated password)
  const [tempPasswordModal, setTempPasswordModal] = useState<{
    email: string;
    fullName: string;
    role: string;
    tempPassword: string;
    title: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await listUsers();
      if (resp.success && Array.isArray(resp.data)) {
        setUsers(resp.data);
      } else {
        setError('Failed to fetch user list');
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Error loading users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.email || !createForm.full_name) return;
    setSubmitting(true);
    try {
      const resp = await createUser(createForm);
      if (resp.success && resp.data) {
        setShowCreateModal(false);
        const createdData = resp.data;
        // Show temp password modal for admin to copy
        setTempPasswordModal({
          email: createdData.email,
          fullName: createdData.full_name,
          role: createdData.role,
          tempPassword: createdData.temporary_password,
          title: 'Account Created Successfully!',
        });
        setCreateForm({ email: '', full_name: '', role: 'FACULTY', department: DEPARTMENTS[0] });
        fetchUsers();
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || err.message || 'Failed to create user');
    } finally {
      setSubmitting(false);
    }
  };

  const handleForceReset = async (user: AdminUser) => {
    if (!confirm(`Generate a new temporary password for ${user.full_name} (${user.email})?`)) return;
    try {
      const resp = await forcePasswordReset(user.id);
      if (resp.success && resp.data) {
        setTempPasswordModal({
          email: resp.data.email,
          fullName: user.full_name,
          role: user.role,
          tempPassword: resp.data.temporary_password,
          title: 'Password Reset Generated!',
        });
        fetchUsers();
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || err.message || 'Failed to reset password');
    }
  };

  const handleToggleActive = async (user: AdminUser) => {
    try {
      if (user.is_active) {
        await deactivateUser(user.id);
      } else {
        await activateUser(user.id);
      }
      fetchUsers();
    } catch (err: any) {
      alert(err?.response?.data?.detail || err.message || 'Action failed');
    }
  };

  const handleResetMfa = async (user: AdminUser) => {
    if (!confirm(`Reset Multi-Factor Authentication (MFA) for ${user.full_name} (${user.email})? They will be able to set up a new authenticator device on their next login.`)) return;
    try {
      const resp = await adminResetMfa(user.id);
      if (resp.success) {
        alert(`MFA state successfully reset for ${user.email}.`);
        fetchUsers();
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || err.message || 'Failed to reset MFA');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase());
    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin User Management & Credentials Portal"
        description="Create institutional accounts, assign RBAC roles, and generate temporary login passwords."
        actions={
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors shadow-sm"
          >
            <UserPlus size={18} />
            Create User & Generate Login
          </button>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Accounts</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{users.length}</div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Users size={24} />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Users</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              {users.filter((u) => u.is_active).length}
            </div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <UserCheck size={24} />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Roles Configured</div>
            <div className="text-2xl font-bold text-purple-600 mt-1">{ROLES.length}</div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
            <Building2 size={24} />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Pending Password Setup</div>
            <div className="text-2xl font-bold text-amber-600 mt-1">
              {users.filter((u) => u.must_change_password).length}
            </div>
          </div>
          <div className="w-12 h-12 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
            <Key size={24} />
          </div>
        </div>
      </div>

      {/* Available Roles Legend Card */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-xl p-6 text-white shadow-md">
        <h3 className="text-base font-semibold mb-2 flex items-center gap-2">
          <ShieldAlert size={18} className="text-blue-400" />
          Supported Institutional Roles & Access Levels
        </h3>
        <p className="text-xs text-slate-300 mb-4">
          Admin can generate login credentials for all remaining roles in the university hierarchy:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {ROLES.map((r) => (
            <div key={r.name} className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${r.color}`}>
                  {r.name}
                </span>
              </div>
              <div className="text-xs font-medium text-slate-200 mt-1.5">{r.label}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">{r.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter and User List Section */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-72">
              <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search by name or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="ALL">All Roles</option>
              {ROLES.map((r) => (
                <option key={r.name} value={r.name}>
                  {r.name} - {r.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={fetchUsers}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh List
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-700 text-sm border-b border-red-100 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={fetchUsers} className="underline font-medium">
              Retry
            </button>
          </div>
        )}

        {/* User Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">User & Email</th>
                <th className="px-6 py-3">Role</th>
                <th className="px-6 py-3">Department</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Setup State</th>
                <th className="px-6 py-3">MFA (TOTP)</th>
                <th className="px-6 py-3 text-right">Actions / Access</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-gray-500">
                    <Loader2 size={24} className="animate-spin inline-block text-blue-600 mb-2" />
                    <div>Loading accounts...</div>
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-gray-400">
                    No user accounts match the search criteria.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => {
                  const roleObj = ROLES.find((r) => r.name === user.role);
                  return (
                    <tr key={user.id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-gray-900">{user.full_name}</div>
                        <div className="text-xs text-gray-500 font-mono">{user.email}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center text-xs font-bold px-2.5 py-1 rounded-md border ${
                            roleObj?.color || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs font-medium text-gray-600">
                        {user.department || 'All Departments'}
                      </td>
                      <td className="px-6 py-4">
                        {user.is_active ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                            <CheckCircle2 size={12} /> Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-700 bg-red-50 px-2 py-0.5 rounded-full">
                            <XCircle size={12} /> Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-xs">
                        {user.must_change_password ? (
                          <span className="text-amber-600 font-semibold bg-amber-50 px-2 py-0.5 rounded">
                            Pending Password Reset
                          </span>
                        ) : (
                          <span className="text-emerald-600 font-semibold">Configured</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-xs">
                        {user.mfa_enabled ? (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-200">
                            <ShieldCheck size={12} /> Active
                          </span>
                        ) : (
                          <span className="text-gray-400 font-medium text-xs">
                            Not Active
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        {user.mfa_enabled && (
                          <button
                            onClick={() => handleResetMfa(user)}
                            title="Reset Multi-Factor Authentication state"
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 text-xs font-semibold rounded-lg transition-colors"
                          >
                            <ShieldCheck size={13} />
                            Reset MFA
                          </button>
                        )}

                        <button
                          onClick={() => handleForceReset(user)}
                          title="Generate New Temporary Login Password"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 text-xs font-semibold rounded-lg transition-colors"
                        >
                          <Key size={14} />
                          Reset Password
                        </button>

                        <button
                          onClick={() => handleToggleActive(user)}
                          className={`px-2.5 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                            user.is_active
                              ? 'bg-red-50 text-red-600 border-red-200 hover:bg-red-100'
                              : 'bg-emerald-50 text-emerald-600 border-emerald-200 hover:bg-emerald-100'
                          }`}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE USER MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
                  <UserPlus size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Create Role Account &amp; Password</h3>
                  <p className="text-xs text-gray-500">Generate login credentials for remaining institutional roles</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600 rounded-lg p-1"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Ramesh Kumar"
                  value={createForm.full_name}
                  onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Institutional Email Address *
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. ramesh.hod@university.edu"
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Assign Institutional Role *
                </label>
                <select
                  value={createForm.role}
                  onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white font-medium"
                >
                  {ROLES.map((r) => (
                    <option key={r.name} value={r.name}>
                      {r.name} — {r.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Department
                </label>
                <select
                  value={createForm.department || ''}
                  onChange={(e) => setCreateForm({ ...createForm, department: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                >
                  <option value="">All Departments (University Level)</option>
                  {DEPARTMENTS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 border-t border-gray-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex items-center gap-2 px-5 py-2 text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 rounded-lg shadow-sm"
                >
                  {submitting && <Loader2 size={16} className="animate-spin" />}
                  Create &amp; Generate Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* GENERATED TEMPORARY PASSWORD DISPLAY MODAL */}
      {tempPasswordModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100 text-center animate-in fade-in zoom-in duration-200">
            <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3">
              <CheckCircle2 size={32} />
            </div>

            <h3 className="text-xl font-bold text-gray-900">{tempPasswordModal.title}</h3>
            <p className="text-xs text-gray-500 mt-1">
              Provide these temporary credentials to the account holder.
            </p>

            <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl text-left space-y-2">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Full Name
                </span>
                <span className="text-sm font-bold text-slate-800">{tempPasswordModal.fullName}</span>
              </div>

              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Login Email
                </span>
                <span className="text-sm font-mono text-slate-800">{tempPasswordModal.email}</span>
              </div>

              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Assigned Role
                </span>
                <span className="text-xs font-bold px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                  {tempPasswordModal.role}
                </span>
              </div>

              <div className="pt-2 border-t border-slate-200">
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Generated Temporary Password:
                </span>
                <div className="flex items-center justify-between bg-white border-2 border-blue-400 rounded-lg p-2.5 font-mono text-base font-extrabold text-blue-700 shadow-inner">
                  <span className="select-all">{tempPasswordModal.tempPassword}</span>
                  <button
                    onClick={() => copyToClipboard(tempPasswordModal.tempPassword)}
                    className="inline-flex items-center gap-1 text-xs bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 transition-colors font-sans font-medium"
                  >
                    {copied ? (
                      <>
                        <Check size={14} /> Copied!
                      </>
                    ) : (
                      <>
                        <Copy size={14} /> Copy
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-2 mt-4 text-left font-medium">
              Notice: The user will be required to create a new password immediately upon first login.
            </p>

            <button
              onClick={() => setTempPasswordModal(null)}
              className="mt-5 w-full py-2.5 bg-slate-900 text-white font-semibold text-sm rounded-xl hover:bg-slate-800 transition-colors"
            >
              Done &amp; Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
