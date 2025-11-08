<template>
  <div class="w-full min-h-screen bg-gray-50 px-6 py-6">
    <!-- Page Header -->
    <h1 class="text-3xl font-bold mb-6 text-gray-800 text-center">
      {{ isEditMode ? 'Edit Purchase Order #' + routeId : 'Purchase Order Dashboard' }}
    </h1>

    <!-- -------- Purchase Header -------- -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <!-- Supplier -->
      <div class="md:col-span-2">
        <label class="block font-semibold mb-1">Supplier</label>
        <v-autocomplete
          v-model="selectedSupplier"
          :items="suppliers"
          item-title="name"
          :item-value="s => s"
          variant="outlined"
          clearable
          class="text-lg"
          :loading="loadingSuppliers"
          @update:model-value="selectSupplier"
        ></v-autocomplete>
        <p v-if="errors.supplier" class="text-red-600 text-sm mt-1">{{ errors.supplier }}</p>
      </div>

      <!-- Invoice -->
      <div>
        <label class="block font-semibold mb-1">Invoice Number</label>
        <input
          v-model="poHeader.invoice_number"
          type="text"
          placeholder="INV-001"
          class="w-full border border-gray-300 rounded-xl p-3 text-lg focus:ring-2 focus:ring-indigo-400 transition"
        />
        <p v-if="errors.invoice_number" class="text-red-600 text-sm mt-1">{{ errors.invoice_number }}</p>
      </div>

      <!-- Purchase Date -->
      <div>
        <label class="block font-semibold mb-1">Purchase Date</label>
        <input
          v-model="poHeader.purchase_date"
          type="date"
          class="w-full border border-gray-300 rounded-xl p-3 text-lg focus:ring-2 focus:ring-indigo-400 transition"
        />
        <p v-if="errors.purchase_date" class="text-red-600 text-sm mt-1">{{ errors.purchase_date }}</p>
      </div>

      <!-- Memo -->
      <div class="md:col-span-4">
        <label class="block font-semibold mb-1">Memo / Notes</label>
        <input
          v-model="poHeader.memo"
          type="text"
          placeholder="Optional"
          class="w-full border border-gray-300 rounded-xl p-3 text-lg focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>
    </div>

    <!-- -------- Purchase Items Table -------- -->
    <div class="overflow-x-auto bg-white rounded-lg shadow border border-gray-200">
      <table class="w-full table-auto border-collapse">
        <thead class="bg-gray-100 text-base">
          <tr>
            <th class="p-3 border min-w-[220px]">Product</th>
            <th class="p-3 border min-w-[120px] text-center">Sale Type</th>
            <th class="p-3 border min-w-[140px] text-center">Unit</th>
            <th class="p-3 border min-w-[100px] text-center">Stock</th>
            <th class="p-3 border min-w-[120px] text-center">Last Purchase</th>
            <th class="p-3 border min-w-[120px] text-center">Selling Price</th>
            <th class="p-3 border min-w-[120px] text-center">Buying Price</th>
            <th class="p-3 border min-w-[120px] text-center">Quantity</th>
            <th class="p-3 border min-w-[120px] text-center">Total</th>
            <th class="p-3 border min-w-[100px] text-center">Action</th>
          </tr>
        </thead>

        <tbody class="text-base">
          <template v-for="(item, idx) in poItems" :key="idx">
            <tr class="hover:bg-gray-50 transition">
              <!-- Product -->
              <td class="p-3 border min-w-[220px]">
                <v-autocomplete
                  v-model="item.selectedProduct"
                  :items="item.searchResults"
                  item-title="name"
                  :item-value="p => p"
                  label="Product"
                  variant="outlined"
                  clearable
                  class="text-lg"
                  hide-details
                  :loading="item.loading"
                  @update:search="val => onProductSearch(val, idx)"
                  @update:model-value="product => onProductSelect(product, idx)"
                ></v-autocomplete>

                <p v-if="errors[`product_${idx}`]" class="text-red-600 text-sm mt-1">
                  {{ errors[`product_${idx}`] }}
                </p>
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

              <!-- Unit -->
              <td class="p-3 border text-center">
                <v-autocomplete
                  v-if="item.units && item.units.length"
                  v-model="item.selectedUnitId"
                  :items="item.units"
                  item-title="unit_name"
                  item-value="id"
                  variant="outlined"
                  hide-details
                  class="text-base"
                  @update:model-value="val => onUnitSelect(idx)"
                ></v-autocomplete>
              </td>

              <!-- Stock -->
              <td class="p-3 border text-center">{{ item.stock_qty }}</td>

              <!-- Last Purchase -->
              <td class="p-3 border text-center text-gray-700">
                {{ formatPrice(item.last_purchase_price) }}
              </td>

              <!-- Selling Price (display only) -->
              <td class="p-3 border text-center text-indigo-700 font-semibold">
                {{ formatPrice(item.sale_type === 'wholesale' ? item.wholesale_price : item.retail_price) }}
              </td>

              <!-- Buying Price (editable) -->
              <td class="p-3 border">
                <input
                  type="number"
                  v-model.number="item.cost_price"
                  min="0"
                  @input="onCostChange(item)"
                  class="w-full border border-gray-300 rounded-xl p-2 text-base text-right focus:ring-2 focus:ring-indigo-400 transition"
                />
              </td>

              <!-- Quantity (editable) -->
              <td class="p-3 border">
                <input
                  type="number"
                  v-model.number="item.quantity"
                  min="0"
                  @input="onQuantityChange(item)"
                  class="w-full border border-gray-300 rounded-xl p-2 text-base text-right focus:ring-2 focus:ring-indigo-400 transition"
                />
              </td>

              <!-- Total (editable) -->
              <td class="p-3 border text-right">
                <input
                  type="number"
                  v-model.number="item.total_price"
                  min="0"
                  @input="onTotalChange(item)"
                  class="w-full border border-gray-300 rounded-xl p-2 text-base font-bold text-indigo-700 text-right focus:ring-2 focus:ring-indigo-400 transition"
                />
              </td>

              <!-- Action -->
              <td class="p-3 border text-center">
                <button
                  @click="removeRow(idx)"
                  class="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 transition transform hover:scale-105"
                >
                  ✕
                </button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- -------- Add Row & Grand Total -------- -->
    <div class="flex flex-col md:flex-row justify-between items-center mt-6 gap-4">
      <button
        @click="addRow"
        class="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition transform hover:scale-105"
      >
        + Add Product
      </button>
      <div class="text-2xl font-bold">
        Grand Total: <span class="text-indigo-600">{{ formatPrice(grandTotal) }}</span>
      </div>
    </div>

    <!-- -------- Save Button -------- -->
    <div class="mt-6 text-right">
      <button
        @click="savePurchaseOrder"
        class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition transform hover:scale-105 text-lg"
      >
        {{ isEditMode ? 'Update Purchase Order' : 'Save Purchase Order' }}
      </button>
    </div>

    <!-- Snackbar -->
    <v-snackbar
      v-if="snackbar.show"
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
      location="top-right"
    >
      {{ snackbar.message }}
    </v-snackbar>
  </div>
