<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">
      Trial Balance Report
    </h1>

    <!-- Filters -->
    <div class="flex flex-wrap items-end mb-6 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
        <input type="date" v-model="startDate" class="border rounded p-2" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
        <input type="date" v-model="endDate" class="border rounded p-2" />
      </div>
      <button
        @click="fetchTrialBalance"
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

      <div class="ml-auto flex gap-3">
        <button
          @click="exportToPDF"
          class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Export PDF
        </button>
        <button
          @click="exportToExcel"
          class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Export Excel
        </button>
        <button
          @click="$router.push('/reports')"
          class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Back to Reports
        </button>
      </div>
    </div>

    <!-- Trial Balance Table -->
    <div class="overflow-x-auto bg-white shadow-md rounded-lg">
      <table class="min-w-full border border-gray-200 rounded-lg">
        <thead class="bg-gray-100 text-gray-800 uppercase text-sm font-semibold">
          <tr>
            <th class="p-2 border-b text-left w-1/4">Account Name</th>
            <th class="p-2 border-b text-right w-1/6">Opening Dr</th>
            <th class="p-2 border-b text-right w-1/6">Opening Cr</th>
            <th class="p-2 border-b text-right w-1/6">Movement Dr</th>
            <th class="p-2 border-b text-right w-1/6">Movement Cr</th>
            <th class="p-2 border-b text-right w-1/6">Closing Balance</th>
          </tr>
        </thead>

        <tbody v-if="trialGroups.length">
          <template v-for="group in trialGroups" :key="group.account_type">
            <!-- Group Header -->
            <tr class="bg-gray-50 font-bold text-indigo-700">
              <td class="p-2 border-b" colspan="6">
                {{ group.account_type }}
              </td>
            </tr>

            <!-- Recursive Accounts -->
            <AccountTRow
              v-for="acc in group.accounts"
              :key="acc.account_id"
              :account="acc"
            />

            <!-- Group Totals -->
            <tr class="bg-gray-100 font-semibold border-t-2 border-gray-300">
              <td class="p-2 text-right pr-4">Subtotal ({{ group.account_type }})</td>
              <td class="p-2 text-right text-green-700">
                {{ formatCurrency(group.subtotal_opening_debit) }}
              </td>
              <td class="p-2 text-right text-red-700">
                {{ formatCurrency(group.subtotal_opening_credit) }}
              </td>
              <td class="p-2 text-right text-green-700">
                {{ formatCurrency(group.subtotal_movement_debit) }}
              </td>
              <td class="p-2 text-right text-red-700">
                {{ formatCurrency(group.subtotal_movement_credit) }}
              </td>
              <td class="p-2 text-right font-bold">
                {{ formatCurrency(group.subtotal_closing) }}
              </td>
            </tr>
          </template>

          <!-- Grand Totals -->
          <tr class="bg-indigo-100 font-bold text-indigo-800 border-t-4 border-indigo-300">
            <td class="p-2 text-right">Grand Totals</td>
            <td class="p-2 text-right text-green-700">
              {{ formatCurrency(totals.total_opening_debit) }}
            </td>
            <td class="p-2 text-right text-red-700">
              {{ formatCurrency(totals.total_opening_credit) }}
            </td>
            <td class="p-2 text-right text-green-700">
              {{ formatCurrency(totals.total_movement_debit) }}
            </td>
            <td class="p-2 text-right text-red-700">
              {{ formatCurrency(totals.total_movement_credit) }}
            </td>
            <td class="p-2 text-right font-bold">
              {{ formatCurrency(grandClosingBalance) }}
            </td>
          </tr>
        </tbody>

        <tbody v-else>
          <tr>
            <td colspan="6" class="text-center p-4 text-gray-500">
              No data available for this period.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import api from "@/api";
import html2pdf from "html2pdf.js";
import * as XLSX from "xlsx";
import AccountTRow from "./AccountTRow.vue";

const startDate = ref("");
const endDate = ref("");
const trialGroups = ref([]);
const totals = ref({
  total_opening_debit: 0,
  total_opening_credit: 0,
  total_movement_debit: 0,
  total_movement_credit: 0,
});
const grandClosingBalance = computed(() =>
  trialGroups.value.reduce((sum, g) => sum + g.subtotal_closing, 0)
);

const formatCurrency = (val) =>
  val ? val.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "-";

const fetchTrialBalance = async () => {
  try {
    const res = await api.get("/reports/trial-balance", {
      params: { start_date: startDate.value, end_date: endDate.value },
    });
    trialGroups.value = res.data.groups ? Object.values(res.data.groups) : [];
    totals.value = res.data.totals || {};
  } catch (err) {
    console.error("Error fetching Trial Balance:", err);
  }
};

const resetFilters = () => {
  startDate.value = "";
  endDate.value = "";
  fetchTrialBalance();
};

// ---------------- PDF Export ----------------
const exportToPDF = () => {
  const element = document.querySelector(".max-w-6xl");
  html2pdf()
    .set({
      margin: 0.4,
      filename: `Trial_Balance_${new Date().toISOString().slice(0, 10)}.pdf`,
      html2canvas: { scale: 2 },
      jsPDF: { orientation: "landscape" },
    })
    .from(element)
    .save();
};

// ---------------- Excel Export ----------------
const exportToExcel = () => {
  const wb = XLSX.utils.book_new();
  const rows = [];

  rows.push([
    "Account Name",
    "Opening Dr",
    "Opening Cr",
    "Movement Dr",
    "Movement Cr",
    "Closing Balance",
  ]);

  trialGroups.value.forEach((group) => {
    rows.push([`${group.account_type} (Subtotal)`]);
    group.accounts.forEach((acc) => {
      rows.push([
        acc.account_name,
        acc.opening_debit,
        acc.opening_credit,
        acc.movement_debit,
        acc.movement_credit,
        acc.closing_balance,
      ]);
    });
  });

  const ws = XLSX.utils.aoa_to_sheet(rows);
  XLSX.utils.book_append_sheet(wb, ws, "Trial Balance");
  XLSX.writeFile(
    wb,
    `Trial_Balance_${new Date().toISOString().slice(0, 10)}.xlsx`
  );
};

onMounted(fetchTrialBalance);
</script>

<style scoped>
table {
  border-collapse: collapse;
}
th,
td {
  font-size: 0.875rem;
}
.bg-green-50 {
  background-color: #f0fdf4;
}
.bg-red-50 {
  background-color: #fef2f2;
}
.text-green-700 {
  color: #15803d;
}
.text-red-700 {
  color: #b91c1c;
}
</style>
