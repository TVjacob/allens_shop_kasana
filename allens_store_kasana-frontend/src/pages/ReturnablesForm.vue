<template>
  <div class="p-6 max-w-5xl mx-auto bg-white rounded-xl shadow-lg mt-6">
    <h2 class="text-2xl font-bold mb-4 text-gray-800">Return / Sell Crates & Bottles</h2>

    <!-- Customer Selector -->
    <div class="mb-4">
      <label class="block font-medium text-gray-700 mb-1">Select Customer</label>
      <select
        v-model="form.customer_id"
        class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
        @change="fetchCustomerSummary"
      >
        <option value="">-- Choose a Customer --</option>
        <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <p v-if="errors.customer_id" class="text-red-600 text-sm mt-1">{{ errors.customer_id }}</p>
    </div>

    <!-- Cash Account Selector -->
    <div class="mb-4">
      <label class="block font-medium text-gray-700 mb-1">Receive Cash To</label>
      <select
        v-model="form.cash_account_id"
        class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
      >
        <option value="">-- Choose Cash Account --</option>
        <option v-for="a in cashAccounts" :key="a.id" :value="a.id">{{ a.name }}</option>
      </select>
      <p v-if="errors.cash_account_id" class="text-red-600 text-sm mt-1">{{ errors.cash_account_id }}</p>
    </div>

    <!-- Products Pending Return / Sale -->
    <div v-if="summary.length">
      <h3 class="text-xl font-semibold mb-2">Pending Returns / Sales</h3>
      <div class="overflow-x-auto bg-gray-50 rounded-xl shadow border p-2">
        <table class="min-w-full border-collapse">
          <thead class="bg-gray-100 text-gray-700 sticky top-0">
            <tr>
              <th class="p-2 border">Product</th>
              <th class="p-2 border">Type</th>
              <th class="p-2 border text-right">Pending Quantity</th>
              <th class="p-2 border text-right">Returned Quantity</th>
              <th class="p-2 border text-right">Damaged Quantity</th>
              <th class="p-2 border text-right">Sold Quantity</th>
              <th class="p-2 border text-right">Sold Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in summary"
              :key="item.customer_id + '-' + item.product_name + '-' + item.type"
            >
              <td class="p-2 border">{{ item.product_name }}</td>
              <td class="p-2 border">{{ item.type }}</td>
              <td class="p-2 border text-right">{{ item.quantity_not_returned }}</td>

              <!-- Returned Quantity -->
              <td class="p-2 border text-right">
                <input
                  type="number"
                  v-model.number="item.returned_quantity"
                  :min="0"
                  :max="item.quantity_not_returned"
                  class="w-20 border rounded px-2 py-1 text-right focus:ring-2 focus:ring-indigo-400"
                />
              </td>

              <!-- Damaged Quantity -->
              <td class="p-2 border text-right">
                <input
                  type="number"
                  v-model.number="item.damaged_quantity"
                  :min="0"
                  :max="item.quantity_not_returned"
                  class="w-20 border rounded px-2 py-1 text-right focus:ring-2 focus:ring-indigo-400"
                />
              </td>

              <!-- Sold Quantity -->
              <td class="p-2 border text-right">
                <input
                  type="number"
                  v-model.number="item.sold_quantity"
                  :min="0"
                  :max="item.quantity_not_returned"
                  class="w-20 border rounded px-2 py-1 text-right focus:ring-2 focus:ring-indigo-400"
                />
              </td>

              <!-- Sold Amount -->
              <td class="p-2 border text-right">
                <input
                  type="number"
                  v-model.number="item.sold_amount"
                  :min="0"
                  class="w-28 border rounded px-2 py-1 text-right focus:ring-2 focus:ring-indigo-400"
                  placeholder="Enter amount"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Submit Button -->
      <button
        @click="submitReturnsAndSales"
        class="mt-4 bg-indigo-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-indigo-500 transition"
        :disabled="loading"
      >
        <span v-if="loading">Saving...</span>
        <span v-else>Save</span>
      </button>
    </div>

    <p v-else-if="form.customer_id" class="mt-4 text-gray-500">
      No pending returns or sales for this customer.
    </p>

    <!-- Snackbars -->
    <p
      v-if="successMessage"
      class="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded shadow-lg transition-all"
    >
      {{ successMessage }}
    </p>

    <p
      v-if="errorMessage"
      class="fixed bottom-16 right-4 bg-red-600 text-white px-4 py-2 rounded shadow-lg transition-all"
    >
      {{ errorMessage }}
    </p>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import api from '../api';

const customers = ref([]);
const cashAccounts = ref([]);
const summary = ref([]);
const loading = ref(false);
const successMessage = ref('');
const errorMessage = ref('');
const errors = reactive({});

