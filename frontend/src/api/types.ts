export interface Keyword {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Decision {
  id: string;
  case_number: string | null;
  city: string;
  address: string | null;
  unit: string | null;
  petitioner_name: string | null;
  respondent_name: string | null;
  hearing_date: string | null;
  decision_date: string | null;
  decision_type: string | null;
  hearing_officer: string | null;
  outcome_summary: string | null;
  amount_awarded: number | null;
  pdf_filename: string;
  keywords: Keyword[];
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_admin: boolean;
  created_at: string;
}
