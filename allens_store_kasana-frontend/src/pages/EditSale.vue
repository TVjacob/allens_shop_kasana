<template>
  <div class="w-full min-h-screen bg-gray-50 px-6 py-6">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 text-center">
      {{ isEditMode ? 'Edit Sale #' + route.params.id : 'Create New Sale' }}
    </h1>

    <!-- Sale Header -->
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
        clearable
        class="text-lg"
        :loading="loadingAccounts"
        @update:model-value="selectPaymentAccountById"
      ></v-autocomplete>
      <p v-if="saleHeaderErrors.payment_account" class="text-red-600 text-sm mt-1">{{ saleHeaderErrors.payment_account }}</p>
    </div>

    <!-- Sale Items Table -->
    <div class="overflow-x-auto bg-white rounded-lg shadow border border-gray-200">
      <table class="w-full table-auto border-collapse">
        <thead class="bg-gray-100 text-base">
          <tr>
            <th class="p-3 border min-w-[220px]">Product</th>
            <th class="p-3 border min-w-[80px] text-center">Stock</th>
            <th class="p-3 border min-w-[140px]">Unit</th>
            <th class="p-3 border min-w-[140px]">Sale Type</th>
            <th class="p-3 border min-w-[120px] text-center">Selling Price</th>
            <th class="p-3 border min-w-[120px] text-center">Cost Price</th>
            <th class="p-3 border min-w-[120px] text-center">Quantity</th>
            <th class="p-3 border min-w-[120px] text-center">Total</th>
            <th class="p-3 border min-w-[100px] text-center">Actions</th>
          </tr>
        </thead>
        <tbody class="text-base">
          <tr v-for="(item, idx) in saleItems" :key="idx" class="hover:bg-gray-50 transition">
            <!-- Product -->
            <td class="p-3 border min-w-[220px]">
              <v-autocomplete
                v-model="item.selectedProductObj"
                :items="item.searchResults"
                item-title="name"
                item-value="id"
                label="Product"
                variant="outlined"
                dense
                clearable
                class="w-full text-lg"
                hide-details
                :loading="item.loading"
                @update:search="val => debouncedSearchProduct(val, idx)"
                @update:model-value="id => selectProduct(id, idx)"
              ></v-autocomplete>
            </td>

            <!-- Stock -->
            <td class="p-3 border text-center">{{ item.stock_qty }}</td>

            <!-- Unit -->
            <td class="p-3 border min-w-[140px]">
              <v-autocomplete
                v-if="item.units && item.units.length"
                v-model="item.selectedUnitObj"
                :items="item.units"
                item-title="unit_name"
                item-value="id"
                label="Select Unit"
                variant="outlined"
                hide-details
                class="text-base w-full"
                @update:model-value="val => selectUnit(val, idx)"
              ></v-autocomplete>
            </td>

            <!-- Sale Type -->
            <td class="p-3 border text-center">
              <select
                v-model="item.sale_type"
                @change="updateSaleType(item)"
                class="w-full border border-gray-300 rounded-xl p-2 text-base focus:ring-2 focus:ring-indigo-400 transition"
              >
                <option value="wholesale">Wholesale</option>
                <option value="retail">Retail</option>
              </select>
            </td>

            <!-- Selling Price -->
            <td class="p-3 border text-center">
              <input
                type="number"
                v-model.number="item.unit_price"
                @input="calculateTotal(item)"
                class="w-full border border-gray-300 rounded-xl p-2 text-base text-right"
              />
            </td>

            <!-- Cost Price -->
            <td class="p-3 border text-center">{{ formatPrice(item.last_purchase_price) }}</td>

            <!-- Quantity -->
            <td class="p-3 border text-center">
              <input
                type="number"
                v-model.number="item.quantity"
                min="0"
                @input="calculateTotal(item)"
                class="w-full border border-gray-300 rounded-xl p-2 text-base text-right"
              />
            </td>

            <!-- Total -->
            <td class="p-3 border text-right">
              <input
                type="number"
                v-model.number="item.total_price"
                @input="recalculateUnitPriceFromTotal(item)"
                class="w-full border border-gray-300 rounded-xl p-2 text-base text-right font-bold text-indigo-700"
              />
            </td>

            <!-- Actions -->
            <td class="p-3 border text-center">
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
    </div>

    <!-- Add Item & Grand Total -->
    <div class="flex flex-col md:flex-row justify-between items-center mt-6 gap-4">
      <button
        @click="addRow"
        class="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition transform hover:scale-105"
      >
        + Add Item
      </button>
      <div class="text-2xl font-bold">
        Grand Total: <span class="text-indigo-600">{{ formatPrice(grandTotal) }}</span>
      </div>
    </div>

    <!-- Save Button -->
    <div class="mt-6 text-right">
      <button
        @click="saveSale"
        class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition transform hover:scale-105 text-lg"
      >
        {{ isEditMode ? 'Update Sale' : 'Save Sale' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import debounce from 'lodash.debounce'
import api from '../api'

const route = useRoute()
const router = useRouter()
const isEditMode = ref(false)
const saleId = ref(null)

// ---------- Header ----------
const saleHeader = reactive({
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
const grandTotal = computed(() => saleItems.value.reduce((sum, item) => sum + (item.total_price || 0), 0))

// ---------- Utils ----------
const formatPrice = value => (value == null ? '0' : new Intl.NumberFormat('en-UG').format(value))

// ---------- Fetch Data ----------
const fetchCustomers = async () => {
  loadingCustomers.value = true
  try {
    const res = await api.get('/customer/')
    customers.value = res.data
  } finally { loadingCustomers.value = false }
}

const fetchAccounts = async () => {
  loadingAccounts.value = true
  try {
    const res = await api.get('/accounts/?type=asset')
    paymentAccounts.value = res.data
  } finally { loadingAccounts.value = false }
}

const selectCustomerById = id => {
  const cust = customers.value.find(c => c.id === id)
  selectedCustomerObj.value = cust || null
  saleHeader.customer_id = cust?.id || ''
}

const selectPaymentAccountById = id => {
  const acc = paymentAccounts.value.find(a => a.id === id)
  selectedPaymentObj.value = acc || null
  saleHeader.payment_account = acc?.id || ''
}

// ---------- Products ----------
const debouncedSearchProduct = debounce(async (query, idx) => {
  const item = saleItems.value[idx]
  if (!query?.trim()) { item.searchResults = []; return }
  item.loading = true
  try {
    const res = await api.get('/inventory/products/search', { params: { name: query } })
    item.searchResults = res.data.map(p => ({
      id: p.id,
      name: p.name + ' : ' + p.category_name,
      stock_qty: p.quantity,
      retail_price: p.price || 0,
      wholesale_price: p.whole_price || 0,
      last_purchase_price: p.last_purchase_price || 0
    }))
  } finally { item.loading = false }
}, 400)

const selectProduct = async (id, idx) => {
  const item = saleItems.value[idx]
  const prod = item.searchResults.find(p => p.id === id)
  if (!prod) return
  item.selectedProductObj = prod
  item.product_id = prod.id
  item.product_name = prod.name
  item.stock_qty = prod.stock_qty
  item.unit_price = 0
  item.quantity = 0
  item.total_price = 0
  item.units = []
  item.selectedUnitObj = null
  item.last_purchase_price = prod.last_purchase_price || 0

  try {
    const res = await api.get(`/inventory/products/${prod.id}/units`)
    item.units = res.data || []
    if (item.units.length) {
      item.selectedUnitObj = item.units[0]
      item.retail_price = item.units[0].retail_price ?? 0
      item.wholesale_price = item.units[0].wholesale_price ?? 0
      item.unit_price = item.units[0].retail_price ?? 0
      item.conversion_quantity = item.units[0].conversion_quantity ?? 1
    }
  } catch (err) { console.error(err) }
}

const selectUnit = (unitId, idx) => {
  const item = saleItems.value[idx]
  const selected = item.units.find(u => u.id === unitId)
  if (!selected) return
  item.selectedUnitObj = selected
  item.retail_price = selected.retail_price ?? 0
  item.wholesale_price = selected.wholesale_price ?? 0
  item.unit_price = item.wholesale_price ?? 0
  item.conversion_quantity = selected.conversion_quantity ?? 1
  calculateTotal(item)
}

// ---------- Calculations ----------
const updateSaleType = item => {
  item.unit_price = item.sale_type === 'wholesale' ?  item.wholesale_price:item.retail_price 
  calculateTotal(item)
}

const calculateTotal = item => item.total_price = (item.quantity || 0) * (item.unit_price || 0)

const recalculateUnitPriceFromTotal = item => {
  if (item.quantity && item.quantity > 0) item.unit_price = item.total_price / item.quantity
  calculateTotal(item)
}

// ---------- Rows ----------
const addRow = () => saleItems.value.push({
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
  loading: false,
  conversion_quantity: 1,
  // sale_type: 'retail',
  sale_type: 'wholesale', // ✅ set default to wholesale

  last_purchase_price: 0
})

const removeRow = idx => saleItems.value.splice(idx, 1)

// ---------- Validation ----------
const validateSale = () => {
  let valid = true
  saleHeaderErrors.customer_id = ''
  saleHeaderErrors.payment_account = ''
  saleItemsErrors.value = saleItems.value.map(() => ({ product_id: '', quantity: '', unit_id: '', unit_price: '' }))

  if (!saleHeader.customer_id) { saleHeaderErrors.customer_id = 'Customer is required'; valid = false }
  if (saleHeader.amount_paid > 0 && !saleHeader.payment_account) { saleHeaderErrors.payment_account = 'Payment account is required'; valid = false }

  saleItems.value.forEach((item, idx) => {
    if (!item.product_id) { saleItemsErrors.value[idx].product_id = 'Select a product'; valid = false }
    if (!item.selectedUnitObj?.id) { saleItemsErrors.value[idx].unit_id = 'Select a unit'; valid = false }
    if (!item.quantity || item.quantity <= 0) { saleItemsErrors.value[idx].quantity = 'Quantity must be > 0'; valid = false }
    if (!item.unit_price || item.unit_price <= 0) { saleItemsErrors.value[idx].unit_price = 'Unit price must be > 0'; valid = false }
  })

  return valid
}

// ---------- Load Existing Sale ----------
const fetchSaleDetails = async id => {
  try {
    const res = await api.get(`/sales/${id}/edit`)
    const sale = res.data.data

    // header
    saleHeader.sale_date = sale.sale_date
    saleHeader.amount_paid = sale.total_paid || 0
    saleHeader.memo = sale.memo || ''
    saleHeader.customer_id = sale.customer_id
    saleHeader.payment_account = sale.payment_account_id || ''
    selectedCustomerObj.value = customers.value.find(c => c.id === sale.customer_id) || null
    selectedPaymentObj.value = paymentAccounts.value.find(a => a.id === sale.payment_account_id) || null

    // items
    saleItems.value = []
    saleItemsErrors.value = []

    for (const i of sale.items) {
      const resUnits = await api.get(`/inventory/products/${i.product_id}/units`)
      const units = resUnits.data || []
      const selectedUnit = units.find(u => u.id === i.unit_id) || units[0] || null

      saleItems.value.push({
        product_id: i.product_id,
        product_name: i.product_name,
        category_name: i.category_name || '',
        stock_qty: i.stock_qty || 0,
        retail_price: selectedUnit?.retail_price ?? i.retail_price ?? 0,
        wholesale_price: selectedUnit?.wholesale_price ?? i.wholesale_price ?? 0,
        unit_price: i.unit_price,
        quantity: i.quantity,
        total_price: i.total_price,
        selectedProductObj: { id: i.product_id, name: i.product_name },
        selectedUnitObj: selectedUnit,
        units: units,
        conversion_quantity: selectedUnit?.conversion_quantity ?? 1,
        sale_type: i.sale_type || 'wholesale',
        searchResults: [{ id: i.product_id, name: i.product_name + ' : ' + (i.category_name || '') }],
        last_purchase_price: i.last_purchase_price || 0,
        loading: false
      })

      saleItemsErrors.value.push({ product_id: '', quantity: '', unit_id: '', unit_price: '' })
    }
  } catch (err) { alert('Failed to load sale details: ' + (err.response?.data?.error || err.message)) }
}

// ---------- Save ----------
const saveSale = async () => {
  if (!validateSale()) return

  const payload = {
    sale_id: isEditMode.value ? saleId.value : undefined,
    sale_date: saleHeader.sale_date,
    customer_id: saleHeader.customer_id,
    payment_account_id: saleHeader.payment_account,
    amount_paid: saleHeader.amount_paid,
    memo: saleHeader.memo,
    items: saleItems.value.map(i => ({
      product_id: i.product_id,
      unit_id: i.selectedUnitObj?.id,
      unit_price: i.unit_price,
      quantity: i.quantity,
      total_price: i.total_price
    }))
  }

  try {
    if (isEditMode.value) {
      await api.post('/sales/edit', payload)
      alert('✅ Sale updated successfully!')
    } else {
      const res = await api.post('/sales/', payload)
      alert(`✅ Sale created! ID: ${res.data.sale_id}`)
    }
    router.push('/saleslist')
  } catch (err) { alert(err.response?.data?.error || err.message) }
}

// ---------- Lifecycle ----------
onMounted(async () => {
  await fetchCustomers()
  await fetchAccounts()
  saleId.value = route.params.id
  if (saleId.value) { isEditMode.value = true; await fetchSaleDetails(saleId.value) }
  else addRow()
})
</script>
