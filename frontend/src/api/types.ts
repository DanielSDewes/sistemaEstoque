// Shared types mirroring the backend Pydantic schemas.

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface Permission {
  id: number;
  code: string;
  description: string;
}

export interface Role {
  id: number;
  name: string;
  description: string | null;
  is_system: boolean;
  permissions: Permission[];
}

export interface User {
  id: number;
  full_name: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  role: Role;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type Status = 'ativo' | 'inativo';

export interface CatalogItem {
  id: number;
  code: string;
  name: string;
  description: string | null;
  status: Status;
}

export type Corridor = CatalogItem;

export interface Shelf {
  id: number;
  code: string;
  name: string;
  corridor_id: number;
  corridor: Corridor;
  capacity: number | null;
  observations: string | null;
  status: Status;
}

export interface ProductStock {
  current: number;
  reserved: number;
  available: number;
  min_stock: number;
  max_stock: number;
  reorder_point: number;
  below_minimum: boolean;
}

export interface Product {
  id: number;
  internal_code: string;
  barcode: string | null;
  sku: string | null;
  name: string;
  short_name: string | null;
  description: string | null;
  unit: string;
  is_active: boolean;
  photo_url: string | null;
  min_stock: number;
  max_stock: number;
  reorder_point: number;
  reserved_stock: number;
  average_cost: number;
  sale_price: number;
  category: CatalogItem | null;
  group: CatalogItem | null;
  brand: CatalogItem | null;
  stock: ProductStock | null;
}

export interface Batch {
  id: number;
  product_id: number;
  lot_number: string;
  serial_number: string | null;
  manufacture_date: string | null;
  expiry_date: string | null;
  status: Status;
}

export interface ProductLocationLink {
  id: number;
  product_id: number;
  corridor_id: number;
  shelf_id: number;
  quantity: number;
  corridor: Corridor;
  shelf: Shelf;
  stock_balance: number;
}

export interface ProductSupplierLink {
  id: number;
  product_id: number;
  supplier_id: number;
  supplier: Supplier;
  supplier_product_code: string | null;
  last_price: number | null;
  current_price: number | null;
  average_price: number | null;
  last_purchase_date: string | null;
  lead_time_days: number | null;
  is_primary: boolean;
}

export interface ImportResult {
  created: number;
  updated: number;
  errors: { line: number; error: string }[];
}

export interface AlertsSummary {
  below_minimum_count: number;
  near_expiry_count: number;
  expired_count: number;
  out_of_stock_count: number;
}

export interface BelowMinimumItem {
  product_id: number;
  internal_code: string;
  name: string;
  current: number;
  min_stock: number;
  reorder_point: number;
  deficit: number;
}

export interface NearExpiryItem {
  product_id: number;
  internal_code: string;
  name: string;
  lot_number: string;
  expiry_date: string;
  days_remaining: number;
}

export type MovementType =
  | 'compra'
  | 'ajuste_entrada'
  | 'devolucao'
  | 'producao'
  | 'venda'
  | 'consumo_interno'
  | 'perda'
  | 'quebra'
  | 'transferencia'
  | 'ajuste_saida';

export interface Movement {
  id: number;
  product_id: number;
  movement_type: MovementType;
  direction: 'entrada' | 'saida';
  quantity: number;
  unit_cost: number | null;
  moved_at: string;
  reason: string | null;
  document: string | null;
  is_cancelled: boolean;
}

export interface Supplier {
  id: number;
  legal_name: string;
  trade_name: string | null;
  cnpj: string;
  city: string | null;
  state: string | null;
  email: string | null;
  phone: string | null;
  status: Status;
}

export interface CustomerAddress {
  id?: number;
  label: string | null;
  street: string | null;
  number: string | null;
  complement: string | null;
  district: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  is_primary: boolean;
}

export interface Customer {
  id: number;
  name: string;
  phone: string;
  document: string | null;
  email: string | null;
  notes: string | null;
  status: Status;
  addresses: CustomerAddress[];
}

export interface CustomerSummary {
  id: number;
  name: string;
  phone: string;
}

export type OrderStatus = 'rascunho' | 'confirmado' | 'cancelado';

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  product_code: string;
  quantity: number;
  unit_price: number;
  unit_cost: number;
  line_total: number;
}

export interface Order {
  id: number;
  number: string | null;
  customer_id: number;
  customer: CustomerSummary;
  status: OrderStatus;
  order_date: string;
  notes: string | null;
  total_amount: number;
  extra_cost: number;
  total_cost: number;
  profit: number;
  items: OrderItem[];
  confirmed_at: string | null;
  cancelled_at: string | null;
}

