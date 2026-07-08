import { api } from './client';
import { createCrudApi, type ListParams } from './crud';
import type {
  AlertsSummary,
  AuditLog,
  BankAccount,
  Batch,
  BelowMinimumItem,
  CashFlowReport,
  CatalogItem,
  Corridor,
  CostCenter,
  Customer,
  Dashboard,
  FinanceDashboardData,
  FinancialAccount,
  FinancialCategory,
  FinancialDirection,
  FinancialStatus,
  ImportResult,
  Inventory,
  LoginResponse,
  Movement,
  NearExpiryItem,
  Order,
  OrderStatus,
  Page,
  PaymentMethod,
  Permission,
  Product,
  ProductLocationLink,
  ProductSupplierLink,
  ProfitReport,
  Role,
  Shelf,
  SuggestedCharges,
  Supplier,
  User,
} from './types';

// --- Auth ---
export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const form = new URLSearchParams({ username, password });
    const { data } = await api.post<LoginResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },
  me: async (): Promise<User> => (await api.get<User>('/auth/me')).data,
  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },
};

// --- Catalog CRUD resources ---
export const categoriesApi = createCrudApi<CatalogItem>('/categories');
export const groupsApi = createCrudApi<CatalogItem>('/groups');
export const subgroupsApi = createCrudApi<CatalogItem>('/subgroups');
export const brandsApi = createCrudApi<CatalogItem>('/brands');
export const corridorsApi = createCrudApi<Corridor>('/corridors');
export const shelvesApi = createCrudApi<Shelf>('/shelves');
export const suppliersApi = createCrudApi<Supplier>('/suppliers');
export const customersApi = createCrudApi<Customer>('/customers');
export const productsApi = createCrudApi<Product>('/products');
export const paymentMethodsApi = createCrudApi<PaymentMethod>('/finance/payment-methods');
export const financialCategoriesApi = createCrudApi<FinancialCategory>('/finance/categories');
export const costCentersApi = createCrudApi<CostCenter>('/finance/cost-centers');
export const bankAccountsApi = createCrudApi<BankAccount>('/finance/bank-accounts');
export const usersApi = createCrudApi<User>('/users');
export const rolesApi = createCrudApi<Role>('/roles');

// --- Products extras ---
export const productHistory = async (id: number, params: ListParams = {}): Promise<Page<Movement>> =>
  (await api.get<Page<Movement>>(`/products/${id}/history`, { params })).data;

