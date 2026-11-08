import type { AuthUser, Customer, CustomerPage, CustomerStatus, Dashboard, Session } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method?.toUpperCase() ?? "GET";
  const csrf = method === "GET" || method === "HEAD"
    ? undefined
    : document.cookie.split("; ").find((cookie) => cookie.startsWith("securityops_csrf="))?.split("=")[1];
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}),
      ...init?.headers,
    },
  });
  if (response.status === 204) return undefined as T;
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Serverfehler (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const getSession = () => request<Session>("/auth/me");

export const login = (username: string, password: string) =>
  request<Session>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

export const logout = () => request<void>("/auth/logout", { method: "POST" });

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

export const getUsers = () => request<AuthUser[]>("/users");
