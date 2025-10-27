<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">Consumption Report (Last 7 Days)</h1>

    <!-- Back & Export Buttons -->
    <div class="mb-4 space-x-2">
      <button @click="$router.push('/reports')" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
        Back to Reports
      </button>
      <button @click="exportExcel" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
        Export Excel
      </button>
      <button @click="exportPDF" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
        Export PDF
      </button>
    </div>

    <!-- Consumption Table -->
    <table class="min-w-full border border-gray-200 rounded shadow">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border-b">#</th>
          <th class="p-2 border-b text-left">Product Name</th>
          <th class="p-2 border-b text-left">Quantity Sold</th>
          <th class="p-2 border-b text-left">Total Amount</th>
          <th class="p-2 border-b text-left">Sale Date</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in reportData" :key="item.id">
          <td class="p-2 border-b text-center">{{ index + 1 }}</td>
          <td class="p-2 border-b">{{ item.product_name }}</td>
          <td class="p-2 border-b">{{ item.quantity_sold }}</td>
          <td class="p-2 border-b">{{ item.total_amount }}</td>
          <td class="p-2 border-b">{{ item.sale_date }}</td>
        </tr>
        <tr v-if="reportData.length === 0">
          <td class="p-2 border-b text-center" colspan="5">No consumption data available.</td>
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

const fetchReport = async () => {
  try {
    const res = await api.get('/reports/consumption-list');
    reportData.value = res.data;
  } catch (err) {
    console.error('Error fetching consumption report:', err);
  }
};

// ---------- Export Functions ----------
const exportExcel = () => {
  const ws = XLSX.utils.json_to_sheet(
    reportData.value.map((item, idx) => ({
      '#': idx + 1,
      'Product Name': item.product_name,
      'Quantity Sold': item.quantity_sold,
      'Total Amount': item.total_amount,
      'Sale Date': item.sale_date
    }))
  );
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Consumption');
  XLSX.writeFile(wb, 'Consumption_Report.xlsx');
};

const exportPDF = () => {
  const doc = new jsPDF();
  doc.text('Consumption Report (Last 7 Days)', 14, 20);
  doc.autoTable({
    startY: 30,
    head: [['#', 'Product Name', 'Quantity Sold', 'Total Amount', 'Sale Date']],
    body: reportData.value.map((item, idx) => [
      idx + 1,
      item.product_name,
      item.quantity_sold,
      item.total_amount,
      item.sale_date
    ])
  });
  doc.save('Consumption_Report.pdf');
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
