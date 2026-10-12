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
  const [landlords, setLandlords] = useState<string[]>([]);
  const [officers, setOfficers] = useState<string[]>([]);
  const [filters, setFilters] = useState({
    keyword: "",
    city: "",
    decision_type: "",
    landlord: "",
    hearing_officer: "",
    q: "",
    date_from: "",
    date_to: "",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    client.get("/api/keywords/").then((r) => setKeywords(r.data));
    client.get("/api/decisions/landlords").then((r) => setLandlords(r.data));
    client.get("/api/decisions/hearing-officers").then((r) => setOfficers(r.data));
    search();
  }, []);

  const search = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filters.keyword) params.append("keyword", filters.keyword);
    if (filters.city) params.append("city", filters.city);
    if (filters.decision_type) params.append("decision_type", filters.decision_type);
    if (filters.landlord) params.append("landlord", filters.landlord);
    if (filters.hearing_officer) params.append("hearing_officer", filters.hearing_officer);
    if (filters.q) params.append("q", filters.q);
    if (filters.date_from) params.append("date_from", filters.date_from);
    if (filters.date_to) params.append("date_to", filters.date_to);
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
        {/* Row 1: Main filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
        </div>

        {/* Row 2: Landlord, Hearing Officer, Search */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Landlord / Respondent
            </label>
            <select
              value={filters.landlord}
              onChange={(e) =>
                setFilters({ ...filters, landlord: e.target.value })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">All Landlords</option>
              {landlords.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Hearing Officer
            </label>
            <select
              value={filters.hearing_officer}
              onChange={(e) =>
                setFilters({ ...filters, hearing_officer: e.target.value })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="">All Officers</option>
              {officers.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Search anything..."
              value={filters.q}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* Row 3: Date range */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Decision Date From
            </label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Decision Date To
            </label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
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
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-gray-900 text-lg">
                  {d.address || "Address not available"}
                  {d.unit && `, Unit ${d.unit}`}
                </h3>
                {d.amount_awarded != null && (
                  <span className="text-sm font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded">
                    ${d.amount_awarded.toLocaleString()}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-1 text-sm mb-3">
                <div>
                  <span className="text-gray-400">City: </span>
                  <span className="text-gray-700">{d.city}</span>
                </div>
                {d.decision_date && (
                  <div>
                    <span className="text-gray-400">Date: </span>
                    <span className="text-gray-700">
                      {new Date(d.decision_date).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {d.case_number && (
                  <div>
                    <span className="text-gray-400">Case #: </span>
                    <span className="text-gray-700">{d.case_number}</span>
                  </div>
                )}
                {d.respondent_name && (
                  <div>
                    <span className="text-gray-400">Landlord: </span>
                    <span className="text-gray-700">{d.respondent_name}</span>
                  </div>
                )}
                {d.hearing_officer && (
                  <div>
                    <span className="text-gray-400">Hearing Officer: </span>
                    <span className="text-gray-700">{d.hearing_officer}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-400">Type: </span>
                  <span className="text-gray-700">{formatType(d.decision_type)}</span>
                </div>
              </div>

              {d.outcome_summary && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {d.outcome_summary}
                </p>
              )}

              {d.keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
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
