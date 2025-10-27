<template>
  <div class="p-6 max-w-6xl mx-auto bg-white shadow-lg rounded-lg">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Purchase Order Dashboard</h1>

    <!-- --------- Purchase Order Header --------- -->
    <div class="grid grid-cols-2 gap-4 mb-6">
      <!-- Supplier Combobox -->
      <v-autocomplete
        label="Supplier"
        v-model="selectedSupplierObj"
        :items="suppliers"
        item-title="name"
        item-value="id"
        density="comfortable"
        clearable
        variant="outlined"
        :loading="loadingSuppliers"
        @update:model-value="selectSupplierById"
      ></v-autocomplete>

      <div>
        <label class="block font-semibold mb-1">Invoice Number</label>
        <input
          type="text"
          v-model="poHeader.invoice_number"
          class="w-full border border-gray-300 rounded-lg p-2"
        />
        <p v-if="errors.invoice_number" class="text-red-500 text-sm">{{ errors.invoice_number }}</p>
      </div>

      <div>
        <label class="block font-semibold mb-1">Purchase Date</label>
        <input
          type="date"
          v-model="poHeader.purchase_date"
          class="w-full border border-gray-300 rounded-lg p-2"
        />
      </div>

      <div>
        <label class="block font-semibold mb-1">Memo</label>
        <input
          type="text"
          v-model="poHeader.memo"
          class="w-full border border-gray-300 rounded-lg p-2"
        />
      </div>
    </div>

    <!-- --------- Product Items Table --------- -->
    <table class="w-full border rounded-lg overflow-hidden relative">
      <thead>
        <tr class="bg-gray-100">
          <th class="p-2 border">Product</th>
          <th class="p-2 border">Stock</th>
          <th class="p-2 border">Cost Price</th>
          <th class="p-2 border">Unit</th>

          <th class="p-2 border">Quantity</th>
          <th class="p-2 border">Total</th>
          <th class="p-2 border">Action</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="(item, idx) in poItems" :key="idx" class="relative">
          <!-- Product Combobox -->
          <td class="p-2 border w-64">
            <v-autocomplete
              v-model="item.selectedProductObj"
              :items="item.searchResults"
              item-title="name"
              item-value="id"
              label="Search product..."
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              :loading="item.loading"
              @update:search="(val) => onProductSearch(val, idx)"
              @update:model-value="(id) => onProductSelect(id, idx)"
            ></v-autocomplete>
          </td>

          <td class="p-2 border text-center">{{ item.stock_qty }}</td>

          <td class="p-2 border">
            <input
              type="number"
              v-model.number="item.cost_price"
              @input="calculateTotal(item)"
              class="w-full text-right border border-gray-300 rounded-lg p-2"
            />
          </td>
          <td class="p-2 border text-center">{{ item.category_name }}</td>

          <td class="p-2 border">
            <input
              type="number"
              v-model.number="item.quantity"
              @input="validateQuantity(item)"
              class="w-full text-right border border-gray-300 rounded-lg p-2"
            />
          </td>

          <td class="p-2 border text-right font-semibold">
            {{ item.total_price.toLocaleString() }}
          </td>

          <td class="p-2 border text-center">
            <button
              @click="removeRow(idx)"
              class="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              ✕
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Add Product + Totals -->
    <div class="flex justify-between items-center mt-6">
      <button
        @click="addRow"
        class="px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600"
      >
        + Add Product
      </button>

      <div class="text-xl font-bold">
        Grand Total: <span class="text-indigo-600">{{ grandTotal.toLocaleString() }}</span>
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
    <transition name="slide-fade">
      <v-snackbar
        v-if="snackbar.show"
        v-model="snackbar.show"
        :color="snackbar.color"
        timeout="3000"
        location="top-right"
      >
        {{ snackbar.message }}
      </v-snackbar>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import debounce from 'lodash.debounce'
import api from '../api'

// ----------------- Header -----------------
const poHeader = ref({
  supplier_id: '',
  supplier_name: '',
  invoice_number: '',
  memo: '',
  purchase_date: new Date().toISOString().slice(0, 10),
})

// ----------------- State -----------------
const poItems = ref([])
const suppliers = ref([])
const selectedSupplierObj = ref(null)
const errors = ref({})
const loadingSuppliers = ref(false)

// ----------------- Snackbar -----------------
const router = useRouter()
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
})

// ----------------- Computed -----------------
const grandTotal = computed(() =>
  poItems.value.reduce((sum, item) => sum + (item.total_price || 0), 0)
)

// ----------------- Supplier Logic -----------------
const fetchSuppliers = async () => {
  loadingSuppliers.value = true
  try {
    const res = await api.get('/suppliers/')
    suppliers.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    loadingSuppliers.value = false
  }
}

