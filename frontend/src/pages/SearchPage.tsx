import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import type { Decision, Keyword } from "../api/types";

function formatType(t: string | null): string {
  const labels: Record<string, string> = {
    HODecision: "Hearing Officer Decision",
    AppealDecision: "Appeal Decision",
    HOCPDecision: "HOCP Decision",
    RemandAppealDecision: "Remand Appeal Decision",
  };
  return t ? labels[t] || t : "Decision";
}

export default function SearchPage() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [filters, setFilters] = useState({
    keyword: "",
    city: "",
    decision_type: "",
    q: "",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    client.get("/api/keywords/").then((r) => setKeywords(r.data));
    search();
  }, []);

  const search = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filters.keyword) params.append("keyword", filters.keyword);
    if (filters.city) params.append("city", filters.city);
    if (filters.decision_type) params.append("decision_type", filters.decision_type);
    if (filters.q) params.append("q", filters.q);
    try {
      const res = await client.get(`/api/decisions/?${params}`);
      setDecisions(res.data);
    } catch {
      setDecisions([]);
    }
    setLoading(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    search();
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Petition Decision Database
        </h1>
        <p className="text-gray-600">
          Search past tenant petition decisions from East Palo Alto and Mountain
          View. Find what was awarded in cases similar to yours.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg shadow p-6 mb-8 space-y-4"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Issue / Category
            </label>
            <select
              value={filters.keyword}
              onChange={(e) =>
                setFilters({ ...filters, keyword: e.target.value })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">All Issues</option>
              {keywords.map((k) => (
                <option key={k.id} value={k.name}>
                  {k.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              City
            </label>
            <select
              value={filters.city}
              onChange={(e) => setFilters({ ...filters, city: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">All Cities</option>
              <option value="East Palo Alto">East Palo Alto</option>
              <option value="Mountain View">Mountain View</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Decision Type
            </label>
            <select
              value={filters.decision_type}
              onChange={(e) =>
                setFilters({ ...filters, decision_type: e.target.value })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">All Types</option>
              <option value="HODecision">Hearing Officer Decision</option>
              <option value="AppealDecision">Appeal Decision</option>
              <option value="HOCPDecision">HOCP Decision</option>
              <option value="RemandAppealDecision">Remand Appeal</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Case # or address..."
              value={filters.q}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <button
          type="submit"
          className="bg-blue-700 text-white px-6 py-2 rounded-md hover:bg-blue-800 text-sm font-medium"
        >
          Search
        </button>
      </form>

      {loading ? (
        <p className="text-center text-gray-500">Searching...</p>
      ) : decisions.length === 0 ? (
        <p className="text-center text-gray-500">
          No decisions found. Try adjusting your filters.
        </p>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            {decisions.length} decision{decisions.length !== 1 && "s"} found
          </p>
          {decisions.map((d) => (
            <Link
              key={d.id}
              to={`/decision/${d.id}`}
              className="block bg-white rounded-lg shadow p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {d.address || "Address not available"}
                    {d.unit && `, Unit ${d.unit}`}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {d.city}
                    {d.case_number && <> &middot; {d.case_number}</>}
                    {" "}&middot; {formatType(d.decision_type)}
                  </p>
                </div>
                <div className="text-right">
                  {d.decision_date && (
                    <p className="text-sm text-gray-500">
                      {new Date(d.decision_date).toLocaleDateString()}
                    </p>
                  )}
                  {d.amount_awarded != null && (
                    <p className="text-sm font-medium text-green-700">
                      ${d.amount_awarded.toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
              {d.outcome_summary && (
                <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                  {d.outcome_summary}
                </p>
              )}
              {d.keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {d.keywords.slice(0, 5).map((k) => (
                    <span
                      key={k.id}
                      className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full"
                    >
                      {k.name}
                    </span>
                  ))}
                  {d.keywords.length > 5 && (
                    <span className="text-gray-400 text-xs px-2 py-0.5">
                      +{d.keywords.length - 5} more
                    </span>
                  )}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
