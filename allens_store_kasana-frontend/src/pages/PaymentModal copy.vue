<template>
    <div
      v-if="show"
      class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
    >
      <div class="bg-white rounded-xl shadow-lg p-6 w-96">
        <h2 class="text-lg font-bold mb-4">
          Receive Payment for Sale #{{ sale.sale_id }}
        </h2>
  
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium">Amount</label>
            <input
              v-model.number="form.amount"
              type="number"
              step="0.01"
              class="w-full p-2 border rounded-lg"
              :max="sale.balance"
            />
          </div>
  
          <div>
            <label class="block text-sm font-medium">Payment Type</label>
            <select v-model="form.payment_type" class="w-full p-2 border rounded-lg">
              <option value="Cash">Cash</option>
              <option value="Bank">Bank</option>
              <option value="Mobile Money">Mobile Money</option>
            </select>
          </div>
  
          <div>
            <label class="block text-sm font-medium">Payment Account</label>
            <select v-model="form.payment_account_id" class="w-full p-2 border rounded-lg">
              <option v-for="account in accounts" :key="account.id" :value="account.id">
                {{ account.name }}
              </option>
            </select>
          </div>
  
          <div>
            <label class="block text-sm font-medium">Transaction Date</label>
            <input
              v-model="form.transaction_date"
              type="date"
              class="w-full p-2 border rounded-lg"
            />
          </div>
  
          <div>
            <label class="block text-sm font-medium">Reference (Optional)</label>
            <input
              v-model="form.reference"
              type="text"
              class="w-full p-2 border rounded-lg"
              placeholder="Enter reference"
            />
          </div>
        </div>
  
        <div class="flex justify-end space-x-2 mt-4">
          <button
            @click="$emit('update:show', false)"
            class="bg-gray-300 hover:bg-gray-400 text-black px-3 py-1 rounded-lg"
          >
            Cancel
          </button>
          <button
            @click="submitPayment"
            class="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded-lg"
          >
            Save Payment
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, watch } from 'vue';
  import api from '../api';
  

  defineProps({
    sale: Object,
    accounts: Array,
    show: Boolean
  });
  defineEmits(['update:show', 'saved']);
  
  const form = ref({
    amount: 0,
    payment_type: 'Cash',
    payment_account_id: '',
    transaction_date: new Date().toISOString().split('T')[0],
    reference: ''
  });
  
  // watch(() => sale, (newSale) => {
  //   if (newSale) form.value.amount = newSale.balance;
  // });

  watch(() => sale, (newSale) => {
  if (newSale && newSale.balance !== undefined) form.value.amount = newSale.balance;
});

  
  const submitPayment = async () => {
    const amount = parseFloat(form.value.amount);
    if (amount > sale.balance) {
      alert(`Amount cannot exceed balance: ${sale.balance}`);
      return;
    }
  
    try {
      await api.post('/payments/', {
        sale_id: sale.sale_id,
        ...form.value
      });
      alert('Payment saved!');
      form.value.reference = '';
      form.value.payment_account_id = '';
      form.value.amount = sale.balance;
      emit('saved');
      emit('update:show', false);
    } catch (err) {
      console.error(err);
      alert('Failed to save payment.');
    }
  };
  </script>
  