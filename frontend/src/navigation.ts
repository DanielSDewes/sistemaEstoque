import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import AssessmentIcon from '@mui/icons-material/Assessment';
import BusinessIcon from '@mui/icons-material/Business';
import CategoryIcon from '@mui/icons-material/Category';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import GroupIcon from '@mui/icons-material/Group';
import HandshakeIcon from '@mui/icons-material/Handshake';
import HistoryIcon from '@mui/icons-material/History';
import InsightsIcon from '@mui/icons-material/Insights';
import Inventory2Icon from '@mui/icons-material/Inventory2';
import ListAltIcon from '@mui/icons-material/ListAlt';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import PaidIcon from '@mui/icons-material/Paid';
import PaymentIcon from '@mui/icons-material/Payment';
import PeopleIcon from '@mui/icons-material/People';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import SavingsIcon from '@mui/icons-material/Savings';
import SellIcon from '@mui/icons-material/Sell';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import type { SvgIconComponent } from '@mui/icons-material';

export interface NavLeaf {
  label: string;
  path: string;
  icon: SvgIconComponent;
  permission?: string;
}

export interface NavGroup {
  label: string;
  icon: SvgIconComponent;
  children: NavLeaf[];
}

export type NavEntry = NavLeaf | NavGroup;

export function isGroup(entry: NavEntry): entry is NavGroup {
  return (entry as NavGroup).children !== undefined;
}

// Sidebar navigation grouped into collapsible sections. Leaves are filtered by
// the user's permissions; a group is hidden when it has no visible child.
export const NAV_ITEMS: NavEntry[] = [
  { label: 'Dashboard', path: '/', icon: DashboardIcon, permission: 'dashboard:view' },
  {
    label: 'Estoque',
    icon: Inventory2Icon,
    children: [
      { label: 'Produtos', path: '/produtos', icon: Inventory2Icon, permission: 'product:view' },
      { label: 'Movimentações', path: '/movimentacoes', icon: SwapVertIcon, permission: 'product:view' },
      { label: 'Inventário', path: '/inventario', icon: FactCheckIcon, permission: 'inventory:count' },
      { label: 'Alertas', path: '/alertas', icon: NotificationsActiveIcon, permission: 'product:view' },
      { label: 'Localização', path: '/localizacao', icon: ViewModuleIcon, permission: 'corridor:view' },
    ],
  },
  {
    label: 'Relacionamentos',
    icon: HandshakeIcon,
    children: [
      { label: 'Clientes', path: '/clientes', icon: PeopleIcon, permission: 'customer:view' },
      { label: 'Fornecedores', path: '/fornecedores', icon: LocalShippingIcon, permission: 'supplier:view' },
    ],
  },
  {
    label: 'Vendas',
    icon: PointOfSaleIcon,
    children: [
      { label: 'Pedidos', path: '/pedidos', icon: ReceiptLongIcon, permission: 'order:view' },
    ],
  },
  {
    label: 'Financeiro',
    icon: AccountBalanceIcon,
    children: [
      { label: 'Contas a Receber', path: '/financeiro/receber', icon: TrendingUpIcon, permission: 'finance:view' },
      { label: 'Contas a Pagar', path: '/financeiro/pagar', icon: TrendingDownIcon, permission: 'finance:view' },
      { label: 'Fluxo de Caixa', path: '/financeiro/fluxo', icon: AccountBalanceIcon, permission: 'finance:view' },
      { label: 'Painel Financeiro', path: '/financeiro/painel', icon: InsightsIcon, permission: 'finance:view' },
      { label: 'Formas de Pagamento', path: '/financeiro/formas-pagamento', icon: PaymentIcon, permission: 'finance:view' },
      { label: 'Categorias Financeiras', path: '/financeiro/categorias', icon: SellIcon, permission: 'finance:view' },
      { label: 'Centros de Custo', path: '/financeiro/centros-custo', icon: BusinessIcon, permission: 'finance:view' },
      { label: 'Contas Bancárias', path: '/financeiro/contas-bancarias', icon: SavingsIcon, permission: 'finance:view' },
    ],
  },
  {
    label: 'Catálogo',
    icon: ListAltIcon,
    children: [
      { label: 'Categorias', path: '/categorias', icon: CategoryIcon, permission: 'category:view' },
    ],
  },
  {
    label: 'Relatórios',
    icon: AssessmentIcon,
    children: [
      { label: 'Relatórios', path: '/relatorios', icon: AssessmentIcon, permission: 'report:view' },
      { label: 'Lucro', path: '/lucro', icon: PaidIcon, permission: 'report:view' },
    ],
  },
  {
    label: 'Administração',
    icon: ManageAccountsIcon,
    children: [
      { label: 'Usuários', path: '/usuarios', icon: GroupIcon, permission: 'user:view' },
      { label: 'Perfis', path: '/perfis', icon: AdminPanelSettingsIcon, permission: 'role:view' },
      { label: 'Auditoria', path: '/auditoria', icon: HistoryIcon, permission: 'audit:view' },
    ],
  },
];
