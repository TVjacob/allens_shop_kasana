<template>
    <div class="w-full min-h-screen bg-gray-50 px-6 py-6">
      <!-- Page Header -->
      <h1 class="text-3xl font-bold mb-6 text-gray-800 text-center">Products Purchased Report</h1>
  
      <!-- Search -->
      <div class="flex flex-col md:flex-row justify-between items-center mb-4 gap-4">
        <input
          v-model="search"
          @input="fetchData"
          type="text"
          placeholder="Search by product, supplier, or invoice..."
          class="w-full md:w-1/2 border border-gray-300 rounded-xl p-3 text-lg focus:ring-2 focus:ring-indigo-400 transition"
        />
      </div>
  
      <!-- Totals Top -->
      <div class="mb-4 flex justify-end gap-6 text-lg font-semibold text-gray-700">
        <div>Total Orders: <span class="text-indigo-600">{{ purchaseOrders.length }}</span></div>
        <div>Grand Total: <span class="text-indigo-600">{{ formatPrice(grandTotal) }}</span></div>
      </div>
  
      <!-- Table -->
      <div class="overflow-x-auto bg-white rounded-lg shadow border border-gray-200">
        <table class="w-full table-auto border-collapse">
          <thead class="bg-gray-100 text-base">
            <tr>

              <th class="p-3 border">Invoice #</th>
              <th class="p-3 border">Supplier</th>
              <th class="p-3 border">Purchase Date</th>
              <th class="p-3 border">Product</th>
              <th class="p-3 border">Category</th>
              <th class="p-3 border text-center">Unit</th>
              <th class="p-3 border text-right">Unit Price</th>
              <th class="p-3 border text-center">Qty</th>
              <th class="p-3 border text-center">Converted Qty</th>
              <th class="p-3 border text-right">Total Price</th>
              <th class="p-3 border">Action </th>

            </tr>
          </thead>
  
          <tbody class="text-base">
            <template v-for="po in purchaseOrders" :key="po.purchase_order_id">
              <tr v-for="(item, idx) in po.items" :key="item.product_id + '-' + idx" class="hover:bg-gray-50 transition">


                <td class="p-3 border">{{ po.invoice_number }}</td>
                <td class="p-3 border">{{ po.supplier_name }}</td>
                <td class="p-3 border">{{ po.purchase_date }}</td>
                <td class="p-3 border">{{ item.product_name }}</td>
                <td class="p-3 border">{{ item.category_name }}</td>
                <td class="p-3 border text-center">{{ item.unit_name }}</td>
                <td class="p-3 border text-right">{{ formatPrice(item.unit_price) }}</td>
                <td class="p-3 border text-center">{{ item.quantity_purchased }}</td>
                <td class="p-3 border text-center">{{ item.converted_quantity }}</td>
                <td class="p-3 border text-right">{{ formatPrice(item.total_price) }}</td>
                <!-- Add Edit button only on the first row of the purchase order -->
                <td class="p-3 border text-center space-x-2">
                    <router-link
                    :to="`/purchase-orders/${po.purchase_order_id}/edit`"
                    class="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded shadow ml-2 transition transform hover:scale-105"
                    >
                    Edit
                    </router-link>
                </td>
              </tr>
            </template>
          </tbody>
  
          <!-- Totals Footer -->
          <tfoot class="bg-gray-100 font-bold text-base">
            <tr>
              <td class="p-3 border text-right" colspan="9">Grand Total:</td>
              <td class="p-3 border text-right">{{ formatPrice(grandTotal) }}</td>
            </tr>
          </tfoot>
        </table>
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
  import { ref, computed, onMounted, watch } from 'vue'
  import api from '@/api'
  import debounce from 'lodash.debounce'
  
  const purchaseOrders = ref([])
  const search = ref('')
  const snackbar = ref({ show: false, message: '', color: 'success' })
  
  // -------- Fetch Data --------
  const fetchData = debounce(async () => {
    try {
      const res = await api.get('reports/products_purhcased', { params: { search: search.value } })
      purchaseOrders.value = res.data.data
    } catch (err) {
      snackbar.value = { show: true, color: 'error', message: err.response?.data?.error || err.message }
    }
  }, 300)
  
  onMounted(fetchData)
  
  // -------- Computed Grand Total --------
  const grandTotal = computed(() => {
    return purchaseOrders.value.reduce((sum, po) => {
      return sum + po.items.reduce((itemSum, item) => itemSum + (item.total_price || 0), 0)
    }, 0)
  })
  
  // -------- Utils --------
  const formatPrice = (v) => new Intl.NumberFormat('en-UG').format(v || 0)
  
  // -------- Watch search input --------
  watch(search, () => fetchData())
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
  