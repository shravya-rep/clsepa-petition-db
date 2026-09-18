import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import client from "../api/client";
import type { Decision } from "../api/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function formatType(t: string | null): string {
  const labels: Record<string, string> = {
    HODecision: "Hearing Officer Decision",
    AppealDecision: "Appeal Decision",
    HOCPDecision: "HOCP Decision",
    RemandAppealDecision: "Remand Appeal Decision",
  };
  return t ? labels[t] || t : "Decision";
}

export default function DecisionPage() {
  const { id } = useParams<{ id: string }>();
  const [decision, setDecision] = useState<Decision | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client
      .get(`/api/decisions/${id}`)
      .then((r) => setDecision(r.data))
      .catch(() => setDecision(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-center py-12 text-gray-500">Loading...</p>;
  if (!decision) return <p className="text-center py-12 text-red-500">Decision not found.</p>;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <Link to="/" className="text-blue-700 hover:underline text-sm mb-6 inline-block">
        &larr; Back to search
      </Link>

      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          {decision.address || "Address not available"}
          {decision.unit && `, Unit ${decision.unit}`}
        </h1>
        <p className="text-gray-500 mb-6">
          {decision.city}
          {decision.case_number && <> &middot; Case {decision.case_number}</>}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Detail label="Decision Type" value={formatType(decision.decision_type)} />
          <Detail label="Hearing Officer" value={decision.hearing_officer} />
          <Detail label="Hearing Date" value={decision.hearing_date ? new Date(decision.hearing_date).toLocaleDateString() : null} />
          <Detail label="Decision Date" value={decision.decision_date ? new Date(decision.decision_date).toLocaleDateString() : null} />
          <Detail label="Petitioner" value={decision.petitioner_name} />
          <Detail label="Respondent" value={decision.respondent_name} />
          <Detail label="Amount Awarded" value={decision.amount_awarded != null ? `$${decision.amount_awarded.toLocaleString()}` : null} />
        </div>

        {decision.outcome_summary && (
          <div className="mb-6">
            <h2 className="text-sm font-medium text-gray-500 mb-1">Outcome Summary</h2>
            <p className="text-gray-800">{decision.outcome_summary}</p>
          </div>
        )}

        {decision.keywords.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-medium text-gray-500 mb-2">Issues / Categories</h2>
            <div className="flex flex-wrap gap-2">
              {decision.keywords.map((k) => (
                <span key={k.id} className="bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded-full">
                  {k.name}
                </span>
              ))}
            </div>
          </div>
        )}

        <a
          href={`${API_BASE}/api/pdfs/${decision.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-blue-700 text-white px-6 py-2.5 rounded-md hover:bg-blue-800 text-sm font-medium"
        >
          View Full Decision (PDF)
        </a>
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-gray-900">{value}</p>
    </div>
  );
}
