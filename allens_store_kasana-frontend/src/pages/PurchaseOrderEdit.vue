<template>
    <div class="p-6 max-w-6xl mx-auto">
      <h1 class="text-2xl font-bold mb-4">Edit Purchase Order #{{ poId }}</h1>
  
      <!-- Purchase Order Form -->
      <div v-if="loaded">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label class="block font-semibold mb-1">Supplier</label>
            <select v-model="poHeader.supplier_id" class="border p-2 rounded w-full">
              <option value="" disabled>Select Supplier</option>
              <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
                {{ supplier.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block font-semibold mb-1">Invoice Number</label>
            <input type="text" v-model="poHeader.invoice_number" class="border p-2 rounded w-full" />
          </div>
          <div>
            <label class="block font-semibold mb-1">Memo / Details</label>
            <input type="text" v-model="poHeader.memo" class="border p-2 rounded w-full" />
          </div>
          <div>
            <label class="block font-semibold mb-1">Purchase Date</label>
            <input type="date" v-model="poHeader.purchase_date" class="border p-2 rounded w-full" />
          </div>
        </div>
  
        <!-- Items Table -->
        <table class="min-w-full border mb-4">
          <thead>
            <tr class="bg-gray-100">
              <th class="p-2 border">Product</th>
              <th class="p-2 border">Stock Qty</th>
              <th class="p-2 border">Cost Price</th>
              <th class="p-2 border">Unit</th>
              <th class="p-2 border">Quantity</th>
              <th class="p-2 border">Total Price</th>
              <th class="p-2 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in poItems" :key="idx">
              <td class="p-2 border relative">
                <input
                  type="text"
                  v-model="item.product_name"
                  @input="searchProduct(item)"
                  placeholder="Search product..."
                  class="border p-1 rounded w-full"
                />
                <ul v-if="item.searchResults.length" class="absolute bg-white border mt-1 max-h-32 overflow-auto z-10 w-full">
                  <li
                    v-for="product in item.searchResults"
                    :key="product.id"
                    @click="selectProduct(item, product)"
                    class="p-1 hover:bg-gray-200 cursor-pointer"
                  >
                    {{ product.name }} (Stock: {{ product.quantity }})
                  </li>
                </ul>
              </td>
              <td class="p-2 border">{{ item.stock_qty || 0 }}</td>
              <td class="p-2 border">
                <input type="number" v-model.number="item.cost_price" class="border p-1 rounded w-full" @input="calculateTotal(item)" />
              </td>
              <td class="p-2 border">{{ item.unit }}</td>
              <td class="p-2 border">
                <input
                  type="number"
                  v-model.number="item.quantity"
                  min="0"
                  class="border p-1 rounded w-full"
                  @input="validateQuantity(item)"
                />
                <p v-if="item.error" class="text-red-500 text-xs">{{ item.error }}</p>
              </td>
              <td class="p-2 border">{{ item.total_price.toFixed(2) }}</td>
              <td class="p-2 border">
                <button @click="removeRow(idx)" class="bg-red-500 text-white px-2 py-1 rounded">Remove</button>
              </td>
            </tr>
          </tbody>
        </table>
  
        <button @click="addRow" class="bg-green-500 text-white px-4 py-2 rounded mb-4">Add Item</button>
  
        <!-- Total -->
        <div class="text-right text-xl font-bold mb-6">
          Grand Total: {{ grandTotal.toFixed(2) }}
        </div>
  
        <button @click="updatePurchaseOrder" class="bg-indigo-600 text-white px-6 py-3 rounded">
          Update Purchase Order
        </button>
      </div>
  
      <div v-else>Loading...</div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import api from '../api';
  
  const route = useRoute();
  const router = useRouter();
  const poId = route.params.id;
  
  const poHeader = ref({});
  const poItems = ref([]);
  const suppliers = ref([]);
  const loaded = ref(false);
  
  const grandTotal = computed(() =>
    poItems.value.reduce((sum, item) => sum + item.total_price, 0)
  );
  
  const fetchSuppliers = async () => {
    const res = await api.get('/suppliers/');
    suppliers.value = res.data;
  };
  
  const fetchPurchaseOrder = async () => {
    try {
      const res = await api.get(`/suppliers/orders/${poId}`);
      const data = res.data;
  
      poHeader.value = {
        supplier_id: data.supplier_id,
        invoice_number: data.invoice_number,
        memo: data.memo || '',
        purchase_date: data.purchase_date.split('T')[0]
      };
  
      poItems.value = data.items.map(i => ({
        id: i.id,
        product_id: i.product_id,
        product_name: i.product_name,
        stock_qty: i.stock_quantity || 0,
        unit: i.unit || '',
        cost_price: i.unit_price,
        quantity: i.quantity,
        total_price: i.quantity * i.unit_price,
        searchResults: [],
        error: ''
      }));
  
      loaded.value = true;
    } catch (err) {
      alert('Error loading purchase order: ' + err.message);
    }
  };
  
  const searchProduct = async (item) => {
    if (!item.product_name || item.product_name.length < 2) return;
    const res = await api.get(`/inventory/products/search?name=${item.product_name}`);
    item.searchResults = res.data;
  };
  
  const selectProduct = (item, product) => {
    item.product_id = product.id;
    item.product_name = product.name;
    item.unit = product.unit;
    item.stock_qty = product.quantity;
    item.searchResults = [];
  };
  
  const calculateTotal = (item) => {
    item.total_price = (item.quantity || 0) * (item.cost_price || 0);
  };
  
  const validateQuantity = (item) => {
    if (item.quantity < 0) {
      item.error = 'Quantity cannot be negative';
      item.quantity = 0;
    } else {
      item.error = '';
    }
    calculateTotal(item);
  };
  
  const addRow = () => {
    poItems.value.push({
      product_id: null,
      product_name: '',
      stock_qty: 0,
      unit: '',
      cost_price: 0,
      quantity: 0,
      total_price: 0,
      searchResults: [],
      error: ''
    });
  };
  
  const removeRow = (idx) => poItems.value.splice(idx, 1);
  
  const updatePurchaseOrder = async () => {
    const payload = {
      supplier_id: poHeader.value.supplier_id,
      invoice_number: poHeader.value.invoice_number,
      memo: poHeader.value.memo,
      purchase_date: poHeader.value.purchase_date,
      items: poItems.value.map(i => ({
        id: i.id,
        product_id: i.product_id,
        quantity: i.quantity,
        unit_price: i.cost_price
      }))
    };
  
    try {
      await api.put(`/suppliers/orders/${poId}/edit`, payload);
      alert('Purchase order updated successfully!');
      router.push('/purchaselist');
    } catch (err) {
      alert('Error updating purchase order: ' + (err.response?.data?.error || err.message));
    }
  };
  
  onMounted(() => {
    fetchSuppliers();
    fetchPurchaseOrder();
  });
  </script>
  