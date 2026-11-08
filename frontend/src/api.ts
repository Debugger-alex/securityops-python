import type {
  AuthUser,
  ObjectAssignableUser,
  ObjectAssignment,
  ObjectContact,
  ObjectHistory,
  ObjectPage,
  ObjectSensitiveData,
  ObjectStatus,
  SecurityObject,
  Customer,
  CustomerAddressInput,
  CustomerContact,
  CustomerContactInput,
  CustomerHistory,
  CustomerPage,
  CustomerSort,
  CustomerStatus,
  Dashboard,
  Session,
} from "./types";

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

export interface CustomerFilters {
  q: string;
  status: CustomerStatus | "";
  includeArchived: boolean;
  sortBy: CustomerSort;
  sortOrder: "asc" | "desc";
  limit: number;
  offset: number;
}

export const getCustomers = (filters: CustomerFilters) => {
  const params = new URLSearchParams({
    limit: String(filters.limit),
    offset: String(filters.offset),
    sort_by: filters.sortBy,
    sort_order: filters.sortOrder,
  });
  if (filters.q.trim()) params.set("q", filters.q.trim());
  if (filters.status) params.set("status", filters.status);
  if (filters.includeArchived) params.set("include_archived", "true");
  return request<CustomerPage>(`/customers?${params}`);
};

export const getDashboard = () => request<Dashboard>("/dashboard");

export type CustomerInput = {
  company_name: string;
  status?: CustomerStatus;
  email?: string;
  phone?: string;
  legal_form?: string;
  vat_number?: string;
  tax_number?: string;
  internal_notes?: string;
  business_address?: CustomerAddressInput | null;
  billing_address?: CustomerAddressInput | null;
};

export type CustomerUpdateInput = {
  company_name?: string;
  status?: CustomerStatus;
  email?: string | null;
  phone?: string | null;
  legal_form?: string | null;
  vat_number?: string | null;
  tax_number?: string | null;
  internal_notes?: string | null;
  business_address?: CustomerAddressInput | null;
  billing_address?: CustomerAddressInput | null;
};

export const createCustomer = (data: CustomerInput) =>
  request<Customer>("/customers", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getCustomer = (id: string) => request<Customer>(`/customers/${id}`);

export const getCustomerHistory = (id: string) =>
  request<CustomerHistory[]>(`/customers/${id}/history?limit=100`);

export const updateCustomer = (id: string, data: CustomerUpdateInput) =>
  request<Customer>(`/customers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const archiveCustomer = (id: string) =>
  request<Customer>(`/customers/${id}/archive`, { method: "POST" });

export const reactivateCustomer = (id: string) =>
  request<Customer>(`/customers/${id}/reactivate`, { method: "POST" });

export const createCustomerContact = (customerId: string, data: CustomerContactInput) =>
  request<CustomerContact>(`/customers/${customerId}/contacts`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateCustomerContact = (
  customerId: string,
  contactId: string,
  data: { is_primary: boolean },
) =>
  request<CustomerContact>(`/customers/${customerId}/contacts/${contactId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteCustomerContact = (customerId: string, contactId: string) =>
  request<void>(`/customers/${customerId}/contacts/${contactId}`, { method: "DELETE" });

export interface SecurityObjectInput {
  customer_id: string;
  name: string;
  status?: ObjectStatus;
  description?: string | null;
  service_instructions?: string | null;
  street: string;
  house_number: string;
  postal_code: string;
  city: string;
  country_code?: string;
  phone?: string | null;
  email?: string | null;
  operating_hours?: Record<string, { start: string; end: string }[]>;
  required_staffing?: number;
  qualification_requirements?: string[];
  object_manager_user_id?: string | null;
}

export interface ObjectFilters {
  q: string;
  customerId: string;
  status: ObjectStatus | "";
  includeArchived: boolean;
  limit: number;
  offset: number;
}

export const getObjects = (filters: ObjectFilters) => {
  const params = new URLSearchParams({
    limit: String(filters.limit),
    offset: String(filters.offset),
  });
  if (filters.q.trim()) params.set("q", filters.q.trim());
  if (filters.customerId) params.set("customer_id", filters.customerId);
  if (filters.status) params.set("status", filters.status);
  if (filters.includeArchived) params.set("include_archived", "true");
  return request<ObjectPage>(`/objects?${params}`);
};

export const getObject = (id: string) => request<SecurityObject>(`/objects/${id}`);

export const createObject = (data: SecurityObjectInput) =>
  request<SecurityObject>("/objects", { method: "POST", body: JSON.stringify(data) });

export const updateObject = (id: string, data: Partial<SecurityObjectInput>) =>
  request<SecurityObject>(`/objects/${id}`, { method: "PATCH", body: JSON.stringify(data) });

export const archiveObject = (id: string) =>
  request<SecurityObject>(`/objects/${id}/archive`, { method: "POST" });

export const getObjectHistory = (id: string) =>
  request<ObjectHistory[]>(`/objects/${id}/history?limit=100`);

export const getObjectContacts = (id: string) =>
  request<ObjectContact[]>(`/objects/${id}/contacts`);

export const createObjectContact = (id: string, data: Omit<ObjectContact, "id">) =>
  request<ObjectContact>(`/objects/${id}/contacts`, { method: "POST", body: JSON.stringify(data) });

export const removeObjectContact = (objectId: string, contactId: string) =>
  request<void>(`/objects/${objectId}/contacts/${contactId}`, { method: "DELETE" });

export const getObjectAssignments = (id: string) =>
  request<ObjectAssignment[]>(`/objects/${id}/assignments`);

export const getObjectAssignmentCandidates = () =>
  request<ObjectAssignableUser[]>("/objects/assignment-candidates");

export const assignUserToObject = (objectId: string, userId: string) =>
  request<ObjectAssignment>(`/objects/${objectId}/assignments`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });

export const removeObjectAssignment = (objectId: string, userId: string) =>
  request<void>(`/objects/${objectId}/assignments/${userId}`, { method: "DELETE" });

export const getObjectSensitiveData = (id: string) =>
  request<ObjectSensitiveData>(`/objects/${id}/sensitive-data`);

export const updateObjectSensitiveData = (
  id: string,
  data: Omit<ObjectSensitiveData, "updated_at">,
) =>
  request<ObjectSensitiveData>(`/objects/${id}/sensitive-data`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const getUsers = () => request<AuthUser[]>("/users");
