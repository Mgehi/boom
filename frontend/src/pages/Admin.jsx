import { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Shield, Plus, Trash2, Users, Mail, Crown } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Admin = () => {
  const [emails, setEmails] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newNote, setNewNote] = useState("");

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      const [emailsRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/allowed-emails`, { withCredentials: true }),
        axios.get(`${API}/admin/users`, { withCredentials: true }),
      ]);
      setEmails(emailsRes.data);
      setUsers(usersRes.data);
    } catch (e) {
      if (e.response?.status === 403) {
        toast.error("Admin access required");
      } else {
        toast.error("Failed to load admin data");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newEmail.includes("@")) {
      toast.error("Please enter a valid email");
      return;
    }
    setAdding(true);
    try {
      await axios.post(`${API}/admin/allowed-emails`, {
        email: newEmail,
        note: newNote,
      }, { withCredentials: true });
      toast.success(`${newEmail} added to whitelist`);
      setNewEmail("");
      setNewNote("");
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to add email");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id, email) => {
    if (!window.confirm(`Remove ${email} from whitelist? They will not be able to sign up again until you re-add them.`)) {
      return;
    }
    try {
      await axios.delete(`${API}/admin/allowed-emails/${id}`, { withCredentials: true });
      toast.success(`${email} removed from whitelist`);
      fetchAll();
    } catch (err) {
      toast.error("Failed to remove email");
    }
  };

  const handleRevokeUser = async (userId, email) => {
    if (!window.confirm(`Revoke access for ${email}? They will be signed out immediately. To fully block them, also remove their email from the whitelist.`)) {
      return;
    }
    try {
      const response = await axios.delete(`${API}/admin/users/${userId}`, { withCredentials: true });
      toast.success(response.data?.message || `${email} access revoked`);
      fetchAll();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to revoke user");
    }
  };

  if (loading) {
    return (
      <div className="p-4 lg:p-8" data-testid="admin-loading">
        <div className="text-zinc-500">Loading admin panel...</div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8" data-testid="admin-page">
      <div className="mb-6 lg:mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-7 h-7 text-zinc-900" />
          <h1 className="text-2xl lg:text-4xl font-bold tracking-tight" data-testid="admin-title">Admin Panel</h1>
        </div>
        <p className="text-sm lg:text-base text-zinc-500">Manage client access to your dashboard</p>
      </div>

      <div className="max-w-5xl space-y-6">
        {/* Add Email Form */}
        <form onSubmit={handleAdd} className="border border-zinc-200 rounded-sm bg-white p-4 lg:p-6">
          <h2 className="text-lg font-bold tracking-tight mb-1">Add Client to Whitelist</h2>
          <p className="text-sm text-zinc-500 mb-4">Add a client's Google email to allow them to sign in</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-1">
              <Label htmlFor="email" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Email *</Label>
              <Input
                id="email"
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="client@business.com"
                required
                data-testid="new-email-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div className="md:col-span-1">
              <Label htmlFor="note" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Note (Optional)</Label>
              <Input
                id="note"
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="e.g., ABC Pvt Ltd"
                data-testid="new-note-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div className="md:col-span-1 flex items-end">
              <Button
                type="submit"
                disabled={adding}
                data-testid="add-email-btn"
                className="bg-red-600 text-white hover:bg-red-700 rounded-sm w-full md:w-auto"
              >
                <Plus className="w-4 h-4 mr-2" />
                {adding ? "Adding..." : "Add to Whitelist"}
              </Button>
            </div>
          </div>
        </form>

        {/* Whitelist */}
        <div className="border border-zinc-200 rounded-sm bg-white">
          <div className="p-4 lg:p-6 border-b border-zinc-200 flex items-center gap-2">
            <Mail className="w-5 h-5 text-zinc-700" />
            <h2 className="text-lg font-bold tracking-tight">Whitelisted Emails</h2>
            <span className="ml-2 px-2 py-1 bg-zinc-100 text-xs font-medium text-zinc-600 rounded-sm">
              {emails.length}
            </span>
          </div>
          {emails.length === 0 ? (
            <div className="p-8 text-center" data-testid="empty-whitelist">
              <Mail className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
              <p className="text-sm text-zinc-500">No clients whitelisted yet</p>
              <p className="text-xs text-zinc-400 mt-1">Add a client email above to give them access</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-[#FAFAFA]">
                  <tr className="border-b border-zinc-200">
                    <th className="px-3 lg:px-6 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Email</th>
                    <th className="hidden sm:table-cell px-3 lg:px-6 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Note</th>
                    <th className="hidden md:table-cell px-3 lg:px-6 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Added</th>
                    <th className="px-3 lg:px-6 py-3 text-right font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {emails.map((entry) => (
                    <tr key={entry.id} className="border-b border-zinc-200 hover:bg-zinc-50" data-testid={`whitelist-row-${entry.email}`}>
                      <td className="px-3 lg:px-6 py-3 font-medium text-zinc-900 text-sm">{entry.email}</td>
                      <td className="hidden sm:table-cell px-3 lg:px-6 py-3 text-zinc-600 text-sm">{entry.note || "—"}</td>
                      <td className="hidden md:table-cell px-3 lg:px-6 py-3 text-zinc-500 text-xs">
                        {new Date(entry.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-3 lg:px-6 py-3 text-right">
                        <button
                          onClick={() => handleRemove(entry.id, entry.email)}
                          data-testid={`remove-email-${entry.email}`}
                          className="inline-flex items-center gap-1 text-xs text-red-600 hover:text-red-700 hover:underline"
                        >
                          <Trash2 className="w-3 h-3" />
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Registered Users */}
        <div className="border border-zinc-200 rounded-sm bg-white">
          <div className="p-4 lg:p-6 border-b border-zinc-200 flex items-center gap-2">
            <Users className="w-5 h-5 text-zinc-700" />
            <h2 className="text-lg font-bold tracking-tight">Active Users</h2>
            <span className="ml-2 px-2 py-1 bg-zinc-100 text-xs font-medium text-zinc-600 rounded-sm">
              {users.length}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#FAFAFA]">
                <tr className="border-b border-zinc-200">
                  <th className="px-3 lg:px-6 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">User</th>
                  <th className="hidden md:table-cell px-3 lg:px-6 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Email</th>
                  <th className="px-3 lg:px-6 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Role</th>
                  <th className="hidden sm:table-cell px-3 lg:px-6 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Shipments</th>
                  <th className="px-3 lg:px-6 py-3 text-right font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.user_id} className="border-b border-zinc-200 hover:bg-zinc-50" data-testid={`user-row-${user.email}`}>
                    <td className="px-3 lg:px-6 py-3">
                      <div className="flex items-center gap-3">
                        {user.picture ? (
                          <img src={user.picture} alt="" className="w-8 h-8 rounded-full border border-zinc-200" />
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-zinc-900 text-white flex items-center justify-center text-xs font-bold">
                            {(user.name || user.email).charAt(0).toUpperCase()}
                          </div>
                        )}
                        <span className="text-zinc-900 font-medium text-sm">{user.name || "—"}</span>
                      </div>
                    </td>
                    <td className="hidden md:table-cell px-3 lg:px-6 py-3 text-zinc-600 text-sm">{user.email}</td>
                    <td className="px-3 lg:px-6 py-3">
                      {user.is_admin ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-zinc-900 text-white text-xs font-medium rounded-sm">
                          <Crown className="w-3 h-3" />
                          Admin
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 bg-white border border-zinc-200 text-zinc-700 text-xs font-medium rounded-sm">
                          Client
                        </span>
                      )}
                    </td>
                    <td className="hidden sm:table-cell px-3 lg:px-6 py-3 mono text-zinc-700">{user.shipment_count}</td>
                    <td className="px-3 lg:px-6 py-3 text-right">
                      {user.is_admin ? (
                        <span className="text-xs text-zinc-400">Protected</span>
                      ) : (
                        <button
                          onClick={() => handleRevokeUser(user.user_id, user.email)}
                          data-testid={`revoke-user-${user.email}`}
                          className="inline-flex items-center gap-1 text-xs text-red-600 hover:text-red-700 hover:underline"
                        >
                          <Trash2 className="w-3 h-3" />
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Info Banner */}
        <div className="bg-zinc-50 border-l-4 border-zinc-900 p-4 rounded-sm text-sm text-zinc-700">
          <strong className="text-zinc-900">How it works:</strong>
          <ul className="mt-2 space-y-1 text-xs">
            <li>• Only emails on the whitelist can sign in via Google</li>
            <li>• Add a client's email <strong>before</strong> they try to sign in</li>
            <li>• "Revoke" signs the user out immediately, but they can sign in again unless you also remove their email from the whitelist</li>
            <li>• You (admin) cannot be revoked from this panel — only another admin can do that</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Admin;
