<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">General Ledger Report</h1>

    <!-- Filters -->
    <div class="flex flex-col md:flex-row gap-4 mb-6 items-end">

      <div>
        <label class="block font-semibold mb-1">Start Date</label>
        <input
          type="date"
          v-model="startDate"
          class="border p-2 rounded w-full focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>
      <div>
        <label class="block font-semibold mb-1">End Date</label>
        <input
          type="date"
          v-model="endDate"
          class="border p-2 rounded w-full focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>
      <div class="flex-1">
        <label class="block font-semibold mb-1">Search</label>
        <input
          type="text"
          v-model="search"
          placeholder="Account or description"
          class="border p-2 rounded w-full focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>
      <button
        @click="fetchReport"
        class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded transition"
      >
        Filter
      </button>
    </div>

    <!-- Export Buttons -->
         <button @click="$router.push('/reports')" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
        Back to Reports
      </button>
    <!-- Export Bu -->
    <div class="flex justify-end gap-2 mb-4">
      <button @click="exportExcel" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">Export Excel</button>
      <button @click="exportPDF" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">Export PDF</button>
    </div>

    <!-- Report Cards / Table -->
    <div class="overflow-x-auto">
      <table class="min-w-full border border-gray-200 rounded shadow">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-2 border-b text-center">#</th>
            <th class="p-2 border-b text-left">Account</th>
            <th class="p-2 border-b text-left">Category</th>
            <th class="p-2 border-b text-left">Subcategory</th>
            <th class="p-2 border-b text-right">Debit</th>
            <th class="p-2 border-b text-right">Credit</th>
            <th class="p-2 border-b text-left">Date</th>
            <th class="p-2 border-b text-left">Description</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in reportData" :key="item.id">
            <td class="p-2 border-b text-center">{{ index + 1 }}</td>
            <td class="p-2 border-b">{{ item.account_name }}</td>
            <td class="p-2 border-b">{{ item.account_type }}</td>
            <td class="p-2 border-b">{{ item.account_subtype || '-' }}</td>
            <td class="p-2 border-b text-right">{{ item.transaction_type === 'Debit' ? item.amount.toFixed(2) : '-' }}</td>
            <td class="p-2 border-b text-right">{{ item.transaction_type === 'Credit' ? item.amount.toFixed(2) : '-' }}</td>
            <td class="p-2 border-b">{{ item.transaction_date }}</td>
            <td class="p-2 border-b">{{ item.description || '-' }}</td>
          </tr>
          <tr class="font-bold bg-gray-50">
            <td class="p-2 border-b text-center" colspan="4">Totals</td>
            <td class="p-2 border-b text-right">{{ totalDebit.toFixed(2) }}</td>
            <td class="p-2 border-b text-right">{{ totalCredit.toFixed(2) }}</td>
            <td class="p-2 border-b" colspan="2"></td>
          </tr>
          <tr v-if="reportData.length === 0">
            <td class="p-2 border-b text-center" colspan="8">No data available.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex justify-center items-center gap-2 mt-6">
      <button
        @click="prevPage"
        :disabled="page === 1"
        class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
      >
        Prev
      </button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button
        @click="nextPage"
        :disabled="page === totalPages"
        class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import api from '@/api';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const reportData = ref([]);
const page = ref(1);
const pageSize = ref(20);
const totalPages = ref(1);
const totalRecords = ref(0);

const startDate = ref('');
const endDate = ref('');
const search = ref('');

// Fetch report
const fetchReport = async () => {
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
      search: search.value || undefined
    };
    const res = await api.get('/reports/general-ledger', { params });
    reportData.value = res.data.data.map(item => ({ ...item, amount: Number(item.amount) }));
    totalPages.value = res.data.total_pages;
    totalRecords.value = res.data.total_records;
  } catch (err) {
    console.error('Error fetching report:', err);
  }
};

// Pagination methods
const prevPage = () => {
  if (page.value > 1) {
    page.value--;
    fetchReport();
  }
};
const nextPage = () => {
  if (page.value < totalPages.value) {
    page.value++;
    fetchReport();
  }
};

// Totals
const totalDebit = computed(() => reportData.value.reduce((sum, r) => r.transaction_type === 'Debit' ? sum + r.amount : sum, 0));
const totalCredit = computed(() => reportData.value.reduce((sum, r) => r.transaction_type === 'Credit' ? sum + r.amount : sum, 0));

// Export Excel
const exportExcel = () => {
  const ws = XLSX.utils.json_to_sheet(reportData.value.map((r, i) => ({
    '#': i + 1,
    'Account': r.account_name,
    'Category': r.account_type,
    'Subcategory': r.account_subtype || '',
    'Debit': r.transaction_type === 'Debit' ? r.amount.toFixed(2) : '',
    'Credit': r.transaction_type === 'Credit' ? r.amount.toFixed(2) : '',
    'Date': r.transaction_date,
    'Description': r.description
  })));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'General Ledger');
  XLSX.writeFile(wb, 'General_Ledger.xlsx');
};

// Export PDF
const exportPDF = () => {
  const doc = new jsPDF('p', 'pt', 'a4');
  const title = 'General Ledger Report';
  doc.setFontSize(14);
  doc.text(title, 40, 40);
  
  // Add date range info
  let dateRange = `From: ${startDate.value || '-'}  To: ${endDate.value || '-'}`;
  doc.setFontSize(10);
  doc.text(dateRange, 40, 60);

  // Prepare rows
  const rows = reportData.value.map((r, i) => [
    i + 1,
    r.account_name,
    r.account_type,
    r.account_subtype || '',
    r.transaction_type === 'Debit' ? r.amount.toFixed(2) : '-',
    r.transaction_type === 'Credit' ? r.amount.toFixed(2) : '-',
    r.transaction_date,
    r.description || '-'
  ]);

  // Totals row
  const totalsRow = ['Totals', '', '', '', totalDebit.value.toFixed(2), totalCredit.value.toFixed(2), '', ''];
  rows.push(totalsRow);

  doc.autoTable({
    startY: 80,
    head: [['#', 'Account', 'Category', 'Subcategory', 'Debit', 'Credit', 'Date', 'Description']],
    body: rows,
    styles: { fontSize: 9, cellPadding: 4 },
    headStyles: { fillColor: [99, 102, 241] },
    alternateRowStyles: { fillColor: [245, 245, 245] },
  });

  doc.save('General_Ledger.pdf');
};

// Initial fetch
fetchReport();
</script>

<style scoped>
/* Modern card-style table for printing */
body {
  font-family: 'Inter', sans-serif;
}
table {
  border-collapse: collapse;
}
th, td {
  text-align: left;
}
th {
  background-color: #f3f4f6;
}
</style>
