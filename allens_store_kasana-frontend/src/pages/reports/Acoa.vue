<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">Chart of Accounts Report</h1>

    <div class="mb-4 flex justify-between items-center">
      <button @click="$router.push('/reports')" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
        Back to Reports
      </button>
      <div class="space-x-2">
        <button @click="exportExcel" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
          Export Excel
        </button>
        <button @click="exportPDF" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
          Export PDF
        </button>
      </div>
    </div>

    <table class="min-w-full border border-gray-200 rounded shadow">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border-b">#</th>
          <th class="p-2 border-b text-left">Account Name</th>
          <th class="p-2 border-b text-left">Code</th>
          <th class="p-2 border-b text-left">Subtype</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="group in groupedAccounts" :key="group.name">
          <!-- Group Header -->
          <tr class="bg-gray-200 font-bold">
            <td class="p-2 border-b text-center" colspan="4">
              {{ group.name }} - Total Accounts: {{ group.total }}
            </td>
          </tr>
          <!-- Account Rows -->
          <AccountRow
            v-for="acc in group.accounts"
            :key="acc.id"
            :account="acc"
            :level="0"
            :counter="counter"
          />
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api';
import AccountRow from './AccountRow.vue';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

// ------------------- Counter -------------------
class Counter {
  constructor() { this.value = 0; }
  next() { this.value += 1; return this.value; }
}
const counter = new Counter();

// ------------------- Data -------------------
const accounts = ref([]);
const groupedAccounts = ref([]);

// ------------------- Fetch Chart of Accounts -------------------
const fetchChart = async () => {
  try {
    const res = await api.get('/accounts/chart');
    accounts.value = res.data;
    groupAccounts();
  } catch (err) {
    console.error('Error fetching chart of accounts:', err);
  }
};

// ------------------- Group Accounts -------------------
const groupAccounts = () => {
  const groups = {};
  accounts.value.forEach(acc => {
    const type = acc.account_type || 'OTHER';
    if (!groups[type]) groups[type] = { name: type, accounts: [], total: 0 };
    groups[type].accounts.push(acc);
    groups[type].total += 1 + countChildren(acc);
  });
  groupedAccounts.value = Object.values(groups);
};

const countChildren = (acc) => {
  if (!acc.children || !acc.children.length) return 0;
  return acc.children.reduce((sum, c) => 1 + countChildren(c), 0);
};

// ------------------- Export Excel -------------------
const exportExcel = () => {
  const flatData = [];
  groupedAccounts.value.forEach(group => {
    flatData.push({
      'Account Name': `${group.name} - Total Accounts: ${group.total}`,
      'Code': '',
      'Subtype': ''
    });
    const addAccounts = (acc, level = 0) => {
      flatData.push({
        'Account Name': ' '.repeat(level * 2) + acc.name,
        'Code': acc.code,
        'Subtype': acc.account_subtype || '-'
      });
      acc.children?.forEach(c => addAccounts(c, level + 1));
    };
    group.accounts.forEach(acc => addAccounts(acc));
  });

  const ws = XLSX.utils.json_to_sheet(flatData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Chart of Accounts');
  XLSX.writeFile(wb, 'Chart_of_Accounts.xlsx');
};

// ------------------- Export PDF -------------------
const exportPDF = () => {
  const doc = new jsPDF();
  doc.setFontSize(16);
  doc.text('Chart of Accounts Report', 14, 20);

  const rows = [];
  groupedAccounts.value.forEach(group => {
    rows.push([{ content: `${group.name} - Total Accounts: ${group.total}`, colSpan: 3, styles: { halign: 'center', fillColor: [220, 220, 220] } }]);
    const addAccounts = (acc, level = 0) => {
      rows.push([
        ' '.repeat(level * 2) + acc.name,
        acc.code,
        acc.account_subtype || '-'
      ]);
      acc.children?.forEach(c => addAccounts(c, level + 1));
    };
    group.accounts.forEach(acc => addAccounts(acc));
  });

  doc.autoTable({
    startY: 30,
    head: [['Account Name', 'Code', 'Subtype']],
    body: rows,
    theme: 'grid',
    headStyles: { fillColor: [240, 240, 240] },
    styles: { fontSize: 10 }
  });

  doc.save('Chart_of_Accounts.pdf');
};

onMounted(fetchChart);
</script>

<style scoped>
table {
  border-collapse: collapse;
}
th, td {
  text-align: left;
}
tr.bg-gray-200 {
  background-color: #f3f4f6;
}
</style>
