<template>
  <div class="p-6 max-w-6xl mx-auto bg-white shadow-lg rounded-lg">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Purchase Order Dashboard</h1>

    <!-- -------- Header Section -------- -->
    <div class="grid grid-cols-2 gap-4 mb-6">
      <!-- Supplier -->
      <v-autocomplete
        label="Supplier"
        v-model="selectedSupplier"
        :items="suppliers"
        item-title="name"
        :item-value="s => s"
        density="comfortable"
        clearable
        variant="outlined"
        :loading="loadingSuppliers"
        @update:model-value="selectSupplier"
      ></v-autocomplete>
      <p v-if="errors.supplier" class="text-red-500 text-sm col-span-2">{{ errors.supplier }}</p>

      <!-- Invoice -->
      <div>
        <label class="block font-semibold mb-1">Invoice Number</label>
        <input
          v-model="poHeader.invoice_number"
          type="text"
          class="w-full border border-gray-300 rounded-lg p-2"
        />
        <p v-if="errors.invoice_number" class="text-red-500 text-sm">{{ errors.invoice_number }}</p>
      </div>

      <!-- Purchase Date -->
      <div>
        <label class="block font-semibold mb-1">Purchase Date</label>
        <input
          v-model="poHeader.purchase_date"
          type="date"
          class="w-full border border-gray-300 rounded-lg p-2"
        />
        <p v-if="errors.purchase_date" class="text-red-500 text-sm">{{ errors.purchase_date }}</p>
      </div>

      <!-- Memo -->
      <div>
        <label class="block font-semibold mb-1">Memo</label>
        <input
          v-model="poHeader.memo"
          type="text"
          class="w-full border border-gray-300 rounded-lg p-2"
        />
      </div>
    </div>

    <!-- -------- Items Table -------- -->
    <table class="w-full border rounded-lg overflow-hidden relative">
      <thead class="bg-gray-100 text-sm">
        <tr>
          <th class="p-2 border">Product</th>
          <th class="p-2 border">Unit</th>
          <th class="p-2 border">Stock</th>
          <th class="p-2 border">Buying price</th>
          <th class="p-2 border">Wholesale</th>
          <th class="p-2 border">Retail</th>
          <th class="p-2 border">Quantity</th>
          <th class="p-2 border">Total</th>
          <th class="p-2 border">Action</th>
        </tr>
      </thead>

      <tbody>
        <template v-for="(item, idx) in poItems" :key="idx">
          <!-- Product Row -->
          <tr class="relative hover:bg-gray-50 transition">
            <!-- Product -->
            <td class="p-2 border w-64">
              <v-autocomplete
                v-model="item.selectedProduct"
                :items="item.searchResults"
                item-title="name"
                :item-value="p => p"
                label="Search product..."
                density="comfortable"
                clearable
                hide-details
                :loading="item.loading"
                @update:search="(val) => onProductSearch(val, idx)"
                @update:model-value="(product) => onProductSelect(product, idx)"
              ></v-autocomplete>
              <p v-if="errors[`product_${idx}`]" class="text-red-500 text-xs">{{ errors[`product_${idx}`] }}</p>
            </td>

            <!-- Unit -->
            <td class="p-2 border text-center">
              <select
                v-if="item.units?.length"
                v-model="item.selectedUnitId"
                @change="onUnitSelect(idx)"
                class="border border-gray-300 rounded-lg p-1 w-full"
              >
                <option disabled value="">Select Unit</option>
                <option
                  v-for="u in item.units"
                  :key="u.id"
                  :value="u.id"
                >
                  {{ u.unit_name }}
                </option>
              </select>
            </td>

            <!-- Stock -->
            <td class="p-2 border text-center">{{ item.stock_qty }}</td>

            <!-- Editable Cost -->
            <td class="p-2 border text-right">
              <input
                type="number"
                min="0"
                v-model.number="item.cost_price"
                @input="calculateTotal(item)"
                class="w-full text-right border border-gray-300 rounded-lg p-1"
              />
              <p v-if="errors[`cost_${idx}`]" class="text-red-500 text-xs">{{ errors[`cost_${idx}`] }}</p>
            </td>

            <!-- Wholesale / Retail -->
            <td class="p-2 border text-right">{{ formatPrice(item.wholesale_price) }}</td>
            <td class="p-2 border text-right">{{ formatPrice(item.retail_price) }}</td>

            <!-- Quantity -->
            <td class="p-2 border">
              <input
                type="number"
                min="0"
                v-model.number="item.quantity"
                @input="calculateTotal(item)"
                class="w-full text-right border border-gray-300 rounded-lg p-2"
              />
              <p v-if="errors[`quantity_${idx}`]" class="text-red-500 text-xs">{{ errors[`quantity_${idx}`] }}</p>
            </td>

            <!-- Total -->
            <td class="p-2 border text-right font-semibold">{{ formatPrice(item.total_price) }}</td>

            <!-- Action -->
            <td class="p-2 border text-center">
              <button
                @click="removeRow(idx)"
                class="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                ✕
              </button>
            </td>
          </tr>

          <!-- Container Row -->
          <tr v-if="item.container" class="bg-gray-50 text-sm text-gray-700">
            <td colspan="9" class="p-2 border-l-4 border-indigo-400">
              <div class="flex justify-between items-center">
                <div>
                  🧃 Container:
                  <strong>{{ item.container.name }}</strong>
                  <span class="text-gray-500 ml-1">(Value: {{ formatPrice(item.container.unit_value) }})</span>
                </div>
                <span class="italic text-indigo-600">Returnable</span>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <!-- Totals -->
    <div class="flex justify-between items-center mt-6">
      <button
        @click="addRow"
        class="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600"
      >
        + Add Product
      </button>

      <div class="text-xl font-bold">
        Grand Total: <span class="text-indigo-600">{{ formatPrice(grandTotal) }}</span>
      </div>
    </div>

    <!-- Save -->
    <div class="mt-6 text-right">
      <button
        @click="savePurchaseOrder"
        class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
      >
        Save Purchase Order
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
import { useRouter } from 'vue-router'
import debounce from 'lodash.debounce'
import api from '../api'

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

const savePurchaseOrder = async () => {
  if (!validateForm()) return

  const payload = {
    supplier_id: poHeader.value.supplier_id,
    invoice_number: poHeader.value.invoice_number,
    memo: poHeader.value.memo,
    purchase_date: poHeader.value.purchase_date,
    items: poItems.value.map(i => ({
      product_id: i.product_id,
      unit_id: i.selectedUnitId,
      quantity: i.quantity,
      cost_price: i.cost_price,
      is_returnable: i.is_returnable,
    })),
  }

  try {
    const res = await api.post('/suppliers/orders', payload)
    snackbar.value = { show: true, color: 'success', message: res.data.message || 'Saved!' }
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
