import type {
  AuthUser,
  Customer,
  CustomerAddressInput,
  CustomerContractStatus,
  CustomerContact,
  CustomerContactInput,
  CustomerHistory,
  CustomerPage,
  CustomerSort,
  CustomerStatus,
  Dashboard,
  Employee,
  EmployeeAccountCandidate,
  EmployeeAbsence,
  EmployeeAbsenceStatus,
  EmployeeAbsenceType,
  EmployeeHistory,
  EmployeeObjectAssignment,
  EmployeeObjectAssignmentHistory,
  EmployeeObjectCandidate,
  EmployeePage,
  EmployeeQualification,
  EmployeeQualificationDocument,
  EmployeeSensitiveDetails,
  EmployeeStatus,
  ObjectAddressInput,
  ObjectAssignment,
  ObjectAssignmentCandidate,
  ObjectContact,
  ObjectContactInput,
  ObjectHistory,
  ObjectPage,
  ObjectSecurityDetails,
  ObjectSort,
  ObjectStatus,
  SecurityObject,
  Session,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method?.toUpperCase() ?? "GET";
  const isFormData = init?.body instanceof FormData;
  const csrf = method === "GET" || method === "HEAD"
    ? undefined
    : document.cookie.split("; ").find((cookie) => cookie.startsWith("securityops_csrf="))?.split("=")[1];
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "same-origin",
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
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
  contractStatus: CustomerContractStatus | "";
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
  if (filters.contractStatus) params.set("contract_status", filters.contractStatus);
  if (filters.includeArchived) params.set("include_archived", "true");
  return request<CustomerPage>(`/customers?${params}`);
};

export const getDashboard = () => request<Dashboard>("/dashboard");

export type CustomerInput = {
  company_name: string;
  status?: CustomerStatus;
  contract_status?: CustomerContractStatus;
  email?: string;
  phone?: string;
  legal_form?: string;
  website?: string;
  vat_number?: string;
  tax_number?: string;
  internal_notes?: string;
  business_address?: CustomerAddressInput | null;
  billing_address?: CustomerAddressInput | null;
};

