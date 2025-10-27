<template>
  <div class="p-6 max-w-6xl mx-auto bg-white shadow-lg rounded-lg">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Sales Dashboard</h1>

    <!-- --------- Sale Header --------- -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
      <!-- Sale Date -->
      <div>
        <label class="block font-semibold mb-1">Sale Date</label>
        <input
          type="date"
          v-model="saleHeader.sale_date"
          class="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>

      <!-- Customer Combobox -->
      <v-autocomplete
        v-model="selectedCustomerObj"
        :items="customers"
        item-title="name"
        item-value="id"
        label="Customer"
        variant="outlined"
        density="comfortable"
        clearable
        :loading="loadingCustomers"
        @update:model-value="selectCustomerById"
      ></v-autocomplete>

      <!-- Amount Paid -->
      <div>
        <label class="block font-semibold mb-1">Amount Paid</label>
        <input
          type="number"
          v-model.number="saleHeader.amount_paid"
          min="0"
          class="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>

      <!-- Memo -->
      <div>
        <label class="block font-semibold mb-1">Memo / Details</label>
        <input
          type="text"
          v-model="saleHeader.memo"
          placeholder="Optional"
          class="w-full border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>

      <!-- Payment Account Combobox -->
      <v-autocomplete
        v-model="selectedPaymentObj"
        :items="paymentAccounts"
        item-title="name"
        item-value="id"
        label="Payment Account"
        variant="outlined"
        density="comfortable"
        clearable
        :loading="loadingAccounts"
        @update:model-value="selectPaymentAccountById"
      ></v-autocomplete>
    </div>

    <!-- --------- Sale Items Table --------- -->
    <table class="w-full border rounded-lg overflow-hidden relative shadow-sm">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border">Product</th>
          <th class="p-2 border">Stock Qty</th>
          <th class="p-2 border">Unit</th>
          <th class="p-2 border"> Retail</th>
          <th class="p-2 border"> WholeSale</th>
          <th class="p-2 border">Unit Price</th>
          <th class="p-2 border">Quantity</th>
          <th class="p-2 border">Total Price</th>
          <th class="p-2 border">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, idx) in saleItems" :key="idx" class="hover:bg-gray-50 transition">
          <td class="p-2 border w-64">
            <v-autocomplete
              v-model="item.selectedProductObj"
              :items="item.searchResults"
              item-title="name"
              item-value="id"
              label="Product"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              :loading="item.loading"
              @update:search="val => debouncedSearchProduct(val, idx)"
              @update:model-value="id => selectProduct(id, idx)"
            ></v-autocomplete>
          </td>
          <td class="p-2 border text-center">{{ item.stock_qty }}</td>
          <td class="p-2 border text-center">{{ item.unit }}</td>
          <td class="p-2 border text-center">{{ formatPrice(item.unit_price || 0 ) }}</td>
          <td class="p-2 border text-center">{{ formatPrice(item.whole_price|| 0) }}</td>
          <td class="p-2 border">
            <input
              type="number"
              v-model.number="item.unit_price"
              @input="calculateTotal(item)"
              class="w-full text-right border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-indigo-400 transition"
            />
          </td>
          <td class="p-2 border">
            <input
              type="number"
              v-model.number="item.quantity"
              @input="validateQuantity(item)"
              class="w-full text-right border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-indigo-400 transition"
            />
          </td>
          <td class="p-2 border text-right font-semibold">{{ item.total_price.toFixed(2) }}</td>
          <td class="p-2 border text-center">
            <button
              @click="removeRow(idx)"
              class="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 transition transform hover:scale-105"
            >
              ✕
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Add Item & Grand Total -->
    <div class="flex justify-between items-center mt-6">
      <button
        @click="addRow"
        class="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition transform hover:scale-105"
      >
        + Add Item
      </button>
      <div class="text-xl font-bold">
        Grand Total: <span class="text-indigo-600">{{ grandTotal.toFixed(2) }}</span>
      </div>
    </div>

    <!-- Save -->
    <div class="mt-6 text-right">
      <button
        @click="saveSale"
        class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition transform hover:scale-105"
      >
        Save Sale
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import debounce from 'lodash.debounce'
import api from '../api'

// ---------- Header ----------
const saleHeader = ref({
  sale_date: new Date().toISOString().slice(0, 10),
  amount_paid: 0,
  memo: '',
  payment_account: '',
  customer_id: ''
})

// ---------- State ----------
const saleItems = ref([])
const customers = ref([])
const paymentAccounts = ref([])
const selectedCustomerObj = ref(null)
const selectedPaymentObj = ref(null)
const loadingCustomers = ref(false)
const loadingAccounts = ref(false)

// ---------- Computed ----------
const grandTotal = computed(() =>
  saleItems.value.reduce((sum, item) => sum + (item.total_price || 0), 0)
)

// ---------- Customer Logic ----------
const fetchCustomers = async () => {
  loadingCustomers.value = true
  try {
    const res = await api.get('/customer/')
    customers.value = res.data
  } finally {
    loadingCustomers.value = false
  }
}
const selectCustomerById = (id) => {
  const cust = customers.value.find(c => c.id === id)
  if (cust) {
    selectedCustomerObj.value = cust
    saleHeader.value.customer_id = cust.id
  } else {
    selectedCustomerObj.value = null
    saleHeader.value.customer_id = ''
  }
}

