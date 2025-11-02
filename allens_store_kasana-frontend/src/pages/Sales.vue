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
          class="w-full border border-gray-300 rounded-xl p-3 text-lg focus:ring-2 focus:ring-indigo-400 transition"
        />
        <p v-if="saleHeaderErrors.sale_date" class="text-red-600 text-sm mt-1">{{ saleHeaderErrors.sale_date }}</p>
      </div>

      <!-- Customer -->
      <v-autocomplete
        v-model="selectedCustomerObj"
        :items="customers"
        item-title="name"
        item-value="id"
        label="Customer"
        variant="outlined"
        density="comfortable"
        clearable
        class="text-lg"
        :loading="loadingCustomers"
        @update:model-value="selectCustomerById"
      ></v-autocomplete>
      <p v-if="saleHeaderErrors.customer_id" class="text-red-600 text-sm mt-1">{{ saleHeaderErrors.customer_id }}</p>

      <!-- Amount Paid -->
      <div>
        <label class="block font-semibold mb-1">Amount Paid</label>
        <input
          type="number"
          v-model.number="saleHeader.amount_paid"
          min="0"
          class="w-full border border-gray-300 rounded-xl p-3 text-lg focus:ring-2 focus:ring-indigo-400 transition"
        />
        <p v-if="saleHeaderErrors.amount_paid" class="text-red-600 text-sm mt-1">{{ saleHeaderErrors.amount_paid }}</p>
      </div>

      <!-- Memo -->
      <div>
        <label class="block font-semibold mb-1">Memo / Details</label>
        <input
          type="text"
          v-model="saleHeader.memo"
          placeholder="Optional"
          class="w-full border border-gray-300 rounded-xl p-3 text-lg focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>

      <!-- Payment Account -->
      <v-autocomplete
        v-model="selectedPaymentObj"
        :items="paymentAccounts"
        item-title="name"
        item-value="id"
        label="Payment Account"
        variant="outlined"
        density="comfortable"
        clearable
        class="text-lg"
        :loading="loadingAccounts"
        @update:model-value="selectPaymentAccountById"
      ></v-autocomplete>
      <p v-if="saleHeaderErrors.payment_account" class="text-red-600 text-sm mt-1">{{ saleHeaderErrors.payment_account }}</p>
    </div>

    <!-- --------- Sale Items Table --------- -->
    <table class="w-full border rounded-lg overflow-hidden relative shadow-sm">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border">Product</th>
          <th class="p-2 border">Stock</th>
          <th class="p-2 border w-56">Unit</th>
          <th class="p-2 border">Retail</th>
          <th class="p-2 border">Wholesale</th>
          <th class="p-2 border">Unit Price</th>
          <th class="p-2 border">Cost Price </th>

          <th class="p-2 border">Quantity</th>
          <th class="p-2 border">Total</th>
          <th class="p-2 border">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(item, idx) in saleItems"
          :key="idx"
          class="hover:bg-gray-50 transition"
        >
          <!-- Product -->
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
              class="text-base"
              :loading="item.loading"
              @update:search="val => debouncedSearchProduct(val, idx)"
              @update:model-value="id => selectProduct(id, idx)"
            ></v-autocomplete>
            <p v-if="saleItemsErrors[idx]?.product_id" class="text-red-600 text-sm mt-1">
              {{ saleItemsErrors[idx].product_id }}
            </p>
          </td>

          <!-- Stock Qty -->
          <td class="p-2 border text-center text-base">{{ item.stock_qty }}</td>

          <!-- Unit -->
          <td class="p-2 border">
            <v-autocomplete
              v-if="item.units && item.units.length"
              v-model="item.selectedUnitObj"
              :items="item.units"
              item-title="unit_name"
              item-value="id"
              label="Select Unit"
              variant="outlined"
              density="comfortable"
              hide-details
              class="text-base min-w-[10rem]"
              @update:model-value="val => selectUnit(val, idx)"
            ></v-autocomplete>
            <p v-if="saleItemsErrors[idx]?.unit_id" class="text-red-600 text-sm mt-1">
              {{ saleItemsErrors[idx].unit_id }}
            </p>
          </td>

          <!-- Retail -->
          <td class="p-2 border text-center text-gray-700 font-semibold">
            {{ formatPrice(item.retail_price) }}
          </td>

          <!-- Wholesale -->
          <td class="p-2 border text-center text-gray-700 font-semibold">
            {{ formatPrice(item.wholesale_price) }}
          </td>
          
          <!-- Unit Price -->
          <td class="p-2 border text-right">
            <input
              type="number"
              v-model.number="item.unit_price"
              @input="calculateTotal(item)"
              class="w-full text-right border border-gray-300 rounded-xl p-2 text-base focus:ring-2 focus:ring-indigo-400 transition"
            />
            <p v-if="saleItemsErrors[idx]?.unit_price" class="text-red-600 text-sm mt-1">
              {{ saleItemsErrors[idx].unit_price }}
            </p>
          </td>

          <!-- cost Price  -->
          <td class="p-2 border text-center text-gray-700 font-semibold">
            {{ formatPrice(item.last_purchase_price) }}
          </td>
          <!-- Quantity -->
          <td class="p-2 border">
            <input
              type="number"
              v-model.number="item.quantity"
              @input="validateQuantity(item, idx)"
              class="w-full text-right border border-gray-300 rounded-xl p-2 text-base focus:ring-2 focus:ring-indigo-400 transition"
            />
            <p v-if="saleItemsErrors[idx]?.quantity" class="text-red-600 text-sm mt-1">
              {{ saleItemsErrors[idx].quantity }}
            </p>
          </td>

          <!-- Total -->
          <td class="p-2 border text-right font-bold text-indigo-700">
            {{ item.total_price.toFixed(2) }}
          </td>

          <!-- Actions -->
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
      <div class="text-2xl font-bold">
        Grand Total:
        <span class="text-indigo-600">{{ grandTotal.toFixed(2) }}</span>
      </div>
    </div>

    <!-- Save -->
    <div class="mt-6 text-right">
      <button
        @click="saveSale"
        class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition transform hover:scale-105 text-lg"
      >
        Save Sale
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
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
const saleHeaderErrors = reactive({
  customer_id: '',
  payment_account: '',
  amount_paid: '',
  sale_date: ''
})

