<template>
    <div class="p-6 max-w-6xl mx-auto bg-white rounded-xl shadow-lg mt-6">
      <h2 class="text-2xl font-bold mb-4 text-gray-800">Customer Balances & Payments</h2>
  
      <!-- 🔹 Table: List Customer Debts -->
      <div v-if="debts.length">
        <div class="overflow-x-auto bg-gray-50 rounded-xl shadow border p-2">
          <table class="min-w-full border-collapse">
            <thead class="bg-gray-100 text-gray-700">
              <tr>
                <th class="p-2 border text-left">Customer</th>
                <th class="p-2 border text-left">Date</th>
                <th class="p-2 border text-right">Total (UGX)</th>
                <th class="p-2 border text-right">Paid (UGX)</th>
                <th class="p-2 border text-right">Balance (UGX)</th>
                <th class="p-2 border text-center">Days Overdue</th>
                <th class="p-2 border text-center">Status</th>
                <th class="p-2 border text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in debts" :key="d.id" class="hover:bg-gray-100">
                <td class="p-2 border">{{ d.customer_name }}</td>
                <td class="p-2 border">{{ d.debt_date }}</td>
                <td class="p-2 border text-right">{{ formatCurrency(d.total_amount) }}</td>
                <td class="p-2 border text-right">{{ formatCurrency(d.amount_paid) }}</td>
                <td class="p-2 border text-right">{{ formatCurrency(d.balance) }}</td>
                <td class="p-2 border text-center">{{ d.days_overdue }} days</td>
                <td class="p-2 border text-center">
                  <span
                    :class="{
                      'text-green-700 font-semibold': d.payment_status === 'Cleared',
                      'text-red-600 font-semibold': d.payment_status === 'Pending'
                    }"
                  >
                    {{ d.payment_status }}
                  </span>
                </td>
                <td class="p-2 border text-center">
                  <button
                    @click="openPaymentModal(d)"
                    class="bg-indigo-600 text-white px-3 py-1 rounded hover:bg-indigo-500 mr-2"
                  >
                    Record Payment
                  </button>
                </td>
              </tr>
            </tbody>
            <!-- 🔹 Totals Row -->
          <tfoot class="bg-gray-100 font-semibold text-gray-800">
            <tr>
              <td colspan="2" class="p-2 border text-right">Totals:</td>
              <td class="p-2 border text-right">{{ formatCurrency(totalDebt) }}</td>
              <td class="p-2 border text-right">{{ formatCurrency(totalPaid) }}</td>
              <td class="p-2 border text-right">{{ formatCurrency(totalBalance) }}</td>
              <td colspan="3" class="p-2 border text-center"></td>
            </tr>
          </tfoot>
          </table>
        </div>
      </div>
  
      <!-- 🔹 Empty state -->
      <p v-else class="text-gray-500 mt-4">No customer debts found.</p>
  
      <!-- 🔹 Buttons -->
      <div class="mt-4 flex gap-4">
        <button
          @click="openNewDebtModal"
          class="bg-green-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-500 transition"
        >
          + Add Customer Debt
        </button>
        <button
          @click="fetchDebts"
          class="bg-gray-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-500 transition"
        >
          Refresh
        </button>
      </div>
  
      <!-- 🧾 Modal: Add Debt -->
      <div v-if="showDebtModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
        <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
          <h3 class="text-xl font-bold mb-4 text-gray-800">Add Customer Debt</h3>
  
          <!-- 🔹 Searchable Customer -->
          <label class="block mb-2 font-medium">Customer Name</label>
          <div class="relative mb-2">
            <input
              type="text"
              v-model="customerSearch"
              @focus="showCustomerDropdown = true"
              @input="filterCustomers"
              @keydown.arrow-down.prevent="highlightNext"
              @keydown.arrow-up.prevent="highlightPrev"
              @keydown.enter.prevent="selectHighlighted"
              class="w-full border rounded px-3 py-2"
              placeholder="Type to search customer..."
            />
            <ul
              v-if="showCustomerDropdown && filteredCustomers.length"
              class="absolute z-50 w-full max-h-40 overflow-auto bg-white border rounded shadow mt-1"
            >
              <li
                v-for="(c, index) in filteredCustomers"
                :key="c.id"
                @click="selectCustomer(c)"
                :class="{'bg-indigo-100': index === highlightedIndex, 'cursor-pointer': true, 'px-3 py-2': true}"
                @mouseover="highlightedIndex = index"
              >
                {{ c.name }}
              </li>
            </ul>
          </div>
  
          <label class="block mb-2 font-medium">Total Amount (UGX)</label>
          <input
            type="number"
            v-model.number="newDebt.total_amount"
            class="w-full border rounded px-3 py-2 mb-2"
          />
  
          <label class="block mb-2 font-medium">Balance (UGX)</label>
          <input
            type="number"
            v-model.number="newDebt.balance"
            class="w-full border rounded px-3 py-2 mb-4"
          />
  
          <div class="flex justify-end gap-3">
            <button @click="showDebtModal = false" class="px-4 py-2 bg-gray-400 text-white rounded">Cancel</button>
            <button @click="saveDebt" class="px-4 py-2 bg-green-600 text-white rounded">Save</button>
          </div>
        </div>
      </div>
  
      <!-- 💰 Modal: Record Payment -->
      <div v-if="showPaymentModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
        <div class="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
          <h3 class="text-xl font-bold mb-4 text-gray-800">Record Payment</h3>
  
          <div class="mb-2">
            <p class="text-gray-700 font-semibold mb-1">{{ paymentCustomer.customer_name }}</p>
            <p class="text-sm text-gray-500">
              Current Balance: {{ formatCurrency(paymentCustomer.balance) }}
            </p>
          </div>
  
          <label class="block mb-2 font-medium">Select Cash/Bank Account</label>
          <select
            v-model="paymentForm.payment_account_id"
            class="w-full border rounded px-3 py-2 mb-2"
          >
            <option value="">-- Choose Account --</option>
            <option v-for="a in cashAccounts" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
  
          <label class="block mb-2 font-medium">Amount Paid (UGX)</label>
          <input
            type="number"
            v-model.number="paymentForm.amount_paid"
            class="w-full border rounded px-3 py-2 mb-2"
          />
  
          <label class="block mb-2 font-medium">Payment Date</label>
          <input
            type="date"
            v-model="paymentForm.payment_date"
            class="w-full border rounded px-3 py-2 mb-4"
          />
  
          <div class="flex justify-end gap-3">
            <button @click="showPaymentModal = false" class="px-4 py-2 bg-gray-400 text-white rounded">Cancel</button>
            <button @click="savePayment" class="px-4 py-2 bg-indigo-600 text-white rounded">Save</button>
          </div>
        </div>
      </div>
  
      <!-- 🔔 Notifications -->
      <p
        v-if="successMessage"
        class="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded shadow-lg transition-all"
      >
        {{ successMessage }}
      </p>
      <p
        v-if="errorMessage"
        class="fixed bottom-16 right-4 bg-red-600 text-white px-4 py-2 rounded shadow-lg transition-all"
      >
        {{ errorMessage }}
      </p>
    </div>
  </template>
  
  <script setup>
  import { ref, reactive, onMounted } from 'vue'
  import api from '../api'
  
  // 🔹 State
  const debts = ref([])
  const cashAccounts = ref([])
  const customers = ref([])
  const showDebtModal = ref(false)
  const showPaymentModal = ref(false)
  const paymentCustomer = ref({})
  const loading = ref(false)
  const successMessage = ref('')
  const errorMessage = ref('')
  
  // 🔹 Forms
  const newDebt = reactive({
    customer_id: '',
    customer_name: '',
    total_amount: '',
    balance: ''
  })
  
  const paymentForm = reactive({
    customer_id: '',
    payment_account_id: '',
    amount_paid: '',
    payment_date: ''
  })
  

  // 🔹 Customer search
  const customerSearch = ref('')
  const filteredCustomers = ref([])
  const showCustomerDropdown = ref(false)
  const highlightedIndex = ref(0)
  const selectedCustomerObj = ref(null)
  

