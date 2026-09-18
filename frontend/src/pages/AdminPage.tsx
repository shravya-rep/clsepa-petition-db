import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { Decision, Keyword } from "../api/types";

export default function AdminPage() {
  const { isAdmin, logout } = useAuth();
  const navigate = useNavigate();
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [tab, setTab] = useState<"upload" | "manage" | "keywords">("upload");

  // Upload form state
  const [pdf, setPdf] = useState<File | null>(null);
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [meta, setMeta] = useState({
    city: "East Palo Alto",
    case_number: "",
    address: "",
    unit: "",
    petitioner_name: "",
    respondent_name: "",
    hearing_date: "",
    decision_date: "",
    decision_type: "HODecision",
    hearing_officer: "",
    outcome_summary: "",
    amount_awarded: "",
  });
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [message, setMessage] = useState("");
  const [extractInfo, setExtractInfo] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Keyword form
  const [newKeyword, setNewKeyword] = useState("");

  useEffect(() => {
    if (!isAdmin) {
      navigate("/login");
      return;
    }
    loadData();
  }, [isAdmin]);

  const loadData = () => {
    client.get("/api/keywords/").then((r) => setKeywords(r.data));
    client.get("/api/decisions/").then((r) => setDecisions(r.data));
  };

  const handleFileSelect = async (file: File) => {
    setPdf(file);
    setMessage("");
    setExtractInfo("");
    setExtracting(true);

    // Auto-extract metadata from the PDF
    const formData = new FormData();
    formData.append("pdf", file);

    try {
      const res = await client.post("/api/extract/", formData);
      const d = res.data;
      setMeta({
        city: d.city || "East Palo Alto",
        case_number: d.case_number || "",
        address: d.address || "",
        unit: d.unit || "",
        petitioner_name: d.petitioner_name || "",
        respondent_name: d.respondent_name || "",
        hearing_date: d.hearing_date || "",
        decision_date: d.decision_date || "",
        decision_type: d.decision_type || "HODecision",
        hearing_officer: d.hearing_officer || "",
        outcome_summary: "",
        amount_awarded: "",
      });

      if (d.confidence === "high") {
        setExtractInfo("Fields auto-filled from PDF. Please review before uploading.");
      } else if (d.confidence === "medium") {
        setExtractInfo("Some fields auto-filled. Please review and complete missing fields.");
      } else {
        setExtractInfo("Could not extract fields from this PDF. Please fill in manually.");
      }

      if (d.warnings && d.warnings.length > 0) {
        setExtractInfo((prev) => prev + " Note: " + d.warnings.join("; "));
      }
    } catch {
      setExtractInfo("Could not auto-extract fields. Please fill in manually.");
    }

    setExtracting(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === "application/pdf") {
      handleFileSelect(file);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pdf) return;
    setUploading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("pdf", pdf);

    const data: Record<string, unknown> = { ...meta, keyword_ids: selectedKeywords };
    if (data.amount_awarded === "") delete data.amount_awarded;
    else data.amount_awarded = parseFloat(data.amount_awarded as string);
    if (data.hearing_date === "") delete data.hearing_date;
    if (data.decision_date === "") delete data.decision_date;

    formData.append("data", JSON.stringify(data));

    try {
      await client.post("/api/decisions/", formData);
      setMessage("Decision uploaded successfully!");
      setPdf(null);
      setSelectedKeywords([]);
      setExtractInfo("");
      setMeta({
        city: "East Palo Alto", case_number: "", address: "", unit: "",
        petitioner_name: "", respondent_name: "", hearing_date: "",
        decision_date: "", decision_type: "HODecision", hearing_officer: "",
        outcome_summary: "", amount_awarded: "",
      });
      if (fileInputRef.current) fileInputRef.current.value = "";
      loadData();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (msg && msg.includes("already exists")) {
        setMessage("This decision has already been uploaded. Please choose a different file.");
      } else {
        setMessage("Upload failed. Please try again.");
      }
    }
    setUploading(false);
  };

  const handleAddKeyword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyword.trim()) return;
    try {
      await client.post("/api/keywords/", { name: newKeyword.trim() });
      setNewKeyword("");
      loadData();
    } catch {
      alert("Could not add keyword. It may already exist.");
    }
  };

  const handleDeleteDecision = async (id: string) => {
    if (!confirm("Delete this decision? This cannot be undone.")) return;
    await client.delete(`/api/decisions/${id}`);
    loadData();
  };

  const toggleKeyword = (id: string) => {
    setSelectedKeywords((prev) =>
      prev.includes(id) ? prev.filter((k) => k !== id) : [...prev, id]
    );
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <button onClick={logout} className="text-sm text-red-600 hover:underline">
          Sign Out
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {(["upload", "manage", "keywords"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              tab === t ? "bg-white shadow text-blue-700" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {t === "upload" ? "Upload Decision" : t === "manage" ? "Manage Decisions" : "Keywords"}
          </button>
        ))}
      </div>

      {/* Upload Tab */}
      {tab === "upload" && (
        <form onSubmit={handleUpload} className="bg-white rounded-lg shadow p-6 space-y-5">
          {message && (
            <p className={`text-sm p-3 rounded ${message.includes("success") ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
              {message}
            </p>
          )}

          {/* Step 1: File Upload Area */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Step 1: Select Decision PDF
            </label>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                dragOver
                  ? "border-blue-500 bg-blue-50"
                  : pdf
                  ? "border-green-400 bg-green-50"
                  : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
              }`}
            >
              {extracting ? (
                <div>
                  <p className="text-blue-700 font-medium">Extracting data from PDF...</p>
                  <p className="text-sm text-gray-500 mt-1">Auto-filling fields below</p>
                </div>
              ) : pdf ? (
                <div>
                  <p className="text-green-700 font-medium">{pdf.name}</p>
                  <p className="text-sm text-gray-500 mt-1">Click or drag to replace</p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-600 font-medium">Click to browse or drag and drop a PDF here</p>
                  <p className="text-sm text-gray-400 mt-1">The form below will auto-fill from the PDF</p>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileSelect(file);
                }}
              />
            </div>
          </div>

          {extractInfo && (
            <p className={`text-sm p-3 rounded ${
              extractInfo.includes("auto-filled") ? "bg-blue-50 text-blue-700" : "bg-amber-50 text-amber-700"
            }`}>
              {extractInfo}
            </p>
          )}

          {/* Step 2: Review/Edit Fields */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Step 2: Review and complete the details
            </label>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
                <select
                  value={meta.city}
                  onChange={(e) => setMeta({ ...meta, city: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option>East Palo Alto</option>
                  <option>Mountain View</option>
                </select>
              </div>
              <Field label="Case Number" value={meta.case_number} onChange={(v) => setMeta({ ...meta, case_number: v })} />
              <Field label="Address" value={meta.address} onChange={(v) => setMeta({ ...meta, address: v })} />
              <Field label="Unit" value={meta.unit} onChange={(v) => setMeta({ ...meta, unit: v })} />
              <Field label="Petitioner Name" value={meta.petitioner_name} onChange={(v) => setMeta({ ...meta, petitioner_name: v })} />
              <Field label="Respondent Name" value={meta.respondent_name} onChange={(v) => setMeta({ ...meta, respondent_name: v })} />
              <Field label="Hearing Date" value={meta.hearing_date} onChange={(v) => setMeta({ ...meta, hearing_date: v })} type="date" />
              <Field label="Decision Date" value={meta.decision_date} onChange={(v) => setMeta({ ...meta, decision_date: v })} type="date" />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Decision Type</label>
                <select
                  value={meta.decision_type}
                  onChange={(e) => setMeta({ ...meta, decision_type: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="HODecision">Hearing Officer Decision</option>
                  <option value="AppealDecision">Appeal Decision</option>
                  <option value="HOCPDecision">HOCP Decision</option>
                  <option value="RemandAppealDecision">Remand Appeal Decision</option>
                </select>
              </div>
              <Field label="Hearing Officer" value={meta.hearing_officer} onChange={(v) => setMeta({ ...meta, hearing_officer: v })} />
              <Field label="Amount Awarded ($)" value={meta.amount_awarded} onChange={(v) => setMeta({ ...meta, amount_awarded: v })} type="number" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Outcome Summary</label>
            <textarea
              value={meta.outcome_summary}
              onChange={(e) => setMeta({ ...meta, outcome_summary: e.target.value })}
              rows={3}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          {/* Step 3: Select Keywords */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Step 3: Select issues / categories that apply
            </label>
            <div className="flex flex-wrap gap-2">
              {keywords.map((k) => (
                <button
                  key={k.id}
                  type="button"
                  onClick={() => toggleKeyword(k.id)}
                  className={`px-3 py-1.5 rounded-full text-sm border ${
                    selectedKeywords.includes(k.id)
                      ? "bg-blue-700 text-white border-blue-700"
                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                  }`}
                >
                  {k.name}
                </button>
              ))}
              {keywords.length === 0 && (
                <p className="text-sm text-gray-400">No keywords yet. Add some in the Keywords tab.</p>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={uploading || !pdf}
            className="bg-blue-700 text-white px-8 py-3 rounded-md hover:bg-blue-800 text-sm font-medium disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Upload Decision"}
          </button>
        </form>
      )}

      {/* Manage Tab */}
      {tab === "manage" && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {decisions.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No decisions uploaded yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Address</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">City</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Case #</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {decisions.map((d) => (
                  <tr key={d.id}>
                    <td className="px-4 py-3">{d.address || "—"}</td>
                    <td className="px-4 py-3">{d.city}</td>
                    <td className="px-4 py-3">{d.case_number || "—"}</td>
                    <td className="px-4 py-3">
                      {d.decision_date ? new Date(d.decision_date).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDeleteDecision(d.id)}
                        className="text-red-600 hover:underline text-xs"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Keywords Tab */}
      {tab === "keywords" && (
        <div className="bg-white rounded-lg shadow p-6">
          <form onSubmit={handleAddKeyword} className="flex gap-3 mb-6">
            <input
              type="text"
              placeholder="New keyword (e.g., Mold, Plumbing)"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="bg-blue-700 text-white px-4 py-2 rounded-md hover:bg-blue-800 text-sm font-medium"
            >
              Add
            </button>
          </form>
          <div className="flex flex-wrap gap-2">
            {keywords.map((k) => (
              <span key={k.id} className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm flex items-center gap-2">
                {k.name}
                <button
                  onClick={async () => {
                    await client.delete(`/api/keywords/${k.id}`);
                    loadData();
                  }}
                  className="text-gray-400 hover:text-red-500"
                >
                  &times;
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label, value, onChange, type = "text",
}: {
  label: string; value: string; onChange: (v: string) => void; type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
      />
    </div>
  );
}