export type CustomerUpdateInput = {
  company_name?: string;
  status?: CustomerStatus;
  contract_status?: CustomerContractStatus;
  email?: string | null;
  phone?: string | null;
  legal_form?: string | null;
  website?: string | null;
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

export const getUsers = () => request<AuthUser[]>("/users");

export interface EmployeeFilters {
  q: string;
  status: EmployeeStatus | "";
  includeArchived: boolean;
  sortBy: "employee_number" | "full_name" | "hired_on" | "employment_status";
  sortOrder: "asc" | "desc";
  limit: number;
  offset: number;
}

export type EmployeeInput = {
  employee_number: string;
  user_id?: string | null;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  job_title?: string | null;
  employment_status?: EmployeeStatus;
  hired_on: string;
  ended_on?: string | null;
  contract_type?: string | null;
  weekly_hours?: number | null;
};

export type EmployeeUpdateInput = Partial<EmployeeInput>;

export const getEmployees = (filters: EmployeeFilters) => {
  const params = new URLSearchParams({
    limit: String(filters.limit),
    offset: String(filters.offset),
    sort_by: filters.sortBy,
    sort_order: filters.sortOrder,
  });
  if (filters.q.trim()) params.set("q", filters.q.trim());
  if (filters.status) params.set("status", filters.status);
  if (filters.includeArchived) params.set("include_archived", "true");
  return request<EmployeePage>(`/employees?${params}`);
};

export const createEmployee = (data: EmployeeInput) =>
  request<Employee>("/employees", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getEmployee = (id: string) => request<Employee>(`/employees/${id}`);

export const getEmployeeLinkedUserCandidates = (employeeId?: string) =>
  request<EmployeeAccountCandidate[]>(
    `/employees/linked-user-candidates${employeeId ? `?employee_id=${employeeId}` : ""}`,
  );

export const getEmployeeObjectAssignments = (id: string) =>
  request<EmployeeObjectAssignment[]>(`/employees/${id}/objects`);

export const getEmployeeObjectAssignmentHistory = (id: string) =>
  request<EmployeeObjectAssignmentHistory[]>(
    `/employees/${id}/object-assignment-history?limit=100`,
  );

export const getEmployeeObjectAssignmentCandidates = () =>
  request<EmployeeObjectCandidate[]>("/employees/object-assignment-candidates");

export const assignEmployeeToObject = (employeeId: string, objectId: string) =>
  request<EmployeeObjectAssignment[]>(`/employees/${employeeId}/objects/${objectId}`, {
    method: "POST",
  });

export const endEmployeeObjectAssignment = (employeeId: string, objectId: string) =>
  request<EmployeeObjectAssignment[]>(`/employees/${employeeId}/objects/${objectId}`, {
    method: "DELETE",
  });

export const updateEmployee = (id: string, data: EmployeeUpdateInput) =>
  request<Employee>(`/employees/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const archiveEmployee = (id: string) =>
  request<Employee>(`/employees/${id}/archive`, { method: "POST" });

export const reactivateEmployee = (id: string) =>
  request<Employee>(`/employees/${id}/reactivate`, { method: "POST" });

export const getEmployeeQualifications = (id: string, includeArchived = false) =>
  request<EmployeeQualification[]>(
    `/employees/${id}/qualifications${includeArchived ? "?include_archived=true" : ""}`,
  );

export const getEmployeeQualificationDocuments = (employeeId: string) =>
  request<EmployeeQualificationDocument[]>(`/employees/${employeeId}/qualification-documents`);

export const uploadEmployeeQualificationDocument = (
  employeeId: string,
  qualificationId: string,
  file: File,
) => {
  const data = new FormData();
  data.append("document", file);
  return request<EmployeeQualificationDocument>(
    `/employees/${employeeId}/qualifications/${qualificationId}/documents`,
    { method: "POST", body: data },
  );
};

export const employeeQualificationDocumentUrl = (
  employeeId: string,
  qualificationId: string,
  documentId: string,
  download = false,
) =>
  `/api/v1/employees/${employeeId}/qualifications/${qualificationId}/documents/${documentId}${
    download ? "?download=true" : ""
  }`;

export const createEmployeeQualification = (
  id: string,
  data: {
    category: string;
    name: string;
    issuer?: string;
    valid_from?: string;
    expires_on?: string;
  },
) =>
  request<EmployeeQualification>(`/employees/${id}/qualifications`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const archiveEmployeeQualification = (employeeId: string, qualificationId: string) =>
  request<EmployeeQualification>(
    `/employees/${employeeId}/qualifications/${qualificationId}/archive`,
    { method: "POST" },
  );

export const getExpiringEmployeeQualifications = (days = 30) =>
  request<Array<EmployeeQualification & {
    employee_number: string;
    employee_name: string;
    days_until_expiry: number;
  }>>(`/employees/qualifications/expiring?days=${days}`);

export const getEmployeeAbsences = (id: string) =>
  request<EmployeeAbsence[]>(`/employees/${id}/absences`);

export const createEmployeeAbsence = (
  id: string,
  data: {
    absence_type: EmployeeAbsenceType;
    starts_on: string;
    ends_on: string;
    status?: EmployeeAbsenceStatus;
  },
) =>
  request<EmployeeAbsence>(`/employees/${id}/absences`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateEmployeeAbsence = (
  employeeId: string,
  absenceId: string,
  data: { status: EmployeeAbsenceStatus },
) =>
  request<EmployeeAbsence>(`/employees/${employeeId}/absences/${absenceId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const getEmployeeSensitiveDetails = (id: string) =>
  request<EmployeeSensitiveDetails>(`/employees/${id}/sensitive`);

export const updateEmployeeSensitiveDetails = (
  id: string,
  data: { address: string | null; emergency_contact: string | null; internal_notes: string | null },
) =>
  request<EmployeeSensitiveDetails>(`/employees/${id}/sensitive`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const getEmployeeHistory = (id: string) =>
  request<EmployeeHistory[]>(`/employees/${id}/history?limit=100`);

export interface ObjectFilters {
  q: string;
  status: ObjectStatus | "";
  customerId: string;
  includeArchived: boolean;
  sortBy: ObjectSort;
  sortOrder: "asc" | "desc";
  limit: number;
  offset: number;
}

export type ObjectInput = {
  customer_id: string;
  name: string;
  code?: string;
  object_type?: string;
  description?: string;
  status?: ObjectStatus;
  operating_hours?: string;
  service_times?: string;
  staffing_requirements?: string;
  address?: ObjectAddressInput;
  contacts?: ObjectContactInput[];
};

export type ObjectUpdateInput = {
  customer_id?: string;
  name?: string;
  code?: string;
  object_type?: string | null;
  description?: string | null;
  status?: ObjectStatus;
  operating_hours?: string | null;
  service_times?: string | null;
  staffing_requirements?: string | null;
  address?: ObjectAddressInput | null;
};

export const getObjects = (filters: ObjectFilters) => {
  const params = new URLSearchParams({
    limit: String(filters.limit),
    offset: String(filters.offset),
    sort_by: filters.sortBy,
    sort_order: filters.sortOrder,
  });
  if (filters.q.trim()) params.set("q", filters.q.trim());
  if (filters.status) params.set("status", filters.status);
  if (filters.customerId) params.set("customer_id", filters.customerId);
  if (filters.includeArchived) params.set("include_archived", "true");
  return request<ObjectPage>(`/objects?${params}`);
};

export const getCustomerObjects = (customerId: string) =>
  getObjects({
    q: "",
    status: "",
    customerId,
    includeArchived: true,
    sortBy: "name",
    sortOrder: "asc",
    limit: 100,
    offset: 0,
  });

export const getObject = (id: string) => request<SecurityObject>(`/objects/${id}`);
export const getObjectHistory = (id: string) =>
  request<ObjectHistory[]>(`/objects/${id}/history?limit=100`);

export const createObject = (data: ObjectInput) =>
  request<SecurityObject>("/objects", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateObject = (id: string, data: ObjectUpdateInput) =>
  request<SecurityObject>(`/objects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const archiveObject = (id: string) =>
  request<SecurityObject>(`/objects/${id}/archive`, { method: "POST" });

export const reactivateObject = (id: string) =>
  request<SecurityObject>(`/objects/${id}/reactivate`, { method: "POST" });

export const createObjectContact = (objectId: string, data: ObjectContactInput) =>
  request<ObjectContact>(`/objects/${objectId}/contacts`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateObjectContact = (
  objectId: string,
  contactId: string,
  data: Partial<ObjectContactInput>,
) =>
  request<ObjectContact>(`/objects/${objectId}/contacts/${contactId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteObjectContact = (objectId: string, contactId: string) =>
  request<void>(`/objects/${objectId}/contacts/${contactId}`, { method: "DELETE" });

export const getObjectSecurity = (id: string) =>
  request<ObjectSecurityDetails>(`/objects/${id}/security`);

export const updateObjectSecurity = (
  id: string,
  data: Partial<Omit<ObjectSecurityDetails, "object_id" | "updated_at">>,
) =>
  request<ObjectSecurityDetails>(`/objects/${id}/security`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const getObjectAssignmentCandidates = () =>
  request<ObjectAssignmentCandidate[]>("/objects/assignment-candidates");

export const getObjectAssignments = (id: string) =>
  request<ObjectAssignment[]>(`/objects/${id}/assignments`);

export const updateObjectAssignments = (id: string, userIds: string[]) =>
  request<ObjectAssignment[]>(`/objects/${id}/assignments`, {
    method: "PUT",
    body: JSON.stringify({ user_ids: userIds }),
  });
