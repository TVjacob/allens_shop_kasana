<template>
    <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
    >
      <div class="bg-white rounded-xl shadow-lg p-6 w-4/5 max-w-5xl relative overflow-auto max-h-[90vh]">
        <button
          @click="$emit('update:show', false)"
          class="absolute top-4 right-4 text-gray-500 hover:text-gray-800"
        >
          ✖
        </button>
  
        <h2 class="text-xl font-bold mb-4">
          {{ report.document_type }} - Sale #{{ report.sale_number }}
        </h2>
  
        <div class="mb-4">
          <h3 class="font-bold">Customer Info</h3>
          <p><strong>Name:</strong> {{ report.customer.name }}</p>
          <p><strong>Phone:</strong> {{ report.customer.phone }}</p>
          <p><strong>Email:</strong> {{ report.customer.email }}</p>
          <p><strong>Address:</strong> {{ report.customer.address }}</p>
        </div>
  
        <h3 class="font-bold mt-4">Items Sold</h3>
        <table class="min-w-full border mt-2">
          <thead>
            <tr class="bg-gray-100">
              <th class="p-2 border">Product</th>
              <th class="p-2 border">Quantity</th>
              <th class="p-2 border">Unit Price</th>
              <th class="p-2 border">Total Price</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in report.items" :key="item.product_name">
              <td class="p-2 border">{{ item.product_name }}</td>
              <td class="p-2 border">{{ item.quantity }}</td>
              <td class="p-2 border">{{ formatCurrency(item.unit_price) }}</td>
              <td class="p-2 border">{{ formatCurrency(item.total_price) }}</td>
            </tr>
          </tbody>
        </table>
  
        <h3 class="font-bold mt-6">Payment History</h3>
        <table class="min-w-full border mt-2">
          <thead>
            <tr class="bg-gray-100">
              <th class="p-2 border">Date</th>
              <th class="p-2 border">Amount</th>
              <th class="p-2 border">Paid With</th>
              <th class="p-2 border">Type</th>
              <th class="p-2 border">Reference</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in report.payments" :key="p.date">
              <td class="p-2 border">{{ p.date }}</td>
              <td class="p-2 border">{{ formatCurrency(p.amount) }}</td>
              <td class="p-2 border">{{ p.payment_account }}</td>
              <td class="p-2 border">{{ p.type }}</td>
              <td class="p-2 border">{{ p.reference || '-' }}</td>
            </tr>
          </tbody>
        </table>
  
        <div class="mt-6 text-right space-y-1">
          <p><strong>Grand Total:</strong> {{ formatCurrency(report.totals.grand_total) }}</p>
          <p><strong>Amount Paid:</strong> {{ formatCurrency(report.totals.amount_paid) }}</p>
          <p><strong>Balance:</strong> {{ formatCurrency(report.totals.balance) }}</p>
          <p><strong>Change:</strong> {{ formatCurrency(report.totals.change) }}</p>
        </div>
  
        <div class="flex justify-end space-x-4 mt-6">
          <button
            @click="printReport"
            class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg"
          >
            Print
          </button>
          <button
            @click="$emit('update:show', false)"
            class="bg-gray-300 hover:bg-gray-400 text-black px-4 py-2 rounded-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  const props = defineProps({ report: Object, show: Boolean });
  const emit = defineEmits(['update:show']);
  
  const formatCurrency = val => Number(val).toLocaleString(undefined, { style: 'currency', currency: 'UGX' });
  
  const printReport = () => {
    const content = document.querySelector('.bg-white.rounded-xl.shadow-lg.p-6').innerHTML;
    const win = window.open('', '', 'width=800,height=600');
    win.document.write('<html><head><title>Report</title></head><body>');
    win.document.write(content);
    win.document.write('</body></html>');
    win.document.close();
    win.print();
  };
  </script>
  