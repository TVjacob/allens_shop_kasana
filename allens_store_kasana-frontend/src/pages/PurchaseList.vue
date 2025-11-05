<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Purchase Orders</h1>

    <!-- Tabs -->
    <div class="flex space-x-4 mb-6">
      <button
        :class="currentTab === 'paid' ? activeTabClass : inactiveTabClass"
        @click="changeTab('paid')"
      >
        Paid Invoices
      </button>
      <button
        :class="currentTab === 'unpaid' ? activeTabClass : inactiveTabClass"
        @click="changeTab('unpaid')"
      >
        Unpaid Invoices
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-4 mb-4 items-center">
      <input
  v-model="productSearchQuery"
  @input="onProductSearch"
  placeholder="🔍 Search product, supplier, invoice or memo"
/>

<!-- <input type="date" v-model="startDate" />
<input type="date" v-model="endDate" /> -->


      <input
        type="date"
        v-model="startDate"
        @change="onFilterChange"
        class="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />

      <input
        type="date"
        v-model="endDate"
        @change="onFilterChange"
        class="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      />

      <button
        @click="fetchPurchaseOrders"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded shadow transition transform hover:scale-105"
      >
        Apply Filters
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
          <tr v-if="filteredPurchaseOrders.length === 0">
            <td colspan="9" class="p-4 text-center text-gray-500">
              No purchase orders found.
            </td>
          </tr>
        </tbody>

        <!-- Totals Row -->
        <tfoot class="bg-gray-100 font-bold">
          <tr>
            <td colspan="4" class="p-3 text-right border-b">Totals:</td>
            <td class="p-3 text-right border-b">{{ formatPrice(totalAmount) }}</td>
            <td class="p-3 text-right border-b">{{ formatPrice(totalPaid) }}</td>
            <td class="p-3 text-right border-b">{{ formatPrice(totalBalance) }}</td>
            <td colspan="2" class="p-3 border-b"></td>
          </tr>
        </tfoot>
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
import debounce from 'lodash.debounce';
import api from '../api';
import PaymentPurchaseModal from './PaymentPurchaseModal.vue';

const currentTab = ref('unpaid');
const purchaseOrders = ref([]);
const accounts = ref([]);
const showPaymentModal = ref(false);
const selectedPO = ref(null);

const activeTabClass = 'px-4 py-2 rounded bg-indigo-600 text-white transition transform hover:scale-105';
const inactiveTabClass = 'px-4 py-2 rounded bg-gray-200 text-gray-700 transition transform hover:scale-105';

// Filters
// Filters
const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
// const startDate = ref(today);
// const endDate = ref(today);
const productSearchQuery = ref('');
const startDate = ref(new Date().toISOString().split('T')[0]); // today
const endDate = ref(new Date().toISOString().split('T')[0]);   // today

// Fetch Data with filters
// const fetchPurchaseOrders = async () => {
//   try {
//     const params = {
//       search: searchQuery.value || undefined,
//       start_date: startDate.value || undefined,
//       end_date: endDate.value || undefined,
//     };
//     const res = await api.get('/suppliers/orders', { params });
//     purchaseOrders.value = res.data;
//   } catch (err) {
//     console.error(err);
//   }
// };
const fetchPurchaseOrders = async () => {
  const res = await api.get('/suppliers/orders', {
    params: {
      search: productSearchQuery.value, // ✅ correct variable
      start_date: startDate.value,
      end_date: endDate.value
    }
  });
  purchaseOrders.value = res.data;
};

// Tab change
const changeTab = (tab) => {
  currentTab.value = tab;
};

// Computed filtered by tab
const filteredPurchaseOrders = computed(() => {
  return currentTab.value === 'paid'
    ? purchaseOrders.value.filter(po => po.total_balance === 0)
    : purchaseOrders.value.filter(po => po.total_balance > 0);
});

// Totals
const totalAmount = computed(() =>
  filteredPurchaseOrders.value.reduce((sum, po) => sum + Number(po.total_amount || 0), 0)
);
const totalPaid = computed(() =>
  filteredPurchaseOrders.value.reduce((sum, po) => sum + Number(po.total_paid || 0), 0)
);
const totalBalance = computed(() =>
  filteredPurchaseOrders.value.reduce((sum, po) => sum + Number(po.total_balance || 0), 0)
);

// Helpers
const formatDate = dateStr => new Date(dateStr).toLocaleDateString();
const formatPrice = val => Number(val || 0).toLocaleString('en-UG');

// Actions
const openPaymentModal = po => {
  selectedPO.value = po;
  showPaymentModal.value = true;
};
const refreshPurchaseOrders = () => fetchPurchaseOrders();

// Export placeholders
const exportCSV = () => alert('CSV export not implemented yet!');
const exportPDF = () => alert('PDF export not implemented yet!');
const onProductSearch = debounce(() => {
  fetchPurchaseOrders();
}, 300);

// Trigger API call when filters change (debounced)
const onFilterChange = debounce(() => {
  fetchPurchaseOrders();
}, 500);

onMounted(() => {
  fetchPurchaseOrders();
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