// ---------- State ----------
const saleItems = ref([])
const saleItemsErrors = ref([])

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

// ---------- Customer / Account ----------
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
  selectedCustomerObj.value = cust || null
  saleHeader.value.customer_id = cust ? cust.id : ''
}

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
  selectedPaymentObj.value = acc || null
  saleHeader.value.payment_account = acc ? acc.id : ''
}

// ---------- Utils ----------
const formatPrice = (value) => (value == null ? '0' : new Intl.NumberFormat('en-UG').format(value))

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
      name: p.name +' : '+p.category_name,
      stock_qty: p.quantity,
      retail_price: p.price || 0,
      wholesale_price: p.whole_price || 0,
      last_purchase_price: p.last_purchase_price || 0
    }))
  } finally {
    item.loading = false
  }
}, 400)

const selectProduct = async (id, idx) => {
  const item = saleItems.value[idx]
  const prod = item.searchResults.find(p => p.id === id)
  if (!prod) return

  item.selectedProductObj = prod
  item.product_id = prod.id
  item.product_name = prod.name
  item.stock_qty = prod.stock_qty
  item.retail_price = 0
  item.wholesale_price = 0
  item.unit_price = 0
  item.quantity = 0
  item.total_price = 0
  item.searchResults = []
  item.units = []
  item.selectedUnitObj = null
  item.last_purchase_price = prod.last_purchase_price || 0

  try {
    const res = await api.get(`/inventory/products/${prod.id}/units`)
    item.units = res.data || []
    if (item.units.length > 0) {
      item.selectedUnitObj = item.units[0]
      item.retail_price = item.units[0].retail_price ?? 0
      item.wholesale_price = item.units[0].wholesale_price ?? 0
    }
  } catch (err) {
    console.error('Failed to fetch units:', err)
  }
}

