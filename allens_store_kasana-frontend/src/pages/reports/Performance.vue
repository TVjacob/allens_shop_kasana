<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">{{ reportTitle }}</h1>

    <div class="mb-4 flex justify-between items-center">
      <div>
        <button @click="goBack" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2">
          Back
        </button>
      </div>
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
          <th class="p-2 border-b">#</th>
          <th class="p-2 border-b text-left">Product Name</th>
          <th class="p-2 border-b text-left">Total Revenue</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in reportData" :key="item.product_id">
          <td class="p-2 border-b text-center">{{ index + 1 }}</td>
          <td class="p-2 border-b">{{ item.product_name }}</td>
          <td class="p-2 border-b">{{ item.total_revenue.toFixed(2) }}</td>
        </tr>
        <tr v-if="reportData.length === 0">
          <td class="p-2 border-b text-center" colspan="3">No data available.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '@/api'; // Axios instance
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const reportData = ref([]);
const reportTitle = ref('Performance Report');
const endpoint = ref('/reports/performance-list');

// Fetch report data
const fetchReport = async () => {
  try {
    const res = await api.get(endpoint.value);
    reportData.value = res.data;
  } catch (err) {
    console.error(`Error fetching ${reportTitle.value}:`, err);
  }
};

// Back button
const goBack = () => {
  window.history.back();
};

// Export to Excel
const exportExcel = () => {
  const ws = XLSX.utils.json_to_sheet(reportData.value.map((r, i) => ({
    '#': i + 1,
    'Product Name': r.product_name,
    'Total Revenue': r.total_revenue.toFixed(2),
  })));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Performance Report');
  XLSX.writeFile(wb, 'Performance_Report.xlsx');
};

// Export to PDF
const exportPDF = () => {
  const doc = new jsPDF();
  doc.text(reportTitle.value, 14, 20);
  const rows = reportData.value.map((r, i) => [i + 1, r.product_name, r.total_revenue.toFixed(2)]);
  doc.autoTable({
    startY: 30,
    head: [['#', 'Product Name', 'Total Revenue']],
    body: rows,
  });
  doc.save('Performance_Report.pdf');
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
