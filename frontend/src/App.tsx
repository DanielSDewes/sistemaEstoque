import { Route, Routes } from 'react-router-dom';

import { costCentersApi, paymentMethodsApi } from '@/api/endpoints';
import Layout from '@/components/Layout';
import { ProtectedRoute } from '@/auth/ProtectedRoute';
import AlertsPage from '@/pages/AlertsPage';
import AuditPage from '@/pages/AuditPage';
import CategoriesPage from '@/pages/CategoriesPage';
import ComprasPage from '@/pages/ComprasPage';
import CustomersPage from '@/pages/CustomersPage';
import DashboardPage from '@/pages/DashboardPage';
import AccountsPage from '@/pages/finance/AccountsPage';
import BankAccountsPage from '@/pages/finance/BankAccountsPage';
import CashFlowPage from '@/pages/finance/CashFlowPage';
import FinanceDashboardPage from '@/pages/finance/FinanceDashboardPage';
import FinancialCategoriesPage from '@/pages/finance/FinancialCategoriesPage';
import SimpleNameCrud from '@/pages/finance/SimpleNameCrud';
import InventoryPage from '@/pages/InventoryPage';
import LocationsPage from '@/pages/LocationsPage';
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import LoginPage from '@/pages/LoginPage';
import MovementsPage from '@/pages/MovementsPage';
import NotFoundPage from '@/pages/NotFoundPage';
import OrdersPage from '@/pages/OrdersPage';
import ProductsPage from '@/pages/ProductsPage';
import ProfilePage from '@/pages/ProfilePage';
import ProfitReportPage from '@/pages/ProfitReportPage';
import ReportsPage from '@/pages/ReportsPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import RolesPage from '@/pages/RolesPage';
import SuppliersPage from '@/pages/SuppliersPage';
import UsersPage from '@/pages/UsersPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/produtos" element={<ProductsPage />} />
        <Route path="/movimentacoes" element={<MovementsPage />} />
        <Route path="/inventario" element={<InventoryPage />} />
        <Route path="/alertas" element={<AlertsPage />} />
        <Route path="/categorias" element={<CategoriesPage />} />
        <Route path="/localizacao" element={<LocationsPage />} />
        <Route path="/fornecedores" element={<SuppliersPage />} />
        <Route path="/clientes" element={<CustomersPage />} />
        <Route path="/pedidos" element={<OrdersPage />} />
        <Route path="/compras" element={<ComprasPage />} />
        <Route path="/financeiro/receber" element={<AccountsPage direction="receber" />} />
        <Route path="/financeiro/pagar" element={<AccountsPage direction="pagar" />} />
        <Route path="/financeiro/fluxo" element={<CashFlowPage />} />
        <Route path="/financeiro/painel" element={<FinanceDashboardPage />} />
        <Route
          path="/financeiro/formas-pagamento"
          element={<SimpleNameCrud title="Formas de Pagamento" subtitle="Meios usados nas baixas" queryKey="payment-methods" api={paymentMethodsApi} />}
        />
        <Route path="/financeiro/categorias" element={<FinancialCategoriesPage />} />
        <Route
          path="/financeiro/centros-custo"
          element={<SimpleNameCrud title="Centros de Custo" subtitle="Classificação por setor" queryKey="cost-centers" api={costCentersApi} />}
        />
        <Route path="/financeiro/contas-bancarias" element={<BankAccountsPage />} />
        <Route path="/lucro" element={<ProfitReportPage />} />
        <Route path="/relatorios" element={<ReportsPage />} />
        <Route path="/auditoria" element={<AuditPage />} />
        <Route path="/usuarios" element={<UsersPage />} />
        <Route path="/perfis" element={<RolesPage />} />
        <Route path="/perfil" element={<ProfilePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