export const productExtrasApi = {
  // Suppliers per product
  suppliers: async (productId: number): Promise<ProductSupplierLink[]> =>
    (await api.get<ProductSupplierLink[]>(`/product-suppliers/product/${productId}`)).data,
  linkSupplier: async (payload: {
    product_id: number;
    supplier_id: number;
    current_price?: number | null;
    supplier_product_code?: string | null;
    is_primary?: boolean;
  }): Promise<ProductSupplierLink> =>
    (await api.post<ProductSupplierLink>('/product-suppliers', payload)).data,
  updateSupplier: async (
    linkId: number,
    payload: Partial<{ current_price: number; is_primary: boolean; supplier_product_code: string }>,
  ): Promise<ProductSupplierLink> =>
    (await api.put<ProductSupplierLink>(`/product-suppliers/${linkId}`, payload)).data,
  unlinkSupplier: async (linkId: number): Promise<void> => {
    await api.delete(`/product-suppliers/${linkId}`);
  },
  // Batches
  batches: async (productId: number): Promise<Batch[]> =>
    (await api.get<Batch[]>(`/products/${productId}/batches`)).data,
  createBatch: async (payload: {
    product_id: number;
    lot_number: string;
    expiry_date?: string | null;
    manufacture_date?: string | null;
    serial_number?: string | null;
  }): Promise<Batch> => (await api.post<Batch>('/batches', payload)).data,
  deleteBatch: async (id: number): Promise<void> => {
    await api.delete(`/batches/${id}`);
  },
  // Locations
  locations: async (productId: number): Promise<ProductLocationLink[]> =>
    (await api.get<ProductLocationLink[]>(`/products/${productId}/locations`)).data,
  assignLocation: async (payload: {
    product_id: number;
    corridor_id: number;
    shelf_id: number;
    is_primary?: boolean;
  }): Promise<ProductLocationLink> =>
    (await api.post<ProductLocationLink>('/product-locations', payload)).data,
  removeLocation: async (id: number): Promise<void> => {
    await api.delete(`/product-locations/${id}`);
  },
  // Photo + import
  uploadPhoto: async (productId: number, file: File): Promise<Product> => {
    const form = new FormData();
    form.append('file', file);
    return (
      await api.post<Product>(`/products/${productId}/photo`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data;
  },
  importCsv: async (file: File): Promise<ImportResult> => {
    const form = new FormData();
    form.append('file', file);
    return (
      await api.post<ImportResult>('/products/import', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data;
  },
};

// --- Alerts ---
export const alertsApi = {
  summary: async (): Promise<AlertsSummary> => (await api.get<AlertsSummary>('/alerts/summary')).data,
  belowMinimum: async (): Promise<BelowMinimumItem[]> =>
    (await api.get<BelowMinimumItem[]>('/alerts/below-minimum')).data,
  nearExpiry: async (): Promise<NearExpiryItem[]> =>
    (await api.get<NearExpiryItem[]>('/alerts/near-expiry')).data,
};

// --- Permissions + role update ---
export const permissionsApi = {
  list: async (): Promise<Permission[]> => (await api.get<Permission[]>('/permissions')).data,
};

export const rolesExtraApi = {
  update: async (
    id: number,
    payload: { name?: string; description?: string; permission_ids?: number[] },
  ): Promise<Role> => (await api.put<Role>(`/roles/${id}`, payload)).data,
  create: async (payload: {
    name: string;
    description?: string;
    permission_ids: number[];
  }): Promise<Role> => (await api.post<Role>('/roles', payload)).data,
};

export const accountApi = {
  changePassword: async (current_password: string, new_password: string): Promise<void> => {
    await api.post('/users/me/change-password', { current_password, new_password });
  },
};

// --- Dashboard ---
export const dashboardApi = {
  get: async (days = 14): Promise<Dashboard> =>
    (await api.get<Dashboard>('/dashboard', { params: { days } })).data,
};

// --- Movements ---
export interface MovementCreate {
  product_id: number;
  movement_type: string;
  quantity: number;
  unit_cost?: number | null;
  reason?: string | null;
  document?: string | null;
}

export const movementsApi = {
  list: async (params: ListParams = {}): Promise<Page<Movement>> =>
    (await api.get<Page<Movement>>('/movements', { params })).data,
  create: async (payload: MovementCreate): Promise<Movement> =>
    (await api.post<Movement>('/movements', payload)).data,
  cancel: async (id: number, reason: string): Promise<Movement> =>
    (await api.post<Movement>(`/movements/${id}/cancel`, { reason })).data,
};

// --- CRM: customer sales history + orders ---
export const customerOrders = async (
  customerId: number,
  params: ListParams = {},
): Promise<Page<Order>> =>
  (await api.get<Page<Order>>(`/customers/${customerId}/orders`, { params })).data;

export interface OrderItemPayload {
  product_id: number;
  quantity: number;
  unit_price: number;
}

export interface OrderCreatePayload {
  customer_id: number;
  order_date?: string | null;
  notes?: string | null;
  extra_cost?: number;
  items: OrderItemPayload[];
}

export interface OrdersListParams extends ListParams {
  customer_id?: number;
  status?: OrderStatus;
}

export interface ProfitReportParams {
  start?: string;
  end?: string;
  group_by?: 'day' | 'month';
}

export const ordersApi = {
  list: async (params: OrdersListParams = {}): Promise<Page<Order>> =>
    (await api.get<Page<Order>>('/orders', { params })).data,
  get: async (id: number): Promise<Order> => (await api.get<Order>(`/orders/${id}`)).data,
  create: async (payload: OrderCreatePayload): Promise<Order> =>
    (await api.post<Order>('/orders', payload)).data,
  update: async (id: number, payload: Partial<OrderCreatePayload>): Promise<Order> =>
    (await api.put<Order>(`/orders/${id}`, payload)).data,
  confirm: async (id: number): Promise<Order> =>
    (await api.post<Order>(`/orders/${id}/confirm`)).data,
  cancel: async (id: number, reason: string): Promise<Order> =>
    (await api.post<Order>(`/orders/${id}/cancel`, { reason })).data,
  remove: async (id: number): Promise<void> => {
    await api.delete(`/orders/${id}`);
  },
  profitReport: async (params: ProfitReportParams = {}): Promise<ProfitReport> =>
    (await api.get<ProfitReport>('/orders/reports/profit', { params })).data,
};

// --- Finance: accounts, installments, settlements, reports ---
export interface InstallmentInputPayload {
  due_date: string;
  amount: number;
}

export interface InstallmentPlanPayload {
  count: number;
  first_due_date: string;
  interval_days?: number;
}

export interface FinancialAccountPayload {
  direction: FinancialDirection;
  customer_id?: number | null;
  supplier_id?: number | null;
  document?: string | null;
  description?: string | null;
  category_id?: number | null;
  cost_center_id?: number | null;
  issue_date?: string | null;
  notes?: string | null;
  total_amount?: number | null;
  installment_plan?: InstallmentPlanPayload | null;
  installments?: InstallmentInputPayload[] | null;
}

export interface SettlementPayload {
  amount: number;
  settled_at?: string | null;
  payment_method_id?: number | null;
  bank_account_id?: number | null;
  interest?: number;
  fine?: number;
  discount?: number;
  notes?: string | null;
}

export interface AccountsListParams extends ListParams {
  direction?: FinancialDirection;
  status?: FinancialStatus;
  customer_id?: number;
  supplier_id?: number;
  category_id?: number;
  overdue?: boolean;
  due_from?: string;
  due_to?: string;
}

export interface CashFlowParams {
  start?: string;
  end?: string;
  group_by?: 'day' | 'week' | 'month';
}

export const financeApi = {
  listAccounts: async (params: AccountsListParams = {}): Promise<Page<FinancialAccount>> =>
    (await api.get<Page<FinancialAccount>>('/finance/accounts', { params })).data,
  getAccount: async (id: number): Promise<FinancialAccount> =>
    (await api.get<FinancialAccount>(`/finance/accounts/${id}`)).data,
  createAccount: async (payload: FinancialAccountPayload): Promise<FinancialAccount> =>
    (await api.post<FinancialAccount>('/finance/accounts', payload)).data,
  cancelAccount: async (id: number): Promise<FinancialAccount> =>
    (await api.post<FinancialAccount>(`/finance/accounts/${id}/cancel`)).data,
  suggestedCharges: async (installmentId: number): Promise<SuggestedCharges> =>
    (await api.get<SuggestedCharges>(`/finance/installments/${installmentId}/suggested-charges`)).data,
  settle: async (installmentId: number, payload: SettlementPayload): Promise<FinancialAccount> =>
    (await api.post<FinancialAccount>(`/finance/installments/${installmentId}/settlements`, payload)).data,
  cancelSettlement: async (settlementId: number): Promise<FinancialAccount> =>
    (await api.post<FinancialAccount>(`/finance/settlements/${settlementId}/cancel`)).data,
  cashflow: async (params: CashFlowParams = {}): Promise<CashFlowReport> =>
    (await api.get<CashFlowReport>('/finance/cashflow', { params })).data,
  dashboard: async (): Promise<FinanceDashboardData> =>
    (await api.get<FinanceDashboardData>('/finance/dashboard')).data,
};

// --- Inventory ---
export const inventoryApi = {
  list: async (params: ListParams = {}): Promise<Inventory[]> =>
    (await api.get<Inventory[]>('/inventories', { params })).data,
  get: async (id: number): Promise<Inventory> =>
    (await api.get<Inventory>(`/inventories/${id}`)).data,
  create: async (payload: { code: string; scope: string; description?: string }): Promise<Inventory> =>
    (await api.post<Inventory>('/inventories', payload)).data,
  count: async (invId: number, itemId: number, counted_quantity: number): Promise<Inventory> =>
    (await api.patch<Inventory>(`/inventories/${invId}/items/${itemId}`, { counted_quantity })).data,
  finish: async (id: number): Promise<Inventory> =>
    (await api.post<Inventory>(`/inventories/${id}/finish`)).data,
  approve: async (id: number): Promise<Inventory> =>
    (await api.post<Inventory>(`/inventories/${id}/approve`)).data,
};

// --- Audit ---
export const auditApi = {
  list: async (params: ListParams = {}): Promise<Page<AuditLog>> =>
    (await api.get<Page<AuditLog>>('/audit', { params })).data,
};

// --- Reports ---
export const reportsApi = {
  list: async (): Promise<Record<string, string>> =>
    (await api.get<Record<string, string>>('/reports')).data,
  exportUrl: (report: string, fmt: string) => `/reports/${report}/export?fmt=${fmt}`,
  download: async (report: string, fmt: string): Promise<Blob> =>
    (await api.get(`/reports/${report}/export`, { params: { fmt }, responseType: 'blob' })).data,
};
