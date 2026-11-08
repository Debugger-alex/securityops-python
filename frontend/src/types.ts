export type CustomerStatus = "active" | "inactive" | "lead";
export type CustomerSort = "company_name" | "customer_number" | "created_at" | "status";

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
