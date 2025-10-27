<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">{{ reportTitle }}</h1>
    <button @click="$router.push('/reports')" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
        Back to Reports
      </button>
    <!-- Export Buttons -->
    <div class="mb-4 space-x-2">
      <button @click="exportExcel" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">Export Excel</button>
      <button @click="exportPDF" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Export PDF</button>
    </div>

    <!-- Table -->
    <table class="min-w-full border border-gray-200 rounded shadow">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border-b">#</th>
          <th class="p-2 border-b text-left">Name / Description</th>
          <th class="p-2 border-b text-left">Other Info</th>
          <th class="p-2 border-b text-left">Amount / Qty</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in reportData" :key="item.id">
          <td class="p-2 border-b text-center">{{ index + 1 }}</td>
          <td class="p-2 border-b">{{ item.name || item.description }}</td>
          <td class="p-2 border-b">{{ item.category_name || item.info || '-' }}</td>
          <td class="p-2 border-b">{{ item.quantity || item.amount || '-' }}</td>
        </tr>
        <tr v-if="reportData.length === 0">
          <td class="p-2 border-b text-center" colspan="4">No data available.</td>
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

const reportData = ref([]);
const reportTitle = ref('Stock List');
const endpoint = ref('/reports/stock-list');

const fetchReport = async () => {
  try {
    const res = await api.get(endpoint.value);
    reportData.value = res.data;
  } catch (err) {
    console.error(`Error fetching ${reportTitle.value}:`, err);
  }
};

const exportExcel = () => {
  const ws = XLSX.utils.json_to_sheet(reportData.value.map((item, idx) => ({
    '#': idx + 1,
    Name: item.name,
    Category: item.category_name,
    Quantity: item.quantity
  })));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'StockList');
  XLSX.writeFile(wb, 'StockList.xlsx');
};

const exportPDF = () => {
  const doc = new jsPDF();
  doc.text(reportTitle.value, 14, 20);
  doc.autoTable({
    startY: 30,
    head: [['#', 'Name', 'Category', 'Quantity']],
    body: reportData.value.map((item, idx) => [
      idx + 1,
      item.name,
      item.category_name,
      item.quantity
    ])
  });
  doc.save('StockList.pdf');
};

onMounted(() => {
  fetchReport();
});
</script>

<style scoped>
table {
  border-collapse: collapse;
}
th, td {
  text-align: left;
}
</style>
