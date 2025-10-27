<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">{{ reportTitle }}</h1>

    <!-- Controls -->
    <div class="flex flex-wrap gap-2 mb-4">
      <input
        v-model="searchQuery"
        placeholder="Search customers..."
        class="border rounded p-2 flex-1 min-w-[200px]"
      />
      <button @click="exportExcel" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
        Export Excel
      </button>
      <button @click="exportPDF" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
        Export PDF
      </button>
      <button @click="$router.push('/reports')" class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
        Back to Reports
      </button>
    </div>

    <!-- Table -->
    <table class="min-w-full border border-gray-200 rounded shadow">
      <thead class="bg-gray-100">
        <tr>
          <th class="p-2 border-b text-center">#</th>
          <th class="p-2 border-b text-left">Customer</th>
          <th class="p-2 border-b text-right">0-30 Days</th>
          <th class="p-2 border-b text-right">31-60 Days</th>
          <th class="p-2 border-b text-right">61-90 Days</th>
          <th class="p-2 border-b text-right">&gt;90 Days</th>
          <th class="p-2 border-b text-right font-bold">Total Balance</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(cust, index) in paginatedData" :key="cust.customer_id">
          <!-- Customer Row -->
          <tr @click="toggleExpand(cust.customer_id)" class="cursor-pointer hover:bg-gray-50">
            <td class="p-2 border-b text-center">{{ index + 1 + (currentPage-1)*pageSize }}</td>
            <td class="p-2 border-b">{{ cust.name }}</td>
            <td class="p-2 border-b text-right" :class="colorClass(cust.aging['0-30'])">{{ formatCurrency(cust.aging['0-30']) }}</td>
            <td class="p-2 border-b text-right" :class="colorClass(cust.aging['31-60'])">{{ formatCurrency(cust.aging['31-60']) }}</td>
            <td class="p-2 border-b text-right" :class="colorClass(cust.aging['61-90'])">{{ formatCurrency(cust.aging['61-90']) }}</td>
            <td class="p-2 border-b text-right" :class="colorClass(cust.aging['>90'])">{{ formatCurrency(cust.aging['>90']) }}</td>
            <td class="p-2 border-b text-right font-bold text-red-600">{{ formatCurrency(cust.total_balance) }}</td>
          </tr>

          <!-- Expandable Invoices -->
          <tr v-if="expandedRows.includes(cust.customer_id)">
            <td colspan="7" class="p-2 bg-gray-50">
              <input
                v-model="cust.invoiceSearch"
                placeholder="Filter invoices..."
                class="border rounded p-1 mb-2 w-full"
              />
              <table class="w-full border border-gray-200">
                <thead>
                  <tr class="bg-gray-200">
                    <th class="p-1 border-b text-left">Invoice #</th>
                    <th class="p-1 border-b text-left">Date</th>
                    <th class="p-1 border-b text-right">Amount</th>
                    <th class="p-1 border-b text-right">Paid</th>
                    <th class="p-1 border-b text-right">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="inv in filteredInvoices(cust)"
                    :key="inv.invoice_id"
                  >
                    <td class="p-1 border-b">{{ inv.sale_number }}</td>
                    <td class="p-1 border-b">{{ formatDate(inv.sale_date) }}</td>
                    <td class="p-1 border-b text-right">{{ formatCurrency(inv.total_amount) }}</td>
                    <td class="p-1 border-b text-right">{{ formatCurrency(inv.total_paid) }}</td>
                    <td class="p-1 border-b text-right text-red-600">{{ formatCurrency(inv.balance) }}</td>
                  </tr>
                  <tr v-if="filteredInvoices(cust).length === 0">
                    <td colspan="5" class="p-1 border-b text-center">No invoices</td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </template>

        <!-- Totals row -->
        <tr class="bg-gray-100 font-bold">
          <td colspan="2" class="p-2 border-b text-left">Totals</td>
          <td class="p-2 border-b text-right">{{ formatCurrency(totals['0-30']) }}</td>
          <td class="p-2 border-b text-right">{{ formatCurrency(totals['31-60']) }}</td>
          <td class="p-2 border-b text-right">{{ formatCurrency(totals['61-90']) }}</td>
          <td class="p-2 border-b text-right">{{ formatCurrency(totals['>90']) }}</td>
          <td class="p-2 border-b text-right">{{ formatCurrency(totals.total) }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <div class="flex justify-between mt-4">
      <button @click="prevPage" :disabled="currentPage === 1" class="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400">Prev</button>
      <div>Page {{ currentPage }} / {{ totalPages }}</div>
      <button @click="nextPage" :disabled="currentPage === totalPages" class="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400">Next</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '@/api';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

const reportData = ref([]);
const expandedRows = ref([]);
const searchQuery = ref('');
const reportTitle = ref('Debtors Aging Report');
const endpoint = ref('/reports/debtors-aging');

const currentPage = ref(1);
const pageSize = ref(10);

const fetchReport = async () => {
  try {
    const res = await api.get(endpoint.value);
    reportData.value = (res.data.report || []).map(c => {
      const aging = { '0-30': 0, '31-60': 0, '61-90': 0, '>90': 0 };
      c.invoices.forEach(inv => {
        if (aging[inv.aging_bucket] !== undefined) aging[inv.aging_bucket] += inv.balance;
      });
      return { ...c, aging, invoices: c.invoices || [], invoiceSearch: '' };
    });
  } catch (err) {
    console.error('Error fetching report:', err);
  }
};

// Expand/collapse
const toggleExpand = (id) => {
  if (expandedRows.value.includes(id)) {
    expandedRows.value = expandedRows.value.filter(x => x !== id);
  } else {
    expandedRows.value.push(id);
  }
};

// Invoice filtering
const filteredInvoices = (cust) => {
  const query = cust.invoiceSearch.toLowerCase();
  return cust.invoices.filter(inv =>
    inv.sale_number.toLowerCase().includes(query)
  );
};

// Color formatting
const colorClass = (value) => value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : '';

// Format currency
const formatCurrency = (value) =>
  value?.toLocaleString('en-US', { style: 'currency', currency: 'UGX' }) || '0';

// Format date
const formatDate = (date) => date ? new Date(date).toLocaleDateString() : '-';

// Pagination helpers
const totalPages = computed(() =>
  Math.ceil(filteredCustomers.value.length / pageSize.value)
);

const paginatedData = computed(() =>
  filteredCustomers.value.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value)
);

