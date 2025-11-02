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
          <div class="text-xl font-bold">{{ summary.total_sales | currency }}</div>
        </div>
        <div class="bg-red-600 p-4 rounded text-center">
          <div>Total Cost</div>
          <div class="text-xl font-bold">{{ summary.total_cost | currency }}</div>
        </div>
        <div class="bg-blue-600 p-4 rounded text-center">
          <div>Total Profit/Loss</div>
          <div class="text-xl font-bold">{{ summary.total_profit_loss | currency }}</div>
        </div>
        <div class="bg-gray-700 p-4 rounded text-center">
          <div>Total Paid</div>
          <div class="text-xl font-bold">{{ summary.total_paid | currency }}</div>
        </div>
        <div class="bg-yellow-600 p-4 rounded text-center">
          <div>Total Balance</div>
          <div class="text-xl font-bold">{{ summary.total_balance | currency }}</div>
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
              <div>Total: {{ sale.total_amount | currency }}</div>
              <div>Profit: {{ sale.profit_loss | currency }}</div>
              <div>Balance: {{ sale.balance | currency }}</div>
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
                <td class="px-4 py-2">{{ item.unit_price | currency }}</td>
                <td class="px-4 py-2">{{ item.cost_price | currency }}</td>
                <td class="px-4 py-2">{{ item.profit | currency }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else class="text-center text-gray-500 mt-6">No sales found for the selected filters.</div>
    </div>
  </template>
  
  <script>
  // import axios from "axios";
  import { ref, reactive, onMounted } from "vue";
  import api from "@/api";

  
  export default {
    name: "SalesProfitLoss",
    setup() {
      const filters = reactive({
        start_date: "",
        end_date: "",
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
  
      onMounted(fetchReport);
  
      return { filters, sales, summary, fetchReport };
    },
    filters: {
      currency(value) {
        return new Intl.NumberFormat("en-UG", {
          style: "currency",
          currency: "UGX",
        }).format(value || 0);
      },
    },
  };
  </script>
  
  <style scoped>
  table th,
  table td {
    border-bottom: 1px solid #e5e7eb;
  }
  </style>
  