<template>
  <div class="p-6 max-w-7xl mx-auto bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Sales List</h1>

    <!-- 🔹 Tabs + Search -->
    <div class="flex flex-wrap gap-2 mb-6 items-center">
      <button
        :class="currentTab === 'paid' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'"
        class="px-4 py-2 rounded-lg font-medium transition hover:bg-indigo-500"
        @click="currentTab = 'paid'"
      >
        Paid Sales
      </button>
      <button
        :class="currentTab === 'unpaid' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-700'"
        class="px-4 py-2 rounded-lg font-medium transition hover:bg-indigo-500"
        @click="currentTab = 'unpaid'"
      >
        Unpaid Sales
      </button>

      <input
        v-model="searchQuery"
        placeholder="🔍 Search by sale number or ID"
        class="ml-auto px-3 py-2 border rounded-lg w-64 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />
    </div>

    <!-- 🔹 Sales Table -->
    <div class="overflow-x-auto bg-white rounded-xl shadow-lg border">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100 text-gray-700 sticky top-0">
          <tr>
            <th class="p-3 border-b text-left">Sale ID</th>
            <th class="p-3 border-b text-left">Customer</th>
            <th class="p-3 border-b text-left">Sale Number</th>
            <th class="p-3 border-b text-left">Sale Date</th>
            <th class="p-3 border-b text-right">Total Amount</th>
            <th class="p-3 border-b text-right">Paid</th>
            <th class="p-3 border-b text-right">Balance</th>
            <th class="p-3 border-b text-center">Status</th>
            <th class="p-3 border-b text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="sale in filteredSales"
            :key="sale.id"
            class="hover:bg-gray-50 transition cursor-pointer"
          >
            <td class="p-2 border">{{ sale.sale_id }}</td>
            <td class="p-2 border">{{ sale.customer.name }}</td>
            <td class="p-2 border">{{ sale.sale_number }}</td>
            <td class="p-2 border">{{ formatDate(sale.sale_date) }}</td>
            <td class="p-2 border text-right">{{ formatCurrency(sale.total_amount) }}</td>
            <td class="p-2 border text-right">{{ formatCurrency(sale.total_paid || 0) }}</td>
            <td
              class="p-2 border text-right font-semibold"
              :class="sale.balance <= 0 ? 'text-green-600' : 'text-red-600'"
            >
              {{ formatCurrency(sale.balance) }}
            </td>
            <td class="p-2 border text-center">
              <span
                :class="sale.balance <= 0 ? 'bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm' : 'bg-red-100 text-red-800 px-2 py-1 rounded-full text-sm'"
              >
                {{ sale.balance <= 0 ? 'Paid' : 'Unpaid' }}
              </span>
            </td>
            <td class="p-2 border text-center flex justify-center gap-2">
              <button
                v-if="sale.balance > 0"
                @click="openPaymentModal(sale)"
                class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg transition"
              >
                Receive Payment
              </button>
              <button
                @click="previewPaymentReport(sale.sale_id)"
                class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg transition"
              >
                View Report
              </button>
              <button
                @click="confirmDeleteSale(sale)"
                class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg transition"
              >
                Delete
              </button>
            </td>
          </tr>

          <tr v-if="filteredSales.length === 0">
            <td colspan="9" class="p-4 text-center text-gray-500">
              No sales found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 🔹 Modals -->
    <PaymentModal
      v-if="showPaymentModal"
      :sale="selectedSale"
      :accounts="accounts"
      v-model:modelValue="showPaymentModal"
      @saved="fetchSales"
    />

    <ReportModal
      v-if="showReportModal"
      :report="paymentReport"
      v-model:show="showReportModal"
    />

    <!-- 🔹 Toast -->
    <div
      v-if="toast.visible"
      class="fixed bottom-6 right-6 bg-gray-800 text-white px-4 py-2 rounded-lg shadow-lg animate-fade-in"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api';
import PaymentModal from './PaymentModal.vue';
import ReportModal from './ReportModal.vue';

const currentTab = ref('unpaid');
const sales = ref([]);
const accounts = ref([]);
const searchQuery = ref('');

// Modals
const showPaymentModal = ref(false);
const selectedSale = ref(null);
const showReportModal = ref(false);
const paymentReport = ref(null);

// Toast
const toast = ref({ visible: false, message: '' });
const showToast = (msg) => {
  toast.value = { visible: true, message: msg };
  setTimeout(() => (toast.value.visible = false), 3000);
};

// Fetch sales
const fetchSales = async () => {
  try {
    const res = await api.get('/sales/');
    sales.value = res.data.map(s => ({ ...s, balance: s.balance }));
  } catch (err) {
    console.error(err);
  }
};

// Fetch accounts
const fetchAccounts = async () => {
  try {
    const res = await api.get('/accounts/cash-bank');
    accounts.value = res.data;
  } catch (err) {
    console.error(err);
  }
};

// Filtered sales + search
const filteredSales = computed(() => {
  return sales.value
    .filter(s => currentTab.value === 'paid' ? s.balance <= 0 : s.balance > 0)
    .filter(s =>
      s.sale_number.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      s.sale_id.toString().includes(searchQuery.value)
    );
});

// Helpers
const formatDate = dateStr => new Date(dateStr).toLocaleDateString();
const formatCurrency = val => Number(val).toLocaleString(undefined, { style: 'currency', currency: 'UGX' });

// Modals
const openPaymentModal = sale => {
  selectedSale.value = sale;
  showPaymentModal.value = true;
};
const previewPaymentReport = async saleId => {
  try {
    const res = await api.get(`/payments/details?sale_id=${saleId}&type=invoice`);
    paymentReport.value = res.data;
    showReportModal.value = true;
  } catch (err) {
    console.error(err);
  }
};

// 🔹 Confirm & Delete Sale
const confirmDeleteSale = async (sale) => {
  if (!confirm(`Are you sure you want to delete sale ${sale.sale_number}? This will reverse all related entries.`)) {
    return;
  }
  try {
    await api.delete(`/sales/${sale.sale_id}/delete`);
    showToast(`✅ Sale ${sale.sale_number} deleted & reversed successfully`);
    await fetchSales();
  } catch (err) {
    console.error(err);
    showToast(`❌ Error deleting sale: ${err.response?.data?.error || err.message}`);
  }
};

onMounted(() => {
  fetchSales();
  fetchAccounts();
});
</script>

<style scoped>
.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
  transition: background-color 0.2s;
}
.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
