export type CustomerStatus = "active" | "inactive" | "lead";
export type CustomerSort = "company_name" | "customer_number" | "created_at" | "status";
export type ObjectStatus = "active" | "inactive";
export type ObjectSort = "name" | "code" | "created_at" | "status";
export type EmployeeStatus = "active" | "inactive" | "leave" | "terminated";
export type EmployeeAbsenceType = "vacation" | "sick_leave" | "other";
export type EmployeeAbsenceStatus = "pending" | "approved" | "rejected";

export interface CustomerAddress {
  id: string;
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  country_code: string;
}

export interface CustomerContact {
  id: string;
  first_name: string;
  last_name: string;
  responsibility: string | null;
  email: string | null;
  phone: string | null;
  is_primary: boolean;
}

export interface CustomerContactInput {
  first_name: string;
  last_name: string;
  responsibility?: string;
  email?: string;
  phone?: string;
  is_primary: boolean;
}

export interface Customer {
  id: string;
  customer_number: string;
  company_name: string;
  status: CustomerStatus;
  email: string | null;
  phone: string | null;
  legal_form: string | null;
  vat_number: string | null;
  tax_number: string | null;
  internal_notes: string | null;
  archived_at: string | null;
  business_address: CustomerAddress | null;
  billing_address: CustomerAddress | null;
  contacts: CustomerContact[];
  created_at: string;
  updated_at: string;
}

export interface CustomerHistory {
  id: string;
  actor_id: string | null;
  action: string;
  changed_fields: string[];
  created_at: string;
}

export interface CustomerAddressInput {
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  country_code: string;
}

export interface CustomerPage {
  items: Customer[];
  total: number;
  limit: number;
  offset: number;
}

export interface Employee {
  id: string;
  employee_number: string;
  user_id: string | null;
  full_name: string;
  email: string | null;
  phone: string | null;
  job_title: string | null;
  employment_status: EmployeeStatus;
  hired_on: string;
  ended_on: string | null;
  contract_type: string | null;
  weekly_hours: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeePage {
  items: Employee[];
  total: number;
  limit: number;
  offset: number;
}

export interface EmployeeQualification {
  id: string;
  employee_id: string;
  category: string;
  name: string;
  issuer: string | null;
  valid_from: string | null;
  expires_on: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeAbsence {
  id: string;
  employee_id: string;
  absence_type: EmployeeAbsenceType;
  starts_on: string;
  ends_on: string;
  status: EmployeeAbsenceStatus;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeSensitiveDetails {
  employee_id: string;
  address: string | null;
  emergency_contact: string | null;
  internal_notes: string | null;
  updated_at: string | null;
}

export interface EmployeeHistory {
  id: string;
  actor_id: string | null;
  action: string;
  changed_fields: string[];
  created_at: string;
}

export interface Dashboard {
  customers_total: number;
  customers_active: number;
  customers_leads: number;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
  permissions: string[];
}

export interface Session {
  user: AuthUser;
}

export interface ObjectAddress {
  id: string;
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  country_code: string;
}

export interface ObjectAddressInput {
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  country_code: string;
}

export interface ObjectContact {
  id: string;
  first_name: string;
  last_name: string;
  role: string | null;
  email: string | null;
  phone: string | null;
  is_primary: boolean;
}

export interface ObjectContactInput {
  first_name: string;
  last_name: string;
  role?: string | null;
  email?: string | null;
  phone?: string | null;
  is_primary: boolean;
}

export interface SecurityObject {
  id: string;
  customer_id: string;
  customer_name: string;
  code: string;
  name: string;
  object_type: string | null;
  description: string | null;
  status: ObjectStatus;
  operating_hours: string | null;
  service_times: string | null;
  staffing_requirements: string | null;
  archived_at: string | null;
  address: ObjectAddress | null;
  contacts: ObjectContact[];
  created_at: string;
  updated_at: string;
}

export interface ObjectPage {
  items: SecurityObject[];
  total: number;
  limit: number;
  offset: number;
}

export interface ObjectHistory {
  id: string;
  actor_id: string | null;
  action: string;
  changed_fields: string[];
  created_at: string;
}

export interface ObjectSecurityDetails {
  object_id: string;
  security_requirements: string | null;
  access_information: string | null;
  emergency_contact: string | null;
  updated_at: string | null;
}

export interface ObjectAssignment {
  user_id: string;
  username: string;
  full_name: string;
  assigned_at: string;
}

export interface ObjectAssignmentCandidate {
  id: string;
  username: string;
  full_name: string;
}
