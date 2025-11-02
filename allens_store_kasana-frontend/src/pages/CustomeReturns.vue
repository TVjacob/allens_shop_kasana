<template>
  <div class="p-6 max-w-7xl mx-auto bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Crates & Bottles Summary</h1>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2 mb-6 items-center">
      <input
        v-model="searchQuery"
        placeholder="🔍 Search by customer, product, or type"
        class="ml-auto px-3 py-2 border rounded-lg w-64 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />
      <button
        class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium transition hover:bg-indigo-500"
        @click="fetchSummary"
      >
        Refresh
      </button>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto bg-white rounded-xl shadow-lg border">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100 text-gray-700 sticky top-0">
          <tr>
            <th class="p-3 border-b text-left">Customer</th>
            <th class="p-3 border-b text-left">Type</th>
            <th class="p-3 border-b text-left">Product</th>
            <th class="p-3 border-b text-left">Category</th>

            <!-- <th class="p-3 border-b text-left">Container</th> -->
            <th class="p-3 border-b text-left">Unit</th>
            <th class="p-3 border-b text-right">Issued</th>
            <th class="p-3 border-b text-right">Returned</th>
            <th class="p-3 border-b text-right">Sold</th>
            <th class="p-3 border-b text-right">Not Returned</th>

          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in filteredSummary"
            :key="entry.customer_id + '-' + entry.product_name + '-' + entry.type"
            class="hover:bg-gray-50 transition cursor-pointer"
          >
            <td class="p-2 border">{{ entry.customer_name }}</td>
            <td class="p-2 border">
              <span
                :class="[
                  'px-2 py-1 rounded-full text-xs font-semibold',
                  entry.type === 'Crate'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-yellow-100 text-yellow-700'
                ]"
              >
                {{ entry.type }}
              </span>
            </td>
            <td class="p-2 border">{{ entry.product_name }}</td>
            <td class="p-2 border">{{ entry.category_name || '-' }}</td>
            <td class="p-2 border">{{ entry.unit_name || '-' }}</td>
            <td class="p-2 border text-right">{{ entry.quantity_issued }}</td>
            <td class="p-2 border text-right">{{ entry.quantity_returned }}</td>
            <td class="p-2 border text-right">{{ entry.quantity_sold }}</td>

            <td
              class="p-2 border text-right font-semibold"
              :class="entry.type === 'Bottle' && entry.quantity_not_returned > 0 ? 'text-red-600' : 'text-gray-700'"
            >
              {{ entry.quantity_not_returned }}
            </td>
          </tr>

          <tr v-if="filteredSummary.length === 0">
            <td colspan="8" class="p-4 text-center text-gray-500">
              ✅ All bottles and crates have been returned.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api';

const summary = ref([]);
const searchQuery = ref('');

// Fetch crate + bottle summary
const fetchSummary = async () => {
  try {
    const res = await api.get('/sales/returnable/summary/by-customer');
    summary.value = res.data;
  } catch (err) {
    console.error('Failed to fetch returnable summary:', err);
  }
};

// Filtered list (search by customer, product, or type)
const filteredSummary = computed(() => {
  return summary.value.filter(entry =>
    entry.customer_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    entry.product_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    entry.type.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

onMounted(() => {
  fetchSummary();
});
</script>

<style scoped>
.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
  transition: background-color 0.2s;
}
</style>