const selectUnit = (unitId, idx) => {
  const item = saleItems.value[idx]
  const selected = item.units.find(u => u.id === unitId)
  if (!selected) return
  item.selectedUnitObj = selected
  item.retail_price = selected.retail_price ?? 0
  item.wholesale_price = selected.wholesale_price ?? 0
  calculateTotal(item)
}

// ---------- Rows ----------
const addRow = () => {
  saleItems.value.push({
    product_id: null,
    product_name: '',
    stock_qty: 0,
    retail_price: 0,
    wholesale_price: 0,
    unit_price: 0,
    quantity: 0,
    total_price: 0,
    selectedProductObj: null,
    selectedUnitObj: null,
    units: [],
    searchResults: [],
    loading: false
  })
  saleItemsErrors.value.push({ product_id: '', quantity: '', unit_id: '', unit_price: '' })
}
const removeRow = (idx) => {
  saleItems.value.splice(idx, 1)
  saleItemsErrors.value.splice(idx, 1)
}
const calculateTotal = (item) => {
  item.total_price = (item.quantity || 0) * (item.unit_price || 0)
}
const validateQuantity = (item, idx) => {
  if (item.quantity < 0) item.quantity = 0
  if (item.quantity > item.stock_qty) item.quantity = item.stock_qty
  calculateTotal(item)
}

// ---------- Validation ----------
const validateSale = () => {
  let valid = true
  saleHeaderErrors.customer_id = ''
  saleHeaderErrors.payment_account = ''
  saleItemsErrors.value = saleItems.value.map(() => ({ product_id: '', quantity: '', unit_id: '', unit_price: '' }))

  if (!saleHeader.value.customer_id) {
    saleHeaderErrors.customer_id = 'Customer is required'
    valid = false
  }
  if ( saleHeader.value.amount_paid >0  &&  !saleHeader.value.payment_account) {
    saleHeaderErrors.payment_account = 'Payment account is required'
    valid = false
  }

  saleItems.value.forEach((item, idx) => {
    if (!item.product_id) {
      saleItemsErrors.value[idx].product_id = 'Select a product'
      valid = false
    }
    if (!item.selectedUnitObj?.id) {
      saleItemsErrors.value[idx].unit_id = 'Select a unit'
      valid = false
    }
    if (!item.quantity || item.quantity <= 0) {
      saleItemsErrors.value[idx].quantity = 'Quantity must be > 0'
      valid = false
    }
    if (!item.unit_price || item.unit_price <= 0) {
      saleItemsErrors.value[idx].unit_price = 'Unit price must be > 0'
      valid = false
    }
  })

  return valid
}

// ---------- Save ----------
const saveSale = async () => {
  if (!validateSale()) return

  const payload = {
    sale_date: saleHeader.value.sale_date,
    customer_id: saleHeader.value.customer_id,
    payment_account_id: saleHeader.value.payment_account,
    amount_paid: saleHeader.value.amount_paid,
    memo: saleHeader.value.memo,
    items: saleItems.value.map(i => ({
      product_id: i.product_id,
      unit_id: i.selectedUnitObj?.id,
      unit_price: i.unit_price,
      quantity: i.quantity,
      total_price: i.total_price
    }))
  }

  try {
    const res = await api.post('/sales/', payload)
    alert(`Sale saved! ID: ${res.data.sale_id}`)

    // Reset form
    saleHeader.value = { sale_date: new Date().toISOString().slice(0, 10), amount_paid: 0, memo: '', payment_account: '', customer_id: '' }
    selectedCustomerObj.value = null
    selectedPaymentObj.value = null
    saleItems.value = []
    saleItemsErrors.value = []
    addRow()
  } catch (err) {
    const errorMsg = err.response?.data?.error || err.message
    alert(errorMsg)
  }
}

// ---------- Lifecycle ----------
onMounted(() => {
  fetchCustomers()
  fetchAccounts()
  addRow()
})
</script>
