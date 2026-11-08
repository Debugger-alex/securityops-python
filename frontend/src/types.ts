export type CustomerStatus = "active" | "inactive" | "lead";

export interface Customer {
  id: string;
  customer_number: string;
  company_name: string;
  status: CustomerStatus;
  email: string | null;
  phone: string | null;
  created_at: string;
  updated_at: string;
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