// 🔹 Totals (computed)
// const totalDebt = computed(() => debts.value.reduce((sum, d) => sum + (d.total_amount || 0), 0))
// const totalPaid = computed(() => debts.value.reduce((sum, d) => sum + (d.amount_paid || 0), 0))
// const totalBalance = computed(() => debts.value.reduce((sum, d) => sum + (d.balance || 0), 0))
// Reactive totals
const totalDebt = ref(0)
const totalPaid = ref(0)
const totalBalance = ref(0)
  // // 🔹 Fetch all debts
  // const fetchDebts = async () => {
  //   loading.value = true
  //   try {
  //     const res = await api.get('/customer_balances/')
  //     debts.value = res.data || []
  //   } catch (err) {
  //     errorMessage.value = 'Failed to fetch customer balances'
  //   } finally {
  //     loading.value = false
  //   }
  // }
  // 🔹 Fetch all debts
const fetchDebts = async () => {
  loading.value = true
  try {
    const res = await api.get('/customer_balances/')
    debts.value = res.data || []

    // 🔹 Compute totals immediately after fetching
    totalDebt.value = debts.value.reduce((sum, d) => sum + (d.total_amount || 0), 0)
    totalPaid.value = debts.value.reduce((sum, d) => sum + (d.amount_paid || 0), 0)
    totalBalance.value = debts.value.reduce((sum, d) => sum + (d.balance || 0), 0)
  } catch (err) {
    errorMessage.value = 'Failed to fetch customer balances'
  } finally {
    loading.value = false
  }
}

  const fetchCustomers = async () => {
    try {
      const res = await api.get('/customer/')
      customers.value = res.data || []
      filteredCustomers.value = customers.value
    } catch (err) {
      console.error(err)
    }
  }
  
  const filterCustomers = () => {
    const search = customerSearch.value.toLowerCase()
    filteredCustomers.value = customers.value.filter(c =>
      c.name.toLowerCase().includes(search)
    )
    highlightedIndex.value = 0
  }
  
  const selectCustomer = (customer) => {
    selectedCustomerObj.value = customer
    newDebt.customer_id = customer.id
    customerSearch.value = customer.name
    showCustomerDropdown.value = false
  }
  
  // Keyboard navigation
  const highlightNext = () => {
    if (highlightedIndex.value < filteredCustomers.value.length - 1) highlightedIndex.value++
  }
  const highlightPrev = () => {
    if (highlightedIndex.value > 0) highlightedIndex.value--
  }
  const selectHighlighted = () => {
    if (filteredCustomers.value[highlightedIndex.value]) {
      selectCustomer(filteredCustomers.value[highlightedIndex.value])
    }
  }


  

  // 🔹 Fetch cash/bank accounts
  const fetchCashAccounts = async () => {
    try {
      const res = await api.get('/accounts/cash-bank')
      cashAccounts.value = res.data || []
    } catch (err) {
      console.error(err)
    }
  }
  
  // 🔹 Open modal for new debt
  const openNewDebtModal = () => {
    newDebt.customer_id = ''
    newDebt.customer_name = ''
    newDebt.total_amount = ''
    newDebt.balance = ''
    customerSearch.value = ''
    showDebtModal.value = true
    filterCustomers()
  }
  
  // 🔹 Save new debt
  const saveDebt = async () => {
    if (!newDebt.customer_id || !newDebt.total_amount || !newDebt.balance) {
      // errorMessage.value = 'All fields are required'
      showMessage('error', 'All fields are required' )

      return
    }
    if (newDebt.total_amount< newDebt.balance){
      showMessage('error', "'Total Debt can't greater  total Bill Amount" )
      return
    }
    try {
      const res = await api.post('/customer_balances/save', newDebt)
      // successMessage.value = res.data.message
      showMessage('success', res.data.message)

      showDebtModal.value = false
      fetchDebts()

    } catch (err) {
      // errorMessage.value = err.response?.data?.error || 'Failed to save debt'
      showMessage('error', errorMessage.value )


    }
  }
  
  // 🔹 Open payment modal
  const openPaymentModal = (debt) => {
    paymentCustomer.value = debt
    paymentForm.customer_id = debt.id
    paymentForm.amount_paid = ''
    paymentForm.payment_account_id = ''
    paymentForm.payment_date = new Date().toISOString().slice(0, 10)
    showPaymentModal.value = true
  }
  
  // 🔹 Save payment
  const savePayment = async () => {
    if (!paymentForm.payment_account_id || !paymentForm.amount_paid) {
      // errorMessage.value = 'Please fill all payment details'
      showMessage('error', 'Please fill all payment details' )

      return
    }
    try {
      const payload = {
        customer_id: paymentCustomer.value.customer_id,
        debt_id: paymentCustomer.value.id,
        payment_account_id: paymentForm.payment_account_id,
        amount_paid: paymentForm.amount_paid,
        paymemnt_date: paymentForm.payment_date
      }
      const res = await api.post('/customer_balances/payment', payload)
      // successMessage.value = res.data.message
      showMessage('success', res.data.message)

      showPaymentModal.value = false
      fetchDebts()

    } catch (err) {
      // errorMessage.value = err.response?.data?.error || 'Failed to save payment'
      showMessage('error', errorMessage.value )


    }
  }
  const showMessage = (type, message) => {
  if (type === 'success') successMessage.value = message
  else errorMessage.value = message

  setTimeout(() => {
    successMessage.value = ''
    errorMessage.value = ''
  }, 3000)
}

  // 🔹 Helpers
  const formatCurrency = (value) =>
    new Intl.NumberFormat('en-UG', { style: 'currency', currency: 'UGX' }).format(value || 0)
  
  // 🔹 Init
  onMounted(() => {
    fetchDebts()
    fetchCashAccounts()
    fetchCustomers()
  })
  </script>
  
  <style scoped>
  tfoot tr {
  background-color: #f8fafc;
}
tfoot td {
  font-weight: 600;
}

  select,
  input {
    transition: all 0.2s ease;
  }
  </style>
  