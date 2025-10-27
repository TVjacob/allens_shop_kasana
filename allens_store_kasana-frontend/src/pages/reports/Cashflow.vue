<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">{{ reportTitle }}</h1>

    <div class="mb-4 flex justify-between items-center">
      <button @click="goBack" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2">
        Back
      </button>
      <div>
        <button @click="exportExcel" class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded mr-2">
          Export Excel
        </button>
        <button @click="exportPDF" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
          Export PDF
        </button>
      </div>
    </div>

    <table class="min-w-full border border-gray-200 rounded shadow">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border-b">Description</th>
          <th class="p-2 border-b text-right">Opening Balance (UGX)</th>
          <th class="p-2 border-b text-right">Period Movement (UGX)</th>
          <th class="p-2 border-b text-right">Closing Balance (UGX)</th>
        </tr>
      </thead>
      <tbody>
        <!-- Inflows -->
        <tr class="font-bold text-green-700">
          <td class="p-2 border-b">Cash Inflows</td>
          <td class="p-2 border-b text-right">{{ totals.inflows.total_opening.toLocaleString() }}</td>
          <td class="p-2 border-b text-right">{{ totals.inflows.total_movement.toLocaleString() }}</td>
          <td class="p-2 border-b text-right">{{ totals.inflows.total_closing.toLocaleString() }}</td>
        </tr>
        <template v-for="acc in inflows" :key="acc.account_id">
          <CashFlowRow :account="acc" :level="1" color="green" />
        </template>

        <!-- Outflows -->
        <tr class="font-bold text-red-600">
          <td class="p-2 border-b">Cash Outflows</td>
          <td class="p-2 border-b text-right">{{ totals.outflows.total_opening.toLocaleString() }}</td>
          <td class="p-2 border-b text-right">{{ totals.outflows.total_movement.toLocaleString() }}</td>
          <td class="p-2 border-b text-right">{{ totals.outflows.total_closing.toLocaleString() }}</td>
        </tr>
        <template v-for="acc in outflows" :key="acc.account_id">
          <CashFlowRow :account="acc" :level="1" color="red" />
        </template>

        <!-- Net Cash Flow -->
        <tr class="font-bold bg-gray-200">
          <td class="p-2 border-b">Net Cash Flow</td>
          <td class="p-2 border-b text-right">{{ totals.net.opening_balance.toLocaleString() }}</td>
          <td class="p-2 border-b text-right">{{ totals.net.movement.toLocaleString() }}</td>
          <td class="p-2 border-b text-right">{{ totals.net.closing_balance.toLocaleString() }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import CashFlowRow from './CashFlowRow.vue'; // <-- separate SFC for recursive row

const reportTitle = ref('Cash Flow Statement');
const inflows = ref([]);
const outflows = ref([]);
const totals = ref({
  inflows: { total_opening: 0, total_movement: 0, total_closing: 0 },
  outflows: { total_opening: 0, total_movement: 0, total_closing: 0 },
  net: { opening_balance: 0, movement: 0, closing_balance: 0 },
});
const endpoint = '/reports/cash-flow';

const fetchReport = async () => {
  try {
    const res = await api.get(endpoint);
    inflows.value = res.data.inflows;
    outflows.value = res.data.outflows;
    totals.value = res.data.totals;
  } catch (err) {
    console.error('Error fetching Cash Flow:', err);
  }
};

onMounted(fetchReport);

const goBack = () => window.history.back();

// --- Exports ---
const flattenAccounts = (accounts) => {
  let rows = [];
  accounts.forEach(acc => {
    rows.push({
      Description: acc.account_name,
      'Opening Balance': acc.opening_balance,
      'Period Movement': acc.movement,
      'Closing Balance': acc.closing_balance
    });
    if (acc.children && acc.children.length) {
      rows = rows.concat(flattenAccounts(acc.children));
    }
  });
  return rows;
};

const exportExcel = () => {
  const data = [
    ...flattenAccounts(inflows.value),
    ...flattenAccounts(outflows.value),
    { Description: 'Net Cash Flow', 'Opening Balance': totals.value.net.opening_balance, 'Period Movement': totals.value.net.movement, 'Closing Balance': totals.value.net.closing_balance }
  ];
  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Cash Flow');
  XLSX.writeFile(wb, 'CashFlow_Statement.xlsx');
};

const exportPDF = () => {
  const doc = new jsPDF();
  doc.text(reportTitle.value, 14, 20);
  const rows = [
    ...flattenAccounts(inflows.value).map(r => [r.Description, r['Opening Balance'], r['Period Movement'], r['Closing Balance']]),
    ...flattenAccounts(outflows.value).map(r => [r.Description, r['Opening Balance'], r['Period Movement'], r['Closing Balance']]),
    ['Net Cash Flow', totals.value.net.opening_balance, totals.value.net.movement, totals.value.net.closing_balance]
  ];
  doc.autoTable({ startY: 30, head: [['Description', 'Opening', 'Movement', 'Closing']], body: rows });
  doc.save('CashFlow_Statement.pdf');
};
</script>

<style scoped>
table { border-collapse: collapse; }
th, td { text-align: left; }
</style>
