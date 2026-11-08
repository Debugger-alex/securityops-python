import type { Customer, CustomerPage, CustomerStatus, Dashboard } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Serverfehler (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const getCustomers = (q: string) =>
  request<CustomerPage>(`/customers?limit=100&q=${encodeURIComponent(q)}`);

export const getDashboard = () => request<Dashboard>("/dashboard");

export const createCustomer = (data: {
  company_name: string;
  email?: string;
  phone?: string;
}) =>
  request<Customer>("/customers", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateCustomerStatus = (id: string, status: CustomerStatus) =>
  request<Customer>(`/customers/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
