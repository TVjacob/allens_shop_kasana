<template>
    <div class="p-6">
      <h1 class="text-2xl font-bold mb-6">{{ reportTitle }}</h1>
      <button @click="$router.push('/reports')" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
        Back to Reports
      </button>
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
            <td class="p-2 border-b">{{ item.info || '-' }}</td>
            <td class="p-2 border-b">{{ item.amount || item.qty || '-' }}</td>
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
  import api from '@/api'; // Axios instance
  
  const reportData = ref([]);
  const reportTitle = ref('Report Title Here'); // Change per report
  const endpoint = ref('/reports/default'); // Change per report
  
  const fetchReport = async () => {
    try {
      const res = await api.get(endpoint.value);
      reportData.value = res.data;
    } catch (err) {
      console.error(`Error fetching ${reportTitle.value}:`, err);
    }
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
  