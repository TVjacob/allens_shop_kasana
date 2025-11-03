<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Purchase Orders</h1>

    <!-- Tabs -->
    <div class="flex space-x-4 mb-6">
      <button
        :class="currentTab === 'paid' ? activeTabClass : inactiveTabClass"
        @click="currentTab = 'paid'"
      >
        Paid Invoices
      </button>
      <button
        :class="currentTab === 'unpaid' ? activeTabClass : inactiveTabClass"
        @click="currentTab = 'unpaid'"
      >
        Unpaid Invoices
      </button>
    </div>

    <!-- Export Buttons -->
    <div class="flex space-x-2 mb-4">
      <button @click="exportCSV" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded shadow transition transform hover:scale-105">
        Export CSV
      </button>
      <button @click="exportPDF" class="px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded shadow transition transform hover:scale-105">
        Export PDF
      </button>
    </div>

    <!-- Purchase Orders Table -->
    <div class="overflow-x-auto border rounded-lg shadow-lg">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-3 border-b text-left">PO ID</th>
            <th class="p-3 border-b text-left">Supplier</th>
            <th class="p-3 border-b text-left">Invoice Number</th>
            <th class="p-3 border-b text-left">Purchase Date</th>
            <th class="p-3 border-b text-right">Total Amount</th>
            <th class="p-3 border-b text-right">Paid</th>
            <th class="p-3 border-b text-right">Balance</th>
            <th class="p-3 border-b text-center">Status</th>
            <th class="p-3 border-b text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="po in filteredPurchaseOrders"
            :key="po.id"
            class="hover:bg-gray-50 cursor-pointer transition-all duration-300 ease-in-out transform hover:scale-[1.01]"
          >
            <td class="p-3 border">{{ po.id }}</td>
            <td class="p-3 border">{{ po.supplier_name }}</td>
            <td class="p-3 border">{{ po.invoice_number }}</td>
            <td class="p-3 border">{{ formatDate(po.purchase_date) }}</td>
            <td class="p-3 border text-right">{{ formatPrice(po.total_amount) }}</td>
            <td class="p-3 border text-right">{{ formatPrice(po.total_paid) }}</td>
            <td class="p-3 border text-right">{{ formatPrice(po.total_balance) }}</td>
            <td class="p-3 border text-center">
              <span
                :class="po.total_balance === 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold'"
              >
                {{ po.total_balance === 0 ? 'Paid' : 'Unpaid' }}
              </span>
            </td>
            <td class="p-3 border text-center space-x-2">
              <button
                v-if="po.total_balance > 0"
                @click="openPaymentModal(po)"
                class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded shadow transition transform hover:scale-105"
              >
                Make Payment
              </button>
              <router-link
                :to="`/purchase-orders/${po.id}/edit`"
                class="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded shadow transition transform hover:scale-105"
              >
                Edit
              </router-link>
              <router-link
                :to="`/purchase-orders/${po.id}`"
                class="text-indigo-600 underline hover:text-indigo-800 transition"
              >
                View
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Payment Modal -->
    <PaymentPurchaseModal
      v-model:modelValue="showPaymentModal"
      :po="selectedPO"
      :accounts="accounts"
      @saved="refreshPurchaseOrders"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../api';
import PaymentPurchaseModal from './PaymentPurchaseModal.vue';

const currentTab = ref('unpaid');
const purchaseOrders = ref([]);
const accounts = ref([]);
const showPaymentModal = ref(false);
const selectedPO = ref(null);

const activeTabClass = 'px-4 py-2 rounded bg-indigo-600 text-white transition transform hover:scale-105';
const inactiveTabClass = 'px-4 py-2 rounded bg-gray-200 text-gray-700 transition transform hover:scale-105';

const fetchPurchaseOrders = async () => {
  try {
    const res = await api.get('/suppliers/orders');
    purchaseOrders.value = res.data;
  } catch (err) {
    console.error(err);
  }
};

const fetchAccounts = async () => {
  try {
    const res = await api.get('/accounts/cash-bank');
    accounts.value = res.data;
  } catch (err) {
    console.error(err);
  }
};

const filteredPurchaseOrders = computed(() => {
  return currentTab.value === 'paid'
    ? purchaseOrders.value.filter(po => po.total_balance === 0)
    : purchaseOrders.value.filter(po => po.total_balance > 0);
});

const formatDate = dateStr => new Date(dateStr).toLocaleDateString();

const openPaymentModal = po => {
  selectedPO.value = po;
  showPaymentModal.value = true;
};
const formatPrice = (value) => (value == null ? '0' : new Intl.NumberFormat('en-UG').format(value))

const refreshPurchaseOrders = () => fetchPurchaseOrders();

// Export placeholders
const exportCSV = () => alert('CSV export not implemented yet!');
const exportPDF = () => alert('PDF export not implemented yet!');

onMounted(() => {
  fetchPurchaseOrders();
  fetchAccounts();
});
</script>

<style scoped>
/* Fade-in animation for header */
@keyframes fadeIn {
  0% { opacity: 0; transform: translateY(-10px);}
  100% { opacity: 1; transform: translateY(0);}
}
.animate-fadeIn {
  animation: fadeIn 0.5s ease-in-out forwards;
}

/* Table hover shadow */
tbody tr:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

/* Smooth button hover */
button, a {
  transition: all 0.3s ease-in-out;
}
</style>