const prevPage = () => { if (currentPage.value > 1) currentPage.value--; };
const nextPage = () => { if (currentPage.value < totalPages.value) currentPage.value++; };

// Customer search
const filteredCustomers = computed(() =>
  reportData.value.filter(c =>
    c.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    c.phone?.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

// Compute totals
const totals = computed(() => {
  const buckets = { '0-30': 0, '31-60': 0, '61-90': 0, '>90': 0, total: 0 };
  reportData.value.forEach(c => {
    buckets['0-30'] += c.aging['0-30'];
    buckets['31-60'] += c.aging['31-60'];
    buckets['61-90'] += c.aging['61-90'];
    buckets['>90'] += c.aging['>90'];
    buckets.total += c.total_balance;
  });
  return buckets;
});

// Export Excel
const exportExcel = () => {
  const wsData = [
    ['Customer','0-30','31-60','61-90','>90','Total Balance'],
    ...reportData.value.map(c => [
      c.name,
      c.aging['0-30'], c.aging['31-60'], c.aging['61-90'], c.aging['>90'], c.total_balance
    ])
  ];
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(wsData);
  XLSX.utils.book_append_sheet(wb, ws, 'Debtors Aging');
  XLSX.writeFile(wb, 'Debtors_Aging_Report.xlsx');
};

// Export PDF
const exportPDF = () => {
  const doc = new jsPDF();
  const head = [['Customer','0-30','31-60','61-90','>90','Total']];
  const body = reportData.value.map(c => [
    c.name,
    c.aging['0-30'], c.aging['31-60'], c.aging['61-90'], c.aging['>90'], c.total_balance
  ]);
  doc.autoTable({ head, body });
  doc.save('Debtors_Aging_Report.pdf');
};

onMounted(fetchReport);
</script>

<style scoped>
table { border-collapse: collapse; }
th, td { text-align: right; }
td:first-child, th:first-child, td:nth-child(2), th:nth-child(2) { text-align: left; }
</style>
