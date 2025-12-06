<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-2xl font-bold mb-4">📊 Sales Profit & Loss Report</h1>

    <!-- Filters -->
    <div class="flex gap-4 mb-6">
      <input
        type="date"
        v-model="filters.start_date"
        class="border rounded px-3 py-1"
      />
      <input
        type="date"
        v-model="filters.end_date"
        class="border rounded px-3 py-1"
      />
      <input
        type="number"
        v-model.number="filters.customer_id"
        placeholder="Customer ID"
        class="border rounded px-3 py-1"
      />
      <input
        type="number"
        v-model.number="filters.category_id"
        placeholder="Category ID"
        class="border rounded px-3 py-1"
      />
      <button
        @click="fetchReport"
        class="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700"
      >
        Filter
      </button>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-5 gap-4 mb-6 text-white">
      <div class="bg-green-600 p-4 rounded text-center">
        <div>Total Sales</div>
        <div class="text-xl font-bold">{{ formatPrice(summary.total_sales) }}</div>
      </div>
      <div class="bg-red-600 p-4 rounded text-center">
        <div>Total Cost</div>
        <div class="text-xl font-bold">{{ formatPrice(summary.total_cost) }}</div>
      </div>
      <div class="bg-blue-600 p-4 rounded text-center">
        <div>Total Profit/Loss</div>
        <div class="text-xl font-bold">{{ formatPrice(summary.total_profit_loss) }}</div>
      </div>
      <div class="bg-gray-700 p-4 rounded text-center">
        <div>Total Paid</div>
        <div class="text-xl font-bold">{{ formatPrice(summary.total_paid) }}</div>
      </div>
      <div class="bg-yellow-600 p-4 rounded text-center">
        <div>Total Balance</div>
        <div class="text-xl font-bold">{{ formatPrice(summary.total_balance) }}</div>
      </div>
    </div>

    <!-- Sales Table -->
    <div v-if="sales.length">
      <div v-for="sale in sales" :key="sale.sale_id" class="mb-6 border rounded bg-white shadow">
        <div class="p-4 border-b flex justify-between items-center bg-gray-100">
          <div>
            <div class="font-bold">Sale #{{ sale.sale_number }} ({{ sale.sale_date }})</div>
            <div>{{ sale.customer_name }} - {{ sale.customer_phone }}</div>
          </div>
          <div class="text-right">
            <div>Total: {{ formatPrice(sale.total_amount) }}</div>
            <div>Profit: {{ formatPrice(sale.profit_loss) }}</div>
            <div>Balance: {{ formatPrice(sale.balance) }}</div>
          </div>
        </div>
        <!-- Sale Items -->
        <table class="min-w-full text-left divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-2">Product</th>
              <th class="px-4 py-2">Category</th>
              <th class="px-4 py-2">Unit</th>
              <th class="px-4 py-2">Qty</th>
              <th class="px-4 py-2">Converted Qty</th>
              <th class="px-4 py-2">Unit Price</th>
              <th class="px-4 py-2">Cost Price</th>
              <th class="px-4 py-2">Profit</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="item in sale.items" :key="item.product_id">
              <td class="px-4 py-2">{{ item.product_name }}</td>
              <td class="px-4 py-2">{{ item.category }}</td>
              <td class="px-4 py-2">{{ item.unit_name }}</td>
              <td class="px-4 py-2">{{ item.quantity }}</td>
              <td class="px-4 py-2">{{ item.converted_quantity }}</td>
              <td class="px-4 py-2">{{ formatPrice(item.unit_price) }}</td>
              <td class="px-4 py-2">{{ formatPrice(item.cost_price) }}</td>
              <td class="px-4 py-2">{{ formatPrice(item.profit) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div v-else class="text-center text-gray-500 mt-6">No sales found for the selected filters.</div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from "vue";
import api from "@/api";

export default {
  name: "SalesProfitLoss",
  setup() {
    const filters = reactive({
      start_date: new Date().toISOString().substr(0,10),
      end_date:  new Date().toISOString().substr(0,10),
      customer_id: null,

      category_id: null,
    });

    const sales = ref([]);
    const summary = reactive({
      total_sales: 0,
      total_cost: 0,
      total_profit_loss: 0,
      total_paid: 0,
      total_balance: 0,
    });

    const fetchReport = async () => {
      try {
        const params = {};
        if (filters.start_date) params.start_date = filters.start_date;
        if (filters.end_date) params.end_date = filters.end_date;
        if (filters.customer_id) params.customer_id = filters.customer_id;
        if (filters.category_id) params.category_id = filters.category_id;

        const res = await api.get("/reports/sales", { params });
        sales.value = res.data.data;
        Object.assign(summary, res.data.summary);
      } catch (err) {
        console.error("Error fetching report:", err);
      }
    };

    // Format amounts as UGX with commas
    const formatPrice = (value) => {
      const amount = value == null ? 0 : Math.round(value);
      return `UGX ${amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
    };

    onMounted(fetchReport);

    return { filters, sales, summary, fetchReport, formatPrice };
  },
};
</script>

<style scoped>
table th,
table td {
  border-bottom: 1px solid #e5e7eb;
}
</style>