</template>

<script setup>
/*
  Purchases.vue
  - Full SFC implementing editable purchase order table with:
    - sale_type (wholesale default)
    - unit selection (auto-select first unit)
    - last_purchase_price display
    - selling price display (depends on sale_type + selected unit)
    - editable cost_price, quantity, total_price (changes are reactive)
    - create/update endpoints and edit-mode loader
  You may need to adapt API routes if your backend differs.
*/

import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import debounce from 'lodash.debounce'
import api from '../api' // your axios wrapper

const route = useRoute()
const router = useRouter()
const routeId = route.params.id || null
const isEditMode = computed(() => !!routeId)

// ---------- State ----------
const poHeader = ref({
  supplier_id: '',
  invoice_number: '',
  memo: '',
  purchase_date: new Date().toISOString().slice(0, 10),
})

const suppliers = ref([])
const selectedSupplier = ref(null)
const loadingSuppliers = ref(false)
const poItems = ref([])
const errors = ref({})
const snackbar = ref({ show: false, message: '', color: 'success' })

// ---------- Computed ----------
const grandTotal = computed(() => poItems.value.reduce((sum, item) => sum + (Number(item.total_price) || 0), 0))

// ---------- Helpers ----------
const formatPrice = (v) => new Intl.NumberFormat('en-UG').format(Number(v || 0))

// ---------- Lifecycle ----------
onMounted(async () => {
  await fetchSuppliers()
  if (isEditMode.value) {
    await fetchExistingPO(routeId)
  } else {
    addRow()
  }
})

// ---------- Suppliers ----------
const fetchSuppliers = async () => {
  loadingSuppliers.value = true
  try {
    const res = await api.get('/suppliers/')
    suppliers.value = res.data
  } catch (err) {
    console.error('fetchSuppliers error', err)
  } finally {
    loadingSuppliers.value = false
  }
}

