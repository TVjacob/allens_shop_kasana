<template>
  <div class="w-full min-h-screen bg-gray-50 px-6 py-6">
    <!-- Page Header -->
    <h1 class="text-3xl font-bold mb-6 text-gray-800 text-center">Purchase Order Dashboard</h1>

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
            <th class="p-3 border min-w-[140px] text-center">Unit</th>
            <th class="p-3 border min-w-[100px] text-center">Stock</th>
            <th class="p-3 border min-w-[120px] text-center">Rate</th>
            <th class="p-3 border min-w-[120px] text-center">Divide by</th>
            <th class="p-3 border min-w-[120px] text-center">Buying Price</th>
            <th class="p-3 border min-w-[120px] text-center">Wholesale</th>
            <th class="p-3 border min-w-[120px] text-center">Retail</th>
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
                <span
                  v-if="item.selectedProduct"
                  class="block text-gray-800 mt-1 font-semibold text-lg"
                >
                  Selected: {{ item.selectedProduct.name }}
                </span>
                <p v-if="errors[`product_${idx}`]" class="text-red-600 text-sm mt-1">
                  {{ errors[`product_${idx}`] }}
                </p>
              </td>

              <!-- Unit -->
              <td class="p-3 border text-center min-w-[140px]">
                <v-autocomplete
                  v-if="item.units && item.units.length"
                  v-model="item.selectedUnitId"
                  :items="item.units"
                  item-title="unit_name"
                  item-value="id"
                  label="Unit"
                  variant="outlined"
                  hide-details
                  class="text-base"
                  @update:model-value="val => onUnitSelect(idx)"
                ></v-autocomplete>
              </td>

              <!-- Stock -->
              <td class="p-3 border text-center">{{ item.stock_qty }}</td>


              <td class="p-3 border" v-if="Number(item.conversion_quantity) <= 1">
                <input
                  type="number"
                  v-model.number="item.rate"
                  min="0"
                  placeholder="0"
                  @input="recalculateUnitPrice(item)"
                  class="w-full border border-gray-300 rounded-xl p-2 text-base focus:ring-2 focus:ring-indigo-400 transition"
                />
              </td>
              <td class="p-3 border" v-else></td>


              <td class="p-3 border"  v-if="Number(item.conversion_quantity) <= 1">
                <input
                  type="number"
                  v-model.number="item.quantity_number"
                  min="1"
                  placeholder="1"
                  @input="recalculateQuantityRate(item)"
                  class="w-full border border-gray-300 rounded-xl p-2 text-base focus:ring-2 focus:ring-indigo-400 transition"
                />
              </td>
              <td class="p-3 border" v-else></td>


              <!-- Buying Price -->
              <td class="p-3 border">
                <input
                  type="number"
                  v-model.number="item.cost_price"
                  min="0"
                  @input="calculateTotal(item)"
                  class="w-full border border-gray-300 rounded-xl p-2 text-base focus:ring-2 focus:ring-indigo-400 transition text-right"
                />
                <p v-if="errors[`cost_${idx}`]" class="text-red-600 text-sm mt-1">
                  {{ errors[`cost_${idx}`] }}
                </p>
              </td>

              <!-- Wholesale -->
              <td class="p-3 border text-center">{{ formatPrice(item.wholesale_price) }}</td>

              <!-- Retail -->
              <td class="p-3 border text-center">{{ formatPrice(item.retail_price) }}</td>

              <!-- Quantity -->
              <td class="p-3 border">
                <input
                  type="number"
                  v-model.number="item.quantity"
                  min="0"
                  @input="calculateTotal(item)"
                  class="w-full border border-gray-300 rounded-xl p-2 text-base focus:ring-2 focus:ring-indigo-400 transition text-right"
                />
                <p v-if="errors[`quantity_${idx}`]" class="text-red-600 text-sm mt-1">
                  {{ errors[`quantity_${idx}`] }}
                </p>
              </td>

              <!-- Total -->
              <td class="p-3 border text-right font-bold text-indigo-700">
                {{ formatPrice(item.total_price) }}
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

            <!-- Container Row -->
            <tr v-if="item.container" class="bg-gray-50 text-sm text-gray-700">
              <td colspan="11" class="p-2 border-l-4 border-indigo-400">
                <div class="flex justify-between items-center">
                  <div>
                    🧃 Container:
                    <strong>{{ item.container?.name || 'N/A' }}</strong>
                    <span class="text-gray-500 ml-1">(Value: {{ formatPrice(item.container?.unit_value || 0) }})</span>
                  </div>
                  <span class="italic text-indigo-600">Returnable</span>
                </div>
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
import { ref, computed, onMounted } from 'vue'
// import { useRouter } from 'vue-router'
import { useRoute, useRouter } from 'vue-router';

