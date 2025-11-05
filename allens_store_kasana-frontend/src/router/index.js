// import { createRouter, createWebHistory } from 'vue-router';
import { createRouter, createWebHistory } from 'vue-router';

import MainLayout from '../layouts/MainLayout.vue';
import Dashboard from '../pages/Dashboard.vue';
import Products from '../pages/Products.vue';
import Sales from '../pages/Sales.vue';
import Purchases from '../pages/Purchases.vue';
import Report from '../pages/Reports.vue';
import Expenses from '../pages/Expenses.vue';
import Supplier from '../pages/Supplier.vue';
import Customer from '../pages/Customer.vue';
import User from '../pages/User.vue';
import Purchaselist from '@/pages/PurchaseList.vue';
import SalesList from '../pages/SalesList.vue';

// Reports
import OutOfStock from '@/pages/reports/OutOfStock.vue';
import StockList from '@/pages/reports/StockList.vue';
import Consumption from '@/pages/reports/ConsumptionList.vue';
import Performance from '@/pages/reports/Performance.vue';
import PurchaseReport from '@/pages/reports/PurchaseReport.vue';
import ExpenseReport from '@/pages/reports/ExpenseReport.vue';
import Creditor from '@/pages/reports/CreditorList.vue';
import Debtor from '@/pages/reports/DebtorList.vue';
import CashFlow from '@/pages/reports/Cashflow.vue';
import TrialBalance from '@/pages/reports/Trialbalance.vue';
import ProfitAndLoss from '@/pages/reports/Profitandloss.vue';
import GeneralLedger from '@/pages/reports/Generalledger.vue';
import PurchaseDetails from '@/pages/reports/PurchaseDetails.vue';
import ExpenseDetailsReport from '@/pages/reports/ExpenseDetailsReport.vue';
import Login from '@/pages/Login.vue';
import PurchaseOrderEdit from '@/pages/PurchaseOrderEdit.vue';
import Acoa from '@/pages/reports/Acoa.vue';
import Accounts from '@/pages/Accounts.vue';
import BalanceSheet from '@/pages/reports/BalanceSheet.vue';
import UserProfile from '@/pages/UserProfile.vue';
import CustomeReturns from '@/pages/CustomeReturns.vue';
import ReturnablesForm from '@/pages/ReturnablesForm.vue';
import SalesProfitLoss from '@/pages/reports/SalesProfitLoss.vue';
import CustomerManagement from '@/pages/CustomerManagement.vue';
import EditSale from '@/pages/EditSale.vue';
import EditPurchases from '@/pages/EditPurchases.vue';
// import EditSale from '@/pages/EditSale.vue';

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', component: Dashboard, meta: { showGreeting: true, pageName: 'Dashboard',requiresAuth: true, } },
      { path: 'dashboard', component: Dashboard, meta: { showGreeting: true, pageName: 'Dashboard',requiresAuth: true, } },
      { path: 'accounts', component: Accounts, meta: { showGreeting: true, pageName: 'Accounts',requiresAuth: true, } },

      { path: 'products', component: Products, meta: { showGreeting: true, pageName: 'Products',requiresAuth: true, } },
      { path: 'customers', component: Customer, meta: { showGreeting: false, pageName: 'Customers',requiresAuth: true, } },
      { path: 'sales', component: Sales, meta: { showGreeting: false, pageName: 'Sales',requiresAuth: true, } },
      { path: '/editsale', component: EditSale, meta: { showGreeting: false, pageName: 'EditSale',requiresAuth: true, } },
      {
        path: '/editsales/:id',
        name: 'Edit Sale',
        component: EditSale,
        meta: { showGreeting: false, pageName: 'Edit Sale', requiresAuth: true,}
      },
      { path: 'purchases', component: Purchases, meta: { showGreeting: true, pageName: 'Purchases',requiresAuth: true, } },
      { path: 'expenses', component: Expenses, meta: { showGreeting: false, pageName: 'Expenses',requiresAuth: true, } },
      { path: 'reports/expenses/:id', component: ExpenseDetailsReport, meta: { showGreeting: false, pageName: 'Expenses Details',requiresAuth: true, } },
      // {
      //   path: '/purchase-orders/:id/edit',
      //   component:PurchaseOrderEdit,meta: { showGreeting: false, pageName: 'EditPurchaseOrder',requiresAuth: true, }},
      
      
      { path: 'supplier', component: Supplier, meta: { showGreeting: false, pageName: 'Supplier',requiresAuth: true, } },
      { path: 'users', component: User, meta: { showGreeting: false, pageName: 'Users',requiresAuth: true, } },
      // { path: 'login', component: Login, meta: { showGreeting: false, pageName: 'Login',requiresAuth: true, } },

      { path: 'purchaselist', component: Purchaselist, meta: { showGreeting: false, pageName: 'Purchase List',requiresAuth: true, } },
      { path: 'saleslist', component: SalesList, meta: { showGreeting: false, pageName: 'Sales List',requiresAuth: true, } },

      // Reports Dashboard
      { path: 'reports', component: Report, meta: { showGreeting: false, pageName: 'Reports',requiresAuth: true, } },

      // Individual Reports
      { path: 'reports/general-ledger', component: GeneralLedger, meta: { showGreeting: false, pageName: 'General Ledger',requiresAuth: true, } },
      { path: 'reports/profit-loss', component: ProfitAndLoss, meta: { showGreeting: false, pageName: 'Profit & Loss',requiresAuth: true, } },
      { path: 'reports/trial-balance', component: TrialBalance, meta: { showGreeting: false, pageName: 'Trial Balance',requiresAuth: true, } },
      { path: 'reports/cash-flow', component: CashFlow, meta: { showGreeting: false, pageName: 'Cash Flow',requiresAuth: true, } },
      { path: 'reports/debtors-report', component: Debtor, meta: { showGreeting: false, pageName: 'Debtors Report',requiresAuth: true, } },
      { path: 'reports/creditors-report', component: Creditor, meta: { showGreeting: false, pageName: 'Creditors Report',requiresAuth: true, } },
      { path: 'reports/balance-sheet', component: BalanceSheet, meta: { showGreeting: false, pageName: 'Balance Sheet',requiresAuth: true, } },
      { path: 'reports/chart-of-accounts', component: Acoa, meta: { showGreeting: false, pageName: 'chart-of-accounts',requiresAuth: true, } },
      { path: '/enter_returnables', component: ReturnablesForm, meta: { showGreeting: false, pageName: 'Enter Returnables',requiresAuth: true, } },
      { path: 'reports/purchases-list', component: PurchaseReport, meta: { showGreeting: false, pageName: 'Purchases Report',requiresAuth: true, } },
      { path: 'reports/sales-list', component: SalesList, meta: { showGreeting: false, pageName: 'Sales Report',requiresAuth: true, } },
      { path: 'reports/performance-list', component: Performance, meta: { showGreeting: false, pageName: 'Performance Report',requiresAuth: true, } },
      { path: 'reports/consumption-list', component: Consumption, meta: { showGreeting: false, pageName: 'Consumption Report',requiresAuth: true, } },
      { path: 'reports/stock-list', component: StockList, meta: { showGreeting: false, pageName: 'Stock List',requiresAuth: true, } },
      { path: 'reports/out-of-stock', component: OutOfStock, meta: { showGreeting: false, pageName: 'Out Of Stock',requiresAuth: true, } },
      {
        path: '/purchase-orders/:id',
        name: 'PurchaseOrderDetails',
        component: PurchaseDetails,
        meta: { showGreeting: false, pageName: 'Purchase Order Details', requiresAuth: true,}
      },
      {
        path: '/purchase-orders/:id/edit',
        name: 'EditPurchaseOrder',
        component: EditPurchases,
        meta: { showGreeting: false, pageName: 'EditPurchaseOrder', requiresAuth: true,}
      },
      {
        path: '/profile',
        name: 'User Profile',
        component: UserProfile,
        meta: { showGreeting: false, pageName: 'User Profile', requiresAuth: true,}
      },
      {
        path: '/customereturns',
        name: 'Customer Returns',
        component: CustomeReturns,
        meta: { showGreeting: false, pageName: 'Customer Returns', requiresAuth: true,}
      },
      {
        path: '/customermanagement',
        name: 'CustomerManagement',
        component: CustomerManagement,
        meta: { showGreeting: false, pageName: 'CustomerManagement', requiresAuth: true,}
      },
      {
        path:'/reports/sales-profit-list',
        name:'Sales Profit',
        component: SalesProfitLoss,
        meta: { showGreeting: false, pageName: 'Sales Profit', requiresAuth: true,}

      }
        
      
      
    ],
  },
    {
      path: '/login',
      component: Login, // Standalone login page
      meta: { requiresAuth: false, pageName: 'Login' }
    }
  // },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// JWT token check
function isTokenExpired(token) {
  if (!token) return true;
  const payload = JSON.parse(atob(token.split('.')[1]));
  return payload.exp * 1000 < Date.now();
}

// Navigation guards
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  if (token && isTokenExpired(token)) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return next('/login');
  }

  if (to.meta.requiresAuth && !token) return next('/login');
  if (to.path === '/login' && token) return next('/');
  next();
});

export default router;