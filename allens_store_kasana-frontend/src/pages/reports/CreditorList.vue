<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">{{ reportTitle }}</h1>

    <!-- Back and Search -->
    <div class="flex items-center gap-2 mb-4">
      <button
        @click="$router.push('/reports')"
        class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
      >
        Back to Reports
      </button>

      <input
        v-model="search"
        type="text"
        placeholder="Search supplier..."
        class="border border-gray-300 rounded p-2 w-64 focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
      />
    </div>

    <!-- Supplier Table -->
    <table class="min-w-full border border-gray-200 rounded shadow">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border-b">#</th>
          <th class="p-2 border-b text-left">Supplier Name</th>
          <th class="p-2 border-b text-left">Contact</th>
          <th class="p-2 border-b text-right">Outstanding Balance (UGX)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(supplier, index) in reportData" :key="supplier.supplier_id">
          <td class="p-2 border-b text-center">{{ (page - 1) * pageSize + index + 1 }}</td>
          <td class="p-2 border-b">{{ supplier.name }}</td>
          <td class="p-2 border-b">{{ supplier.contact || '-' }}</td>
          <td class="p-2 border-b text-right">{{ formatCurrency(supplier.total_balance) }}</td>
        </tr>

        <tr v-if="reportData.length === 0">
          <td class="p-2 border-b text-center" colspan="4">No data available.</td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination Controls -->
    <div class="flex justify-between items-center mt-4">
      <div>
        Page {{ page }} of {{ totalPages }}
      </div>
      <div class="flex gap-2">
        <button
          @click="prevPage"
          :disabled="page === 1"
          class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
        >
          Prev
        </button>
        <button
          @click="nextPage"
          :disabled="page === totalPages"
          class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import api from '@/api';

const reportTitle = ref('Creditor Aging Report');
const reportData = ref([]);
const page = ref(1);
const pageSize = ref(10);
const totalPages = ref(1);
const search = ref('');

// --- Fetch data from server-side API ---
const fetchReport = async () => {
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      as_of: new Date().toISOString().split('T')[0],
      search: search.value || undefined
    };
    const res = await api.get('/reports/creditors-aging', { params });
    reportData.value = res.data.report || [];
    totalPages.value = res.data.total_pages || 1;
  } catch (err) {
    console.error('Error fetching creditors aging report:', err);
  }
};

// --- Pagination ---
const prevPage = () => {
  if (page.value > 1) page.value--;
};
const nextPage = () => {
  if (page.value < totalPages.value) page.value++;
};

// --- Watchers to reload data ---
watch([page, search], fetchReport);

onMounted(fetchReport);

// --- Format currency ---
const formatCurrency = (value) => {
  return value?.toLocaleString('en-US', { style: 'currency', currency: 'UGX' }) || '0';
};
</script>

<style scoped>
table {
  border-collapse: collapse;
}
th,
td {
  text-align: left;
}
td:last-child,
th:last-child {
  text-align: right;
}
</style>