import debounce from 'lodash.debounce'

import api from '../api'

const route = useRoute()
const isEditMode = computed(() => !!route.params.id)

const router = useRouter()

// -------- State --------
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

// -------- Computed --------
const grandTotal = computed(() =>
  poItems.value.reduce((sum, item) => sum + (item.total_price || 0), 0)
)

onMounted(() => {
  fetchSuppliers()
  if (isEditMode.value) {
    fetchExistingPO(route.params.id)
  } else {
    addRow()
  }
})


// -------- Supplier Logic --------
const fetchSuppliers = async () => {
  loadingSuppliers.value = true
  try {
    const res = await api.get('/suppliers/')
    suppliers.value = res.data
  } catch (e) {
    console.error('Failed to fetch suppliers:', e)
  } finally {
    loadingSuppliers.value = false
  }
}

const fetchExistingPO = async (id) => {
  try {
    const res = await api.get(`/suppliers/orders/full_details/${id}`)
    const po = res.data

    poHeader.value = {
      supplier_id: po.supplier_id,
      invoice_number: po.invoice_number,
      memo: po.memo || '',
      purchase_date: po.purchase_date.slice(0, 10),
    }

    selectedSupplier.value = suppliers.value.find(s => s.id === po.supplier_id)

    poItems.value = po.items.map(i => ({
      id: i.id,
      product_id: i.product_id,
      selectedProduct: { id: i.product_id, name: i.product_name },
      selectedUnitId: i.unit_id,
      units: i.units || [],
      cost_price: i.cost_price,
      wholesale_price: i.wholesale_price || 0,
      retail_price: i.retail_price || 0,
      quantity: i.quantity,
      total_price: i.total_price,
      is_returnable: i.is_returnable,
      container: i.container,
      stock_qty: i.stock_qty || 0,
      searchResults: [],
      rate: i.cost_price * (i.conversion_quantity || 1),
      quantity_number: i.conversion_quantity || 1,
    }))
  } catch (err) {
    console.error('Failed to fetch purchase order:', err)
    snackbar.value = { show: true, color: 'error', message: 'Failed to load purchase order' }
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

// -------- Product Logic --------
const debouncedSearchProduct = debounce(async (query, idx) => {
  const item = poItems.value[idx]
  if (!query?.trim()) {
    item.searchResults = []
    return
  }
  item.loading = true
  try {
    const res = await api.get('/inventory/products/search', { params: { name: query } })
    item.searchResults = res.data.map(p => ({
      id: p.id,
      name: p.name+' : '+p.category_name,
      stock_qty: p.quantity || 0,
    }))
  } catch (e) {
    console.error('Product search failed:', e)
  } finally {
    item.loading = false
  }
}, 400)

const onProductSearch = (val, idx) => debouncedSearchProduct(val, idx)

const onProductSelect = async (product, idx) => {
  const item = poItems.value[idx]
  if (!product?.id) {
    // Cleared selection
    item.product_id = null
    item.product_name = ''
    item.units = []
    item.selectedUnitId = ''
    item.cost_price = 0
    item.wholesale_price = 0
    item.retail_price = 0
    item.quantity = 0
    item.total_price = 0
    item.container = null
    item.rate =0 
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
    item.selectedUnitId = ''
    item.cost_price = 0
    item.wholesale_price = 0
    item.retail_price = 0
    item.quantity = 0
    item.total_price = 0
    item.container = null
  } catch (err) {
    console.error('Failed to fetch product:', err)
    snackbar.value = { show: true, color: 'error', message: 'Failed to fetch product. Check network or backend.' }
  }
}

const onUnitSelect = (idx) => {
  const item = poItems.value[idx]
  const unit = item.units.find(u => u.id === item.selectedUnitId)
  if (!unit) return
  // item.cost_price = unit.cost_price ?? 0
  item.wholesale_price = unit.wholesale_price ?? 0
  item.retail_price = unit.retail_price ?? 0
  item.is_returnable = unit.is_returnable ?? false
  item.container = unit.container || null
  item.rate =0 
  item.conversion_quantity =unit.conversion_quantity
  calculateTotal(item)
}
const recalculateQuantityRate = (item) => {
  if (item.quantity_number > 0) {
    item.cost_price = item.rate / item.quantity_number
  } else {
    item.cost_price = item.wholesale_price || 0
  }
  calculateTotal(item)
}
const recalculateUnitPrice = (item) => {
  if (item.rate && item.rate > 0) {
    item.cost_price = item.rate / (item.quantity_number || item.conversion_quantity || 1)
  } else {
    item.cost_price = item.wholesale_price || 0
  }
  calculateTotal(item)
}
// -------- Table Logic --------
const addRow = () => {
  poItems.value.push({
    product_id: null,
    product_name: '',
    units: [],
    selectedProduct: null,
    selectedUnitId: '',
    cost_price: 0,
    wholesale_price: 0,
    retail_price: 0,
    quantity: 0,
    total_price: 0,
    searchResults: [],
    rate: 0, // 🔹 newly added
    quantity_number: 24, // ✅ newly added
    conversion_quantity:1,
    loading: false,
    container: null,
  })
}

const removeRow = (idx) => poItems.value.splice(idx, 1)

const calculateTotal = (item) => {
  item.total_price = (item.quantity || 0) * (item.cost_price || 0)
}

const formatPrice = (v) => new Intl.NumberFormat('en-UG').format(v || 0)

// -------- Validation & Save --------
const validateForm = () => {
  errors.value = {}
  let valid = true

  if (!poHeader.value.supplier_id) {
    errors.value.supplier = 'Select supplier'
    valid = false
  }
  if (!poHeader.value.invoice_number) {
    errors.value.invoice_number = 'Invoice required'
    valid = false
  }
  if (!poHeader.value.purchase_date) {
    errors.value.purchase_date = 'Purchase date required'
    valid = false
  }

  poItems.value.forEach((item, idx) => {
    if (!item.product_id) {
      errors.value[`product_${idx}`] = 'Select a product'
      valid = false
    }
    if (item.quantity <= 0) {
      errors.value[`quantity_${idx}`] = 'Quantity must be > 0'
      valid = false
    }
    if (item.cost_price < 0) {
      errors.value[`cost_${idx}`] = 'Cost cannot be negative'
      valid = false
    }
  })

  return valid
}

// const savePurchaseOrder = async () => {
//   if (!validateForm()) return

//   const payload = {
//     supplier_id: poHeader.value.supplier_id,
//     invoice_number: poHeader.value.invoice_number,
//     memo: poHeader.value.memo,
//     purchase_date: poHeader.value.purchase_date,
//     items: poItems.value.map(i => ({
//       product_id: i.product_id,
//       unit_id: i.selectedUnitId,
//       quantity: i.quantity,
//       cost_price: i.cost_price,
//       is_returnable: i.is_returnable,
//     })),
//   }

//   try {
//     const res = await api.post('/suppliers/orders', payload)
//     snackbar.value = { show: true, color: 'success', message: res.data.message || 'Saved!' }
//     router.push(`/purchase-orders/${res.data.po_id}`)
//   } catch (err) {
//     snackbar.value = { show: true, color: 'error', message: err.response?.data?.error || err.message }
//   }
// }



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
      quantity: i.quantity,
      cost_price: i.cost_price,
      is_returnable: i.is_returnable,
    })),
  }

  try {
    let res
    if (isEditMode.value) {
      res = await api.put(`/suppliers/orders/${route.params.id}`, payload)
    } else {
      res = await api.post('/suppliers/orders', payload)
    }

    snackbar.value = { show: true, color: 'success', message: res.data.message || 'Saved!' }
    // router.push('/purchase-orders')
    router.push(`/purchase-orders/${res.data.po_id}`)

  } catch (err) {
    snackbar.value = { show: true, color: 'error', message: err.response?.data?.error || err.message }
  }
}


// -------- Lifecycle --------
onMounted(() => {
  fetchSuppliers()
  addRow()
})
</script>

<style>
/* Slide-fade for snackbar */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.5s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}
.slide-fade-enter-to,
.slide-fade-leave-from {
  transform: translateY(0);
  opacity: 1;
}
</style>