const selectSupplier = (supplier) => {
  if (!supplier) {
    selectedSupplier.value = null
    poHeader.value.supplier_id = ''
    return
  }
  selectedSupplier.value = supplier
  poHeader.value.supplier_id = supplier.id
}

// ---------- Product search & selection ----------
const debouncedSearchProduct = debounce(async (query, idx) => {
  const item = poItems.value[idx]
  if (!query?.trim()) { item.searchResults = []; return }
  item.loading = true
  try {
    const res = await api.get('/inventory/products/search', { params: { name: query } })
    item.searchResults = res.data.map(p => ({
      id: p.id,
      name: `${p.name} : ${p.category_name}`,
      raw: p
    }))
  } catch (err) {
    console.error('product search', err)
  } finally {
    item.loading = false
  }
}, 350)

const onProductSearch = (val, idx) => debouncedSearchProduct(val, idx)

const onProductSelect = async (product, idx) => {
  const item = poItems.value[idx]
  if (!product?.id) {
    // cleared
    item.product_id = null
    item.product_name = ''
    item.units = []
    item.selectedUnitId = ''
    item.cost_price = 0
    item.wholesale_price = 0
    item.retail_price = 0
    item.quantity = 0
    item.total_price = 0
    item.last_purchase_price = 0
    return
  }

  try {
    const res = await api.get(`/inventory/products/${product.id}`)
    const data = res.data
    item.product_id = data.id
    item.product_name = data.name
    item.selectedProduct = { id: data.id, name: data.name }
    item.units = data.units || []
    item.stock_qty = data.quantity || 0
    item.last_purchase_price = data.last_purchase_price ?? 0
    // default sale_type and select first unit if present
    item.sale_type = 'wholesale'
    if (item.units.length) {
      item.selectedUnitId = item.units[0].id
      onUnitSelect(idx)
    } else {
      // ensure prices reset
      item.wholesale_price = 0
      item.retail_price = 0
      item.cost_price = 0
      item.quantity = 0
      item.total_price = 0
    }
  } catch (err) {
    console.error('onProductSelect error', err)
    snackbar.value = { show: true, color: 'error', message: 'Failed to load product details' }
  }
}

// ---------- Unit selection ----------
const onUnitSelect = (idx) => {
  const item = poItems.value[idx]
  const unit = item.units?.find(u => u.id === item.selectedUnitId)
  if (!unit) return
  item.wholesale_price = unit.wholesale_price ?? 0
  item.retail_price = unit.retail_price ?? 0
  item.is_returnable = unit.is_returnable ?? false
  item.container = unit.container || null
  // set default cost_price to selling price for chosen sale_type (keeps behavior consistent)
  const selling = item.sale_type === 'wholesale' ? item.wholesale_price : item.retail_price
  // only set cost if cost is zero (so user edits persist)
  if (!item.cost_price) item.cost_price = selling
  calculateTotal(item)
}

// ---------- Sale type change ----------
const updateSaleType = (item) => {
  // When sale_type changes we update displayed selling price and optionally adjust default cost
  const selling = item.sale_type === 'wholesale' ? item.wholesale_price : item.retail_price
  // If user hasn't entered custom cost, set cost to selling; else keep user-entered cost
  if (!item._manualCost) {
    item.cost_price = selling
  }
  calculateTotal(item)
}

// ---------- Edit handlers (cost / qty / total) ----------
const onCostChange = (item) => {
  // mark manual override
  item._manualCost = true
  // update total
  calculateTotal(item)
}

const onQuantityChange = (item) => {
  // recalc total from cost * qty
  calculateTotal(item)
}

const onTotalChange = (item) => {
  // user edited total directly -> derive cost if qty > 0
  if (item.quantity && item.quantity > 0) {
    // derive cost_price = total / qty
    item.cost_price = Number(item.total_price || 0) / Number(item.quantity || 1)
    // mark as manual cost because we changed it from user input
    item._manualCost = true
  } else {
    // if quantity is zero, leave cost as-is
    item.cost_price = Number(item.total_price || 0)
  }
}

// ---------- Calculations ----------
const calculateTotal = (item) => {
  // ensure numeric
  const qty = Number(item.quantity || 0)
  const cost = Number(item.cost_price || 0)
  item.total_price = +(qty * cost)
}

// ---------- Table operations ----------
const addRow = () => {
  poItems.value.push({
    id: null,
    product_id: null,
    product_name: '',
    selectedProduct: null,
    units: [],
    selectedUnitId: '',
    cost_price: 0,
    wholesale_price: 0,
    retail_price: 0,
    last_purchase_price: 0,
    sale_type: 'wholesale',
    quantity: 0,
    total_price: 0,
    stock_qty: 0,
    is_returnable: false,
    container: null,
    searchResults: [],
    loading: false,
    _manualCost: false
  })
}