// ---------- Payment Account Logic ----------
const fetchAccounts = async () => {
  loadingAccounts.value = true
  try {
    const res = await api.get('/accounts/?type=asset')
    paymentAccounts.value = res.data
  } finally {
    loadingAccounts.value = false
  }
}
const selectPaymentAccountById = (id) => {
  const acc = paymentAccounts.value.find(a => a.id === id)
  if (acc) {
    selectedPaymentObj.value = acc
    saleHeader.value.payment_account = acc.id
  } else {
    selectedPaymentObj.value = null
    saleHeader.value.payment_account = ''
  }
}
const formatPrice=(value)=> {
  if (value == null) return '0';
  return new Intl.NumberFormat('en-UG').format(value);
    }

// ---------- Product Logic ----------
const debouncedSearchProduct = debounce(async (query, idx) => {
  const item = saleItems.value[idx]
  if (!query?.trim()) {
    item.searchResults = []
    return
  }
  item.loading = true
  try {
    const res = await api.get('/inventory/products/search', { params: { name: query } })
    item.searchResults = res.data.map(p => ({
      id: p.id,
      name: p.name,
      stock_qty: p.quantity,
      unit: p.category_name || '',
      price: p.price||0,
      whole_price: p.whole_price||0,
    }))
  } finally {
    item.loading = false
  }
}, 400)

const selectProduct = (id, idx) => {
  const item = saleItems.value[idx]
  const prod = item.searchResults.find(p => p.id === id)
  if (!prod) return
  item.selectedProductObj = prod
  item.product_id = prod.id
  item.product_name = prod.name
  item.stock_qty = prod.stock_qty
  item.unit = prod.unit
  item.unit_price = prod.price
  item.quantity = 0
  item.total_price = 0
  item.searchResults = []
  item.whole_price=prod.whole_price
}

// ---------- Rows ----------
const addRow = () => {
  saleItems.value.push({
    product_id: null,
    product_name: '',
    stock_qty: 0,
    unit: '',
    unit_price: 0,
    quantity: 0,
    total_price: 0,
    selectedProductObj: null,
    searchResults: [],
    loading: false
  })
}
const removeRow = (idx) => saleItems.value.splice(idx, 1)
const calculateTotal = (item) => item.total_price = (item.quantity || 0) * (item.unit_price || 0)
const validateQuantity = (item) => {
  if (item.quantity < 0) item.quantity = 0
  if (item.quantity > item.stock_qty) item.quantity = item.stock_qty
  calculateTotal(item)
}

// ---------- Save ----------
const saveSale = async () => {
  if (!saleHeader.value.customer_id) return alert("Select a customer")
  if (!saleItems.value.length) return alert("Add at least one item")
  for (const [i, item] of saleItems.value.entries()) {
    if (!item.product_id) return alert(`Item ${i+1}: Select a product`)
    if (!item.quantity || item.quantity <= 0) return alert(`Item ${i+1}: Quantity > 0 required`)
  }

  const payload = {
    sale_date: saleHeader.value.sale_date,
    customer_id: saleHeader.value.customer_id,
    payment_account_id: saleHeader.value.payment_account,
    amount_paid: saleHeader.value.amount_paid,
    memo: saleHeader.value.memo,
    items: saleItems.value.map(i => ({
      product_id: i.product_id,
      unit_price: i.unit_price,
      quantity: i.quantity,
      total_price: i.total_price
    }))
  }

  try {
    const res = await api.post('/sales/', payload)
    alert(`Sale saved! ID: ${res.data.sale_id}`)
    // reset
    saleHeader.value = { sale_date: new Date().toISOString().slice(0,10), amount_paid:0, memo:'', payment_account:'', customer_id:'' }
    selectedCustomerObj.value = null
    selectedPaymentObj.value = null
    saleItems.value = []
    addRow()
  } catch (err) {
    alert(err.response?.data?.error || err.message)
  }
}

// ---------- Lifecycle ----------
onMounted(() => {
  fetchCustomers()
  fetchAccounts()
  addRow()
})
</script>

<!-- <style scoped>
input[type="text"],
input[type="number"],
input[type="date"],
select {
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  transition: all 0.2s ease-in-out;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
input:focus,
select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.2);
}
button {
  transition: all 0.2s ease-in-out;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
table {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
  border-radius: 0.5rem;
}
thead tr { background-color: #f3f4f6; }
th, td { padding: 0.75rem 0.5rem; border-bottom: 1px solid #e5e7eb; }
tbody tr:hover { background-color: #f9fafb; transition: background-color 0.2s ease-in-out; }
ul { width: 100%; border-radius: 0.5rem; max-height: 10rem; overflow-y: auto; z-index: 50; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
ul li { padding: 0.5rem 0.75rem; cursor: pointer; transition: all 0.2s ease; }
ul li:hover { background-color: #e0e7ff; }
.text-red-500 { color: #dc2626; font-size: 0.75rem; }
</style> -->