export interface ProfitPeriod {
  period: string;
  orders: number;
  revenue: number;
  cost: number;
  extra_cost: number;
  profit: number;
}

export interface ProfitReport {
  start: string;
  end: string;
  group_by: 'day' | 'month';
  totals: ProfitPeriod;
  periods: ProfitPeriod[];
}

// --- Finance ---
export type FinancialDirection = 'receber' | 'pagar';
export type FinancialStatus =
  | 'em_aberto'
  | 'parcial'
  | 'quitado'
  | 'vencido'
  | 'cancelado'
  | 'renegociado';
export type FinancialCategoryKind = 'receita' | 'despesa';

export interface PaymentMethod {
  id: number;
  name: string;
  status: Status;
}

export interface FinancialCategory {
  id: number;
  name: string;
  kind: FinancialCategoryKind;
  status: Status;
}

export interface CostCenter {
  id: number;
  name: string;
  status: Status;
}

export interface BankAccount {
  id: number;
  name: string;
  bank: string | null;
  agency: string | null;
  account_number: string | null;
  opening_balance: number;
  current_balance: number;
  status: Status;
}

export interface FinancialSettlement {
  id: number;
  installment_id: number;
  settled_at: string;
  amount: number;
  interest: number;
  fine: number;
  discount: number;
  payment_method_id: number | null;
  payment_method_name: string | null;
  bank_account_id: number | null;
  notes: string | null;
  is_cancelled: boolean;
}

export interface FinancialInstallment {
  id: number;
  number: number;
  total_installments: number;
  due_date: string;
  original_amount: number;
  interest: number;
  fine: number;
  addition: number;
  discount: number;
  amount_paid: number;
  balance: number;
  status: FinancialStatus;
  settlements: FinancialSettlement[];
}

export interface FinancialAccount {
  id: number;
  direction: FinancialDirection;
  customer_id: number | null;
  supplier_id: number | null;
  party_name: string | null;
  document: string | null;
  description: string | null;
  category_id: number | null;
  category_name: string | null;
  cost_center_id: number | null;
  cost_center_name: string | null;
  issue_date: string;
  total_amount: number;
  total_paid: number;
  balance: number;
  notes: string | null;
  status: FinancialStatus;
  installments: FinancialInstallment[];
}

export interface SuggestedCharges {
  days_overdue: number;
  interest: number;
  fine: number;
  balance: number;
}

export interface CashFlowPeriod {
  period: string;
  inflow_expected: number;
  outflow_expected: number;
  inflow_realized: number;
  outflow_realized: number;
  net_expected: number;
  net_realized: number;
}

export interface CashFlowReport {
  start: string;
  end: string;
  group_by: 'day' | 'week' | 'month';
  totals: CashFlowPeriod;
  periods: CashFlowPeriod[];
}

export interface BankBalance {
  id: number;
  name: string;
  balance: number;
}

export interface FinanceDashboardData {
  receivable_open: number;
  receivable_overdue: number;
  received_today: number;
  received_month: number;
  payable_open: number;
  payable_overdue: number;
  paid_today: number;
  paid_month: number;
  cash_total: number;
  banks: BankBalance[];
}

export interface AuditLog {
  id: number;
  username: string | null;
  action: string;
  entity: string | null;
  entity_id: number | null;
  field: string | null;
  old_value: string | null;
  new_value: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface SeriesPoint {
  label: string;
  value: number;
}

export interface NamedSeries {
  name: string;
  points: SeriesPoint[];
}

export interface Dashboard {
  kpis: {
    total_products: number;
    products_no_stock: number;
    products_below_min: number;
    products_near_expiry: number;
    movements_today: number;
    total_stock_quantity: number;
    total_stock_value: number;
    total_suppliers: number;
  };
  movements_by_day: SeriesPoint[];
  top_moved_products: SeriesPoint[];
  stock_by_category: SeriesPoint[];
  entries_vs_exits: NamedSeries[];
}

export interface InventoryItem {
  id: number;
  product_id: number;
  system_quantity: number;
  counted_quantity: number | null;
  difference: number | null;
  divergence_pct: number | null;
  counted_at: string | null;
  notes: string | null;
}

export interface Inventory {
  id: number;
  code: string;
  description: string | null;
  scope: string;
  scope_ref_id: number | null;
  status: 'em_aberto' | 'em_andamento' | 'finalizado' | 'aprovado' | 'cancelado';
  items?: InventoryItem[];
}
