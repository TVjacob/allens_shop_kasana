<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-8 text-gray-800">Reports Dashboard</h1>

    <!-- Stock & Inventory -->
    <Section title="Stock & Inventory" :reports="stockReports" />

    <!-- Sales & Purchases -->
    <Section title="Sales & Purchases" :reports="salesReports" />

    <!-- Accounting -->
    <Section title="Accounting" :reports="accountingReports" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import Section from '@/components/Section.vue';

// Simulated user from localStorage or API
const user = JSON.parse(localStorage.getItem('user')) || { permissions: [] };

// Helper to check permission
const canView = (perm) => user.permissions.includes(perm);

// Reports grouped by sections
const stockReports = computed(() =>
  [
    { title: "Out of Stock", link: "/reports/out-of-stock", permission: "view_stock" },
    { title: "Stock List", link: "/reports/stock-list", permission: "view_stock" },
    { title: "Consumption List", link: "/reports/consumption-list", permission: "view_stock" },
    { title: "Performance List", link: "/reports/performance-list", permission: "view_stock" },
  ].filter(r => canView(r.permission))
);

const salesReports = computed(() =>
  [
    { title: "Sales List", link: "/reports/sales-list", permission: "view_sales" },
    { title: "Sales Profit", link: "/reports/sales-profit-list", permission: "view_sales" },
    { title: "Purchases List", link: "/reports/purchases-list", permission: "view_purchases" },
  ].filter(r => canView(r.permission))
);

const accountingReports = computed(() =>
  [
    { title: "General Ledger", link: "/reports/general-ledger", permission: "view_accounts" },
    { title: "Chart of Accounts", link: "/reports/chart-of-accounts", permission: "view_accounts" },
    { title: "Profit & Loss", link: "/reports/profit-loss", permission: "view_accounts" },
    { title: "Trial Balance", link: "/reports/trial-balance", permission: "view_accounts" },
    { title: "Cash Flow Statement", link: "/reports/cash-flow", permission: "view_accounts" },
    { title: "Debtors Report", link: "/reports/debtors-report", permission: "view_accounts" },
    { title: "Creditors Report", link: "/reports/creditors-report", permission: "view_accounts" },
    { title: "Balance Sheet", link: "/reports/balance-sheet", permission: "view_accounts" },
  ].filter(r => canView(r.permission))
);
</script>

<style scoped>
h1 {
  letter-spacing: 0.5px;
}
</style>