const selectSupplierById = (id) => {
  const supplier = suppliers.value.find((s) => s.id === id)
  if (supplier) {
    selectedSupplierObj.value = supplier
    poHeader.value.supplier_id = supplier.id
    poHeader.value.supplier_name = supplier.name
    errors.value.supplier = ''
  } else {
    selectedSupplierObj.value = null
    poHeader.value.supplier_id = ''
    poHeader.value.supplier_name = ''
  }
}

// ----------------- Product Logic -----------------
const debouncedSearchProduct = debounce(async (query, idx) => {
  if (!query?.trim()) {
    poItems.value[idx].searchResults = []
    return
  }
  poItems.value[idx].loading = true
  try {
    const res = await api.get(`/inventory/products/search`, { params: { name: query } })
    poItems.value[idx].searchResults = res.data.slice(0, 15).map((p) => ({
      id: p.id,
      name: `${p.name} — Stock: ${p.quantity ?? 0}`,
      quantity: p.quantity ?? 0,
      category_name: p.category_name ?? '',
      price: p.price ?? 0,
    }))
  } catch (err) {
    console.error(err)
  } finally {
    poItems.value[idx].loading = false
  }
}, 400)

const onProductSearch = (val, idx) => {
  debouncedSearchProduct(val, idx)
}

const onProductSelect = (id, idx) => {
  const product = poItems.value[idx].searchResults.find((p) => p.id === id)
  const item = poItems.value[idx]
  if (product) {
    item.selectedProductObj = product
    item.product_id = product.id
    item.product_name = product.name
    item.stock_qty = product.quantity
    item.category_name = product.category_name
    item.cost_price = product.price || 0
    item.quantity = 0
    item.total_price = 0
  } else {
    item.selectedProductObj = null
    item.product_id = null
    item.product_name = ''
    item.stock_qty = 0
    item.category_name = ''
    item.cost_price = 0
    item.quantity = 0
    item.total_price = 0
  }
}

// ----------------- Rows -----------------
const addRow = () => {
  poItems.value.push({
    product_id: null,
    product_name: '',
    stock_qty: 0,
    category_name: '',
    cost_price: 0,
    quantity: 0,
    total_price: 0,
    searchResults: [],
    loading: false,
    selectedProductObj: null,
  })
}

const removeRow = (idx) => poItems.value.splice(idx, 1)

const validateQuantity = (item) => {
  if (item.quantity < 0) item.quantity = 0
  calculateTotal(item)
}

const calculateTotal = (item) => {
  item.total_price = (item.quantity || 0) * (item.cost_price || 0)
}

// ----------------- Save PO -----------------
const savePurchaseOrder = async () => {
  errors.value = {}
  if (!poHeader.value.supplier_id) {
    errors.value.supplier = 'Select supplier'
    return
  }
  if (!poHeader.value.invoice_number) {
    errors.value.invoice_number = 'Invoice required'
    return
  }

  for (const item of poItems.value) {
    if (!item.product_id) return alert('Select product for all rows')
    if (item.quantity <= 0)
      return alert(`Quantity > 0 required for ${item.product_name}`)
  }

  const payload = {
    supplier_id: poHeader.value.supplier_id,
    invoice_number: poHeader.value.invoice_number,
    memo: poHeader.value.memo,
    purchase_date: poHeader.value.purchase_date,
    items: poItems.value.map((i) => ({
      product_id: i.product_id,
      quantity: i.quantity,
      cost_price: i.cost_price,
    })),
  }

  try {
    const res = await api.post('/suppliers/orders', payload)

    // Show snackbar
    snackbar.value.message = res.data.message || `PO created successfully!`
    snackbar.value.color = 'success'
    snackbar.value.show = true

    // Navigate after short delay
    setTimeout(() => {
      router.push(`/purchase-orders/${res.data.po_id}`)
    }, 1000)

    // Reset form
    poHeader.value = {
      supplier_id: '',
      supplier_name: '',
      invoice_number: '',
      memo: '',
      purchase_date: new Date().toISOString().slice(0, 10),
    }
    selectedSupplierObj.value = null
    poItems.value = []
    addRow()
  } catch (err) {
    snackbar.value.message = err.response?.data?.error || err.message
    snackbar.value.color = 'error'
    snackbar.value.show = true
  }
}

// ----------------- Lifecycle -----------------
onMounted(() => {
  fetchSuppliers()
  addRow()
})
</script>

<style>
.slide-fade-enter-active {
  transition: all 0.5s ease;
}
.slide-fade-leave-active {
  transition: all 0.5s ease;
}
.slide-fade-enter-from {
  transform: translateY(-20px);
  opacity: 0;
}
.slide-fade-enter-to {
  transform: translateY(0);
  opacity: 1;
}
.slide-fade-leave-from {
  transform: translateY(0);
  opacity: 1;
}
.slide-fade-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}
</style>
