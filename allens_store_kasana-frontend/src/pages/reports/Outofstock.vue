<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">Out of Stock Report</h1>
    <button @click="$router.push('/reports')" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
        Back to Reports
      </button>
    <!-- Export Buttons -->
    <div class="mb-4 space-x-2">
      <button @click="exportExcel" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
        Export Excel
      </button>
      <button @click="exportPDF" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
        Export PDF
      </button>
    </div>

    <table class="min-w-full border border-gray-200 rounded shadow">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border-b">#</th>
          <th class="p-2 border-b text-left">Product Name</th>
          <th class="p-2 border-b text-left">SKU</th>
          <th class="p-2 border-b text-left">Category</th>
          <th class="p-2 border-b text-left">Current Stock</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in outOfStockProducts" :key="item.id">
          <td class="p-2 border-b text-center">{{ index + 1 }}</td>
          <td class="p-2 border-b">{{ item.name }}</td>
          <td class="p-2 border-b">{{ item.sku }}</td>
          <td class="p-2 border-b">{{ item.category_name }}</td>
          <td class="p-2 border-b text-red-600 font-bold">{{ item.quantity }}</td>
        </tr>
        <tr v-if="outOfStockProducts.length === 0">
          <td class="p-2 border-b text-center" colspan="5">No products are out of stock.</td>
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

const outOfStockProducts = ref([]);

const fetchOutOfStock = async () => {
  try {
    const res = await api.get('/reports/out-of-stock');
    outOfStockProducts.value = res.data;
  } catch (err) {
    console.error('Error fetching out-of-stock products:', err);
  }
};

// ---------- Export Functions ----------
const exportExcel = () => {
  const ws = XLSX.utils.json_to_sheet(
    outOfStockProducts.value.map((item, idx) => ({
      '#': idx + 1,
      'Product Name': item.name,
      'SKU': item.sku,
      'Category': item.category_name,
      'Current Stock': item.quantity
    }))
  );
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'OutOfStock');
  XLSX.writeFile(wb, 'OutOfStock.xlsx');
};

const exportPDF = () => {
  const doc = new jsPDF();
  doc.text('Out of Stock Report', 14, 20);
  doc.autoTable({
    startY: 30,
    head: [['#', 'Product Name', 'SKU', 'Category', 'Current Stock']],
    body: outOfStockProducts.value.map((item, idx) => [
      idx + 1,
      item.name,
      item.sku,
      item.category_name,
      item.quantity
    ])
  });
  doc.save('OutOfStock.pdf');
};

onMounted(() => {
  fetchOutOfStock();
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
