import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { isAdmin } = useAuth();

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-14">
        <Link to="/" className="font-bold text-gray-900">
          CLSEPA Petition Database
        </Link>
        <div className="flex gap-4 text-sm">
          <Link to="/" className="text-gray-600 hover:text-gray-900">
            Search
          </Link>
          {isAdmin ? (
            <Link to="/admin" className="text-blue-700 hover:underline">
              Admin
            </Link>
          ) : (
            <Link to="/login" className="text-gray-600 hover:text-gray-900">
              Staff Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
