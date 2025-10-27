<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">Profit & Loss Dashboard</h1>

    <!-- Tabs -->
    <div class="flex mb-6 space-x-2">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="switchTab(tab.key)"
        :class="[
          'px-4 py-2 rounded',
          activeTab === tab.key
            ? 'bg-indigo-500 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        ]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap items-end mb-6 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Year</label>
        <select v-model="selectedYear" class="border rounded p-2">
          <option v-for="year in availableYears" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Month</label>
        <select v-model="selectedMonth" class="border rounded p-2">
          <option value="">All Months</option>
          <option v-for="(name, num) in months" :key="num" :value="num">
            {{ name }}
          </option>
        </select>
      </div>

      <button
        @click="fetchReport"
        class="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
      >
        Filter
      </button>

      <button
        @click="resetFilters"
        class="px-4 py-2 bg-gray-400 text-white rounded hover:bg-gray-500"
      >
        Reset
      </button>

      <div class="ml-auto flex gap-2">
        <button
          @click="exportExcel"
          class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Export Excel
        </button>
        <button
          @click="exportPDF"
          class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Export PDF
        </button>
        <button
          @click="$router.push('/reports')"
          class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Back to Reports
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="min-w-full border border-gray-200 rounded shadow">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-2 border-b text-left">Name / Account</th>
            <th class="p-2 border-b text-right">Amount (UGX)</th>
          </tr>
        </thead>
        <tbody>
          <!-- Revenue -->
          <tr class="font-bold bg-gray-50">
            <td class="p-2 border-b">Revenue</td>
            <td></td>
          </tr>
          <tr v-for="acc in revenueAccounts" :key="acc.id">
            <td class="p-2 border-b pl-4">{{ acc.name }}</td>
            <td class="p-2 border-b text-right">
              {{ acc.balance.toLocaleString() }}
            </td>
          </tr>
          <tr class="font-bold bg-gray-100">
            <td class="p-2 border-b">Total Revenue</td>
            <td class="p-2 border-b text-right">
              {{ totalRevenue.toLocaleString() }}
            </td>
          </tr>

          <!-- Expenses -->
          <tr class="font-bold bg-gray-50">
            <td class="p-2 border-b">Expenses</td>
            <td></td>
          </tr>
          <tr v-for="acc in otherExpenses" :key="acc.id">
            <td class="p-2 border-b pl-4">{{ acc.name }}</td>
            <td class="p-2 border-b text-right">
              {{ acc.balance.toLocaleString() }}
            </td>
          </tr>
          <tr class="font-bold bg-gray-100">
            <td class="p-2 border-b">Total Expenses</td>
            <td class="p-2 border-b text-right">
              {{ totalExpenses.toLocaleString() }}
            </td>
          </tr>

          <!-- Net Profit before COGS -->
          <tr class="font-bold bg-gray-200">
            <td class="p-2 border-b">Net Profit (Revenue - Expenses)</td>
            <td class="p-2 border-b text-right">
              {{ netProfit.toLocaleString() }}
            </td>
          </tr>

          <!-- COGS -->
          <tr class="font-bold bg-gray-50">
            <td class="p-2 border-b">COGS</td>
            <td></td>
          </tr>
          <tr v-for="acc in cogsAccounts" :key="acc.id">
            <td class="p-2 border-b pl-4">{{ acc.name }}</td>
            <td class="p-2 border-b text-right">
              {{ acc.balance.toLocaleString() }}
            </td>
          </tr>
          <tr class="font-bold bg-gray-100">
            <td class="p-2 border-b">Total COGS</td>
            <td class="p-2 border-b text-right">
              {{ totalCogs.toLocaleString() }}
            </td>
          </tr>

          <!-- Net Profit after COGS -->
          <tr class="font-bold bg-gray-200">
            <td class="p-2 border-b">Net Profit after COGS</td>
            <td class="p-2 border-b text-right">
              {{ netProfitAfterCogs.toLocaleString() }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "@/api";
import * as XLSX from "xlsx";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

const tabs = [
  { key: "professional", label: "All-Time Totals", endpoint: "/reports/profit-loss-professional" },
  { key: "periodic", label: "Monthly Totals", endpoint: "/reports/profit-loss-periodic" },
  { key: "ytd", label: "Monthly + YTD", endpoint: "/reports/profit-loss-ytd" },
];

const activeTab = ref("professional");
const revenueAccounts = ref([]);
const otherExpenses = ref([]);
const cogsAccounts = ref([]);
const totalRevenue = ref(0);
const totalExpenses = ref(0);
const totalCogs = ref(0);
const netProfit = ref(0);
const netProfitAfterCogs = ref(0);

const currentYear = new Date().getFullYear();
const availableYears = Array.from({ length: 6 }, (_, i) => currentYear - i);
const months = {
  1: "January",
  2: "February",
  3: "March",
  4: "April",
  5: "May",
  6: "June",
  7: "July",
  8: "August",
  9: "September",
  10: "October",
  11: "November",
  12: "December",
};

const selectedYear = ref(currentYear);
const selectedMonth = ref("");

const fetchReport = async () => {
  const tab = tabs.find((t) => t.key === activeTab.value);
  if (!tab) return;

  try {
    let start_date, end_date;

    if (selectedMonth.value) {
      const month = String(selectedMonth.value).padStart(2, "0");
      start_date = `${selectedYear.value}-${month}-01`;
      const days = new Date(selectedYear.value, selectedMonth.value, 0).getDate();
      end_date = `${selectedYear.value}-${month}-${days}`;
    } else {
      start_date = `${selectedYear.value}-01-01`;
      end_date = `${selectedYear.value}-12-31`;
    }

    const res = await api.get(tab.endpoint, { params: { start_date, end_date } });

    const accs = res.data.accounts || res.data.data?.accounts || [];

    revenueAccounts.value = accs.filter((a) => a.type === "REVENUE");
    cogsAccounts.value = accs.filter((a) => a.id === 30);
    otherExpenses.value = accs.filter((a) => a.type === "EXPENSE" && a.id !== 30);

    totalRevenue.value = revenueAccounts.value.reduce((sum, a) => sum + a.balance, 0);
    totalExpenses.value = otherExpenses.value.reduce((sum, a) => sum + a.balance, 0);
    totalCogs.value = cogsAccounts.value.reduce((sum, a) => sum + a.balance, 0);

    netProfit.value = totalRevenue.value - totalExpenses.value;
    netProfitAfterCogs.value = netProfit.value - totalCogs.value;
  } catch (err) {
    console.error("Error fetching P&L:", err);
  }
};

const switchTab = (key) => {
  activeTab.value = key;
  fetchReport();
};

const resetFilters = () => {
  selectedYear.value = currentYear;
  selectedMonth.value = "";
  fetchReport();
};

// ---------------- Export to Excel ----------------
const exportExcel = () => {
  const wsData = [
    ["Profit & Loss Report"],
    [],
    ["Revenue"],
    ...revenueAccounts.value.map((a) => [a.name, a.balance]),
    ["Total Revenue", totalRevenue.value],
    [],
    ["Expenses"],
    ...otherExpenses.value.map((a) => [a.name, a.balance]),
    ["Total Expenses", totalExpenses.value],
    [],
    ["COGS"],
    ...cogsAccounts.value.map((a) => [a.name, a.balance]),
    ["Total COGS", totalCogs.value],
    [],
    ["Net Profit", netProfit.value],
    ["Net Profit After COGS", netProfitAfterCogs.value],
  ];

  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(wsData);
  XLSX.utils.book_append_sheet(wb, ws, "P&L");
  XLSX.writeFile(wb, `Profit_and_Loss_${selectedYear.value}.xlsx`);
};

// ---------------- Export to PDF ----------------
const exportPDF = () => {
  const doc = new jsPDF();
  doc.setFontSize(14);
  doc.text("Profit & Loss Report", 14, 15);

  autoTable(doc, {
    startY: 25,
    head: [["Name / Account", "Amount (UGX)"]],
    body: [
      ...revenueAccounts.value.map((a) => [a.name, a.balance.toLocaleString()]),
      ["Total Revenue", totalRevenue.value.toLocaleString()],
      [],
      ...otherExpenses.value.map((a) => [a.name, a.balance.toLocaleString()]),
      ["Total Expenses", totalExpenses.value.toLocaleString()],
      [],
      ...cogsAccounts.value.map((a) => [a.name, a.balance.toLocaleString()]),
      ["Total COGS", totalCogs.value.toLocaleString()],
      [],
      ["Net Profit", netProfit.value.toLocaleString()],
      ["Net Profit After COGS", netProfitAfterCogs.value.toLocaleString()],
    ],
  });

  doc.save(`Profit_and_Loss_${selectedYear.value}.pdf`);
};

onMounted(fetchReport);
</script>

<style scoped>
table {
  border-collapse: collapse;
}
th,
td {
  text-align: left;
}
</style>
