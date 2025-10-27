<template>
    <!-- Overlay -->
    <transition name="fade">
      <div
        v-if="localShow"
        class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
      >
        <!-- Modal -->
        <transition name="slide-fade">
          <div
            v-if="localShow"
            class="bg-white rounded-xl shadow-xl w-full max-w-md p-6 transform transition-all"
          >
          
            <!-- Header -->
            <h2 class="text-xl font-bold mb-4 text-gray-800">
              Make Payment for PO #{{ po?.id || 'N/A' }}
            </h2>
  
            <!-- Payment Form -->
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-600">Amount</label>
                <input
                  v-model="paymentForm.amount"
                  type="number"
                  step="0.01"
                  :max="po?.total_balance"
                  class="mt-1 w-full border border-gray-300 rounded-lg p-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                />
              </div>
  
              <div>
                <label class="block text-sm font-medium text-gray-600">Payment Type</label>
                <select
                  v-model="paymentForm.payment_type"
                  class="mt-1 w-full border border-gray-300 rounded-lg p-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                >
                  <option value="Cash">Cash</option>
                  <option value="Bank">Bank</option>
                  <option value="Mobile Money">Mobile Money</option>
                </select>
              </div>
  
              <div>
                <label class="block text-sm font-medium text-gray-600">Payment Account</label>
                <select
                  v-model="paymentForm.payment_account_id"
                  class="mt-1 w-full border border-gray-300 rounded-lg p-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                >
                  <option v-for="account in accounts" :key="account.id" :value="account.id">
                    {{ account.name }}
                  </option>
                </select>
              </div>
  
              <div>
                <label class="block text-sm font-medium text-gray-600">Transaction Date</label>
                <input
                  v-model="paymentForm.transaction_date"
                  type="date"
                  class="mt-1 w-full border border-gray-300 rounded-lg p-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                />
              </div>
  
              <div>
                <label class="block text-sm font-medium text-gray-600">Reference (Optional)</label>
                <input
                  v-model="paymentForm.reference"
                  type="text"
                  placeholder="Enter reference"
                  class="mt-1 w-full border border-gray-300 rounded-lg p-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                />
              </div>
            </div>
  
            <!-- Footer -->
            <div class="flex justify-end space-x-3 mt-6">
              <button
                @click="closeModal"
                class="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition"
              >
                Cancel
              </button>
              <button
                @click="submitPayment"
                class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
              >
                Save Payment
              </button>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  </template>
  
  <script setup>
  import { ref, watch } from 'vue';
  import api from '../api'; // Adjust your API path
  
  // ---------------------------
  // Props
  // ---------------------------
  const props = defineProps({
    modelValue: { type: Boolean, default: false },
    po: { type: Object, default: null },
    accounts: { type: Array, default: () => [] },
  });
  
  // ---------------------------
  // Emits
  // ---------------------------
  const emit = defineEmits(['update:modelValue', 'saved']);
  
  // ---------------------------
  // Local state
  // ---------------------------
  const localShow = ref(props.modelValue);
  
  watch(
    () => props.modelValue,
    (val) => (localShow.value = val),
    { immediate: true }
  );
  
  watch(localShow, (val) => emit('update:modelValue', val));
  
  const paymentForm = ref({
    amount: '',
    payment_type: 'Cash',
    payment_account_id: '',
    transaction_date: new Date().toISOString().split('T')[0],
    reference: '',
  });
  
  // ---------------------------
  // Methods
  // ---------------------------
  const closeModal = () => {
    localShow.value = false;
  };
  
  const submitPayment = async () => {
    if (!props.po) return;
    try {
      const payload = {
        amount: parseFloat(paymentForm.value.amount),
        payment_type: paymentForm.value.payment_type,
        payment_account_id: paymentForm.value.payment_account_id,
        transaction_date: paymentForm.value.transaction_date,
        reference: paymentForm.value.reference,
      };
  
      await api.post(`/suppliers/orders/${props.po.id}/pay`, payload);
  
      emit('saved');
      closeModal();
    } catch (err) {
      console.error('Error saving payment:', err.response?.data || err.message);
    }
  };
  
  // Reset form when PO changes
  watch(
    () => props.po,
    (val) => {
      if (!val) return;
      paymentForm.value = {
        amount: val.total_balance,
        payment_type: 'Cash',
        payment_account_id: '',
        transaction_date: new Date().toISOString().split('T')[0],
        reference: '',
      };
    },
    { immediate: true }
  );
  </script>
  
  <style scoped>
  /* Fade overlay */
  .fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s ease;
  }
  .fade-enter-from, .fade-leave-to {
    opacity: 0;
  }
  
  /* Slide + fade modal */
  .slide-fade-enter-active {
    transition: all 0.3s ease;
  }
  .slide-fade-leave-active {
    transition: all 0.2s ease;
  }
  .slide-fade-enter-from {
    opacity: 0;
    transform: translateY(-20px);
  }
  .slide-fade-leave-to {
    opacity: 0;
    transform: translateY(-20px);
  }
  </style>
  