<template>
    <div class="p-6 max-w-6xl mx-auto">
        <div>
    <button
      @click="goBack"
      class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded shadow"
    >
      ← Back to Purchase List
    </button>
  </div>
      <div class="flex justify-between items-center mb-4 no-print">
        <h1 class="text-2xl font-bold">Purchase Order Details</h1>
        <button
          @click="printPage"
          class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded shadow"
        >
          Print
        </button>
      </div>
  
      <div v-if="loading" class="text-gray-500">Loading...</div>
  
      <!-- Printable Section -->
      <div id="print-section" v-else>
        <!-- Supplier Info -->
        <div class="bg-gray-100 p-4 rounded mb-6 shadow">
          <h2 class="text-lg font-bold mb-2">Supplier Information</h2>
          <p><strong>Name:</strong> {{ purchaseOrder.supplier.name }}</p>
          <p><strong>Contact:</strong> {{ purchaseOrder.supplier.contact }}</p>
          <p><strong>Email:</strong> {{ purchaseOrder.supplier.email }}</p>
          <p><strong>Invoice #:</strong> {{ purchaseOrder.invoice_number }}</p>
          <p><strong>Purchase Date:</strong> {{ formatDate(purchaseOrder.purchase_date) }}</p>
        </div>
  
        <!-- Items Table -->
        <div class="mb-6">
          <h2 class="text-lg font-bold mb-2">Ordered Items</h2>
          <table class="min-w-full border">
            <thead>
              <tr class="bg-gray-200">
                <th class="p-2 border">Product</th>
                <th class="p-2 border">Quantity</th>
                <th class="p-2 border">Unit Price</th>
                <th class="p-2 border">Total Price</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in purchaseOrder.items" :key="item.product_id">
                <td class="p-2 border">{{ item.product_name }}</td>
                <td class="p-2 border">{{ item.quantity }}</td>
                <td class="p-2 border">{{ formatCurrency(item.unit_price) }}</td>
                <td class="p-2 border">{{ formatCurrency(item.total_price) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
  
        <!-- Payments Table -->
        <div class="mb-6">
          <h2 class="text-lg font-bold mb-2">Payments Made</h2>
          <table class="min-w-full border">
            <thead>
              <tr class="bg-gray-200">
                <th class="p-2 border">Payment Date</th>
                <th class="p-2 border">Amount</th>
                <th class="p-2 border">Type</th>
                <th class="p-2 border">Reference</th>
                <th class="p-2 border">Account</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="purchaseOrder.payments.length === 0">
                <td colspan="5" class="p-2 text-center text-gray-500">
                  No payments recorded
                </td>
              </tr>
              <tr v-for="payment in purchaseOrder.payments" :key="payment.payment_id">
                <td class="p-2 border">{{ formatDate(payment.payment_date) }}</td>
                <td class="p-2 border">{{ formatCurrency(payment.amount) }}</td>
                <td class="p-2 border">{{ payment.payment_type }}</td>
                <td class="p-2 border">{{ payment.reference || '-' }}</td>
                <td class="p-2 border">{{ payment.account_id }}</td>
              </tr>
            </tbody>
          </table>
        </div>
  
        <!-- Summary -->
        <div class="bg-gray-100 p-4 rounded shadow">
          <h2 class="text-lg font-bold mb-2">Summary</h2>
          <p><strong>Total Amount:</strong> {{ formatCurrency(purchaseOrder.summary.total_amount) }}</p>
          <p><strong>Total Paid:</strong> {{ formatCurrency(purchaseOrder.summary.total_paid) }}</p>
          <p>
            <strong>Balance:</strong>
            <span
              :class="purchaseOrder.summary.balance === 0 ? 'text-green-600 font-bold' : 'text-red-600 font-bold'"
            >
              {{ formatCurrency(purchaseOrder.summary.balance) }}
            </span>
          </p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRoute,useRouter } from 'vue-router';
  import api from '@/api';
  
  const route = useRoute();
  const purchaseOrder = ref(null);
  const loading = ref(true);
  const router = useRouter(); // <-- define router here




  const goBack = () => {
  router.push('/purchaselist'); // navigate to /purchaselist
};
  
  const fetchPurchaseOrderDetails = async () => {
    try {
      const res = await api.get(`/suppliers/purchase-order/${route.params.id}`);
      purchaseOrder.value = res.data;
    } catch (err) {
      console.error('Error fetching purchase order details', err);
    } finally {
      loading.value = false;
    }
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString();
  };
  
  const formatCurrency = (value) => {
    if (value == null) return 'UGX 0';
    return new Intl.NumberFormat('en-UG', {
      style: 'currency',
      currency: 'UGX',
      currencyDisplay: 'code',
      minimumFractionDigits: 0,
    }).format(value);
  };
  
  const printPage = () => {
    window.print();
  };
  
  onMounted(fetchPurchaseOrderDetails);
  </script>
  
  <style>
  /* Hide all elements except print-section during printing */
  @media print {
    body * {
      visibility: hidden !important;
    }
    #print-section,
    #print-section * {
      visibility: visible !important;
    }
    #print-section {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
    }
    /* Hide Print button in print view */
    .no-print {
      display: none !important;
    }
  }
  </style>
  