const form = reactive({
  customer_id: '',
  cash_account_id: '',
});

// Fetch customers
const fetchCustomers = async () => {
  try {
    const res = await api.get('/sales/returnable/summary/by-customer');
    const data = res.data || [];
    const customerMap = {};
    data.forEach(item => {
      if (!customerMap[item.customer_id]) {
        customerMap[item.customer_id] = {
          id: item.customer_id,
          name: item.customer_name
        };
      }
    });
    customers.value = Object.values(customerMap);
  } catch (err) {
    console.error(err);
    customers.value = [];
  }
};

// Fetch cash accounts
const fetchCashAccounts = async () => {
  try {
    const res = await api.get('/accounts/cash-bank'); // endpoint returning list of cash accounts
    cashAccounts.value = res.data || [];
  } catch (err) {
    console.error(err);
    cashAccounts.value = [];
  }
};

// Fetch customer summary
const fetchCustomerSummary = async () => {
  if (!form.customer_id) return;

  loading.value = true;
  successMessage.value = '';
  errorMessage.value = '';

  try {
    const res = await api.get(`/sales/returnable/summary/customer/${form.customer_id}`);
    summary.value = res.data.map(item => ({
      ...item,
      returned_quantity: 0,
      damaged_quantity: 0,
      sold_quantity: 0,
      sold_amount: 0, // new field
    }));
  } catch (err) {
    console.error(err);
    errorMessage.value = 'Failed to fetch summary';
  } finally {
    loading.value = false;
  }
};

// Format currency
const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-UG', { style: 'currency', currency: 'UGX' }).format(value || 0);
};

// Submit returns/damages/sales
const submitReturnsAndSales = async () => {
  errors.customer_id = '';
  errors.cash_account_id = '';
  successMessage.value = '';
  errorMessage.value = '';

  if (!form.customer_id) {
    errors.customer_id = 'Customer is required';
    return;
  }

  // if (!form.cash_account_id and ) {
  //   errors.cash_account_id = 'Cash account is required';
  //   return;
  // }

// Validate quantities and sold amount/account
for (const item of summary.value) {
  const totalEntered = item.returned_quantity + item.damaged_quantity + item.sold_quantity;

  // Check total quantities do not exceed pending
  if (totalEntered > item.quantity_not_returned) {
    errorMessage.value = `Total returned + damaged + sold exceeds pending for ${item.product_name}`;
    return;
  }

  // If sold quantity > 0, amount must be entered
  if (item.sold_quantity > 0 && (!item.sold_amount || item.sold_amount <= 0)) {
    errorMessage.value = `Please enter sold amount for ${item.product_name}`;
    return;
  }

  // If sold quantity > 0, cash account must be selected
  if (item.sold_quantity > 0 && !form.cash_account_id) {
    errors.cash_account_id = 'Cash account is required when selling items';
    errorMessage.value = 'Cash account is required for sold items';
    return;
  }
}


  const payload = {
    customer_id: form.customer_id,
    cash_account_id: form.cash_account_id,
    items: summary.value
      .filter(item => item.returned_quantity > 0 || item.damaged_quantity > 0 || item.sold_quantity > 0)
      .map(item => ({
        product_unit_id: item.type === 'Bottle' ? item.product_unit_id : null,
        container_id: item.type === 'Crate' ? item.container_id : null,
        bottles_returned: item.type === 'Bottle' ? item.returned_quantity : 0,
        bottles_damaged: item.type === 'Bottle' ? item.damaged_quantity : 0,
        bottles_sold: item.type === 'Bottle' ? item.sold_quantity : 0,
        bottles_sold_amount: item.type === 'Bottle' ? item.sold_amount : 0,
        crates_returned: item.type === 'Crate' ? item.returned_quantity : 0,
        crates_damaged: item.type === 'Crate' ? item.damaged_quantity : 0,
        crates_sold: item.type === 'Crate' ? item.sold_quantity : 0,
        crates_sold_amount: item.type === 'Crate' ? item.sold_amount : 0,
      }))
  };

  if (!payload.items.length) {
    errorMessage.value = 'No quantities entered';
    return;
  }

  loading.value = true;
  try {
    const res = await api.post('/sales/returnable/auto_return_or_sell', payload);

    successMessage.value = res.data.message || 'Saved successfully';

    // Reset form
    form.customer_id = '';
    form.cash_account_id = '';
    summary.value = [];
    Object.keys(errors).forEach(k => (errors[k] = ''));

    setTimeout(() => {
      successMessage.value = '';
    }, 3000);

  } catch (err) {
    console.error(err);
    errorMessage.value = err.response?.data?.error || 'Failed to submit';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchCustomers();
  fetchCashAccounts();
});
</script>

<style scoped>
select,
input {
  transition: all 0.2s ease;
}
</style>
