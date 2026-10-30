export type UserRole = 'administrator' | 'technician' | 'analyst' | 'researcher';

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: UserRole | null;
  mfa_enabled: boolean;
  is_active: boolean;
}

export interface Patient {
  id: string;
  patient_code: string;
  date_of_birth: string | null;
  biological_sex: 'male' | 'female' | 'intersex' | 'not_specified' | null;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  is_synthetic: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type SampleStatus = 'registered' | 'collected' | 'received' | 'processing' | 'completed' | 'rejected' | 'archived';

export interface Sample {
  id: string;
  sample_code: string;
  patient_id: string;
  sample_type: string;
  collection_notes: string | null;
  collected_at: string | null;
  received_at: string | null;
  status: SampleStatus;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface TestCategory {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface ReferenceRange {
  id: string;
  applicable_sex: string | null;
  min_age_years: number | null;
  max_age_years: number | null;
  lower_limit: number | null;
  upper_limit: number | null;
  unit: string | null;
  qualitative_normal_values: string | null;
  source: string;
  notes: string | null;
  is_active: boolean;
}

export interface LaboratoryTest {
  id: string;
  test_code: string;
  name: string;
  category_id: string;
  category_name: string | null;
  measurement_unit: string | null;
  result_type: 'numeric' | 'qualitative' | 'text';
  allowed_values: string | null;
  description: string | null;
  is_active: boolean;
  reference_ranges: ReferenceRange[];
  created_at: string;
}

export interface TestResult {
  id: string;
  sample_id: string;
  sample_code: string | null;
  test_id: string;
  test_code: string | null;
  test_name: string | null;
  numeric_value: number | null;
  qualitative_value: string | null;
  text_value: string | null;
  measurement_unit: string | null;
  is_above_upper_limit: boolean | null;
  is_below_lower_limit: boolean | null;
  measured_at: string;
  status: 'pending' | 'verified' | 'corrected' | 'cancelled';
  verified_at: string | null;
  verified_by_name: string | null;
  revisions_count: number;
  created_at: string;
}

export interface DashboardSummary {
  total_patients: number;
  total_samples: number;
  total_tests: number;
  completed_tests: number;
  pending_tests: number;
  verified_results: number;
  data_quality_issues: number;
  statistical_anomalies: number;
}