const removeRow = (idx) => {
  poItems.value.splice(idx, 1)
}

// ---------- Fetch existing PO (edit) ----------
const fetchExistingPO = async (id) => {
  try {
    const res = await api.get(`/suppliers/orders/full_details/${id}`)
    const po = res.data
    // header
    poHeader.value.supplier_id = po.supplier_id
    poHeader.value.invoice_number = po.invoice_number
    poHeader.value.memo = po.memo || ''
    poHeader.value.purchase_date = po.purchase_date ? po.purchase_date.slice(0,10) : poHeader.value.purchase_date
    // set selectedSupplier if suppliers already loaded — otherwise set after fetchSuppliers
    selectedSupplier.value = suppliers.value.find(s => s.id === po.supplier_id) || null

    // items
    poItems.value = (po.items || []).map(i => {
      const units = i.units || []
      const selectedUnit = units.find(u => u.id === i.unit_id) || units[0] || null
      return {
        id: i.id,
        product_id: i.product_id,
        product_name: i.product_name,
        selectedProduct: { id: i.product_id, name: i.product_name },
        units,
        selectedUnitId: selectedUnit?.id || '',
        cost_price: Number(i.cost_price || 0),
        wholesale_price: Number(i.wholesale_price || 0),
        retail_price: Number(i.retail_price || 0),
        last_purchase_price: Number(i.last_purchase_price || 0),
        sale_type: i.sale_type || 'wholesale',
        quantity: Number(i.quantity || 0),
        total_price: Number(i.total_price || 0),
        stock_qty: Number(i.stock_qty || 0),
        is_returnable: i.is_returnable || false,
        container: i.container || null,
        searchResults: [{ id: i.product_id, name: i.product_name }],
        loading: false,
        _manualCost: !!i._manualCost
      }
    })
  } catch (err) {
    console.error('fetchExistingPO error', err)
    snackbar.value = { show: true, color: 'error', message: 'Failed to load purchase order' }
  }
}

// ---------- Validation & Save ----------
const validateForm = () => {
  errors.value = {}
  let valid = true
  if (!poHeader.value.supplier_id) { errors.value.supplier = 'Select supplier'; valid = false }
  if (!poHeader.value.invoice_number) { errors.value.invoice_number = 'Invoice required'; valid = false }
  if (!poHeader.value.purchase_date) { errors.value.purchase_date = 'Purchase date required'; valid = false }

  poItems.value.forEach((item, idx) => {
    if (!item.product_id) { errors.value[`product_${idx}`] = 'Select a product'; valid = false }
    if (!item.selectedUnitId) { errors.value[`unit_${idx}`] = 'Select a unit'; valid = false }
    if (!(Number(item.quantity) > 0)) { errors.value[`quantity_${idx}`] = 'Quantity > 0'; valid = false }
    if (Number(item.cost_price) < 0) { errors.value[`cost_${idx}`] = 'Cost invalid'; valid = false }
  })

  return valid
}

const savePurchaseOrder = async () => {
  if (!validateForm()) return

  const payload = {
    supplier_id: poHeader.value.supplier_id,
    invoice_number: poHeader.value.invoice_number,
    memo: poHeader.value.memo,
    purchase_date: poHeader.value.purchase_date,
    items: poItems.value.map(i => ({
      id: i.id,
      product_id: i.product_id,
      unit_id: i.selectedUnitId,
      sale_type: i.sale_type,
      quantity: i.quantity,
      cost_price: i.cost_price,
      is_returnable: i.is_returnable
    }))
  }

  try {
    let res
    if (isEditMode.value) {
      res = await api.put(`/suppliers/orders/${routeId}`, payload)
    } else {
      res = await api.post('/suppliers/orders', payload)
    }
    snackbar.value = { show: true, color: 'success', message: res.data.message || 'Saved!' }
    // navigate to the created/updated PO (backend expected to return po_id)
    const poId = res.data.po_id || routeId
    router.push(`/purchase-orders/${poId}`)
  } catch (err) {
    console.error('savePurchaseOrder error', err)
    snackbar.value = { show: true, color: 'error', message: err.response?.data?.error || err.message }
  }
}
</script>

<style>
/* Slide-fade for snackbar (optional) */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.4s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-12px);
  opacity: 0;
}
.slide-fade-enter-to,
.slide-fade-leave-from {
  transform: translateY(0);
  opacity: 1;
}
</style>
