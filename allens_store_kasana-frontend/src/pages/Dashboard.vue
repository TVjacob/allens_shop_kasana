<template>
  <div class="p-6 space-y-6">
    <!-- ---------------- Metrics Cards ---------------- -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
      <div v-for="card in metricCards" :key="card.title" class="bg-white shadow rounded p-5 flex flex-col justify-between">
        <div class="flex items-center justify-between">
          <div class="text-gray-500">{{ card.title }}</div>
          <div class="text-3xl font-bold">{{ card.value }}</div>
        </div>
        <div class="text-sm text-gray-400 mt-2">{{ card.subtitle }}</div>
      </div>
    </div>

    <!-- ---------------- Charts ---------------- -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-white p-6 rounded shadow">
        <h2 class="text-xl font-bold mb-4">Sales Last 7 Days</h2>
        <LineChart :chartData="salesChartData" />
      </div>

      <div class="bg-white p-6 rounded shadow">
        <h2 class="text-xl font-bold mb-4">Expenses Last 7 Days</h2>
        <LineChart :chartData="expensesChartData" />
      </div>
    </div>

    <!-- ---------------- Best / Least Products ---------------- -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-white p-6 rounded shadow">
        <h2 class="text-xl font-bold mb-4">Best Performing Products</h2>
        <ul class="divide-y divide-gray-200">
          <li v-for="product in bestProducts" :key="product.product_id" class="py-2 flex justify-between">
            <span>{{ product.product_name }}</span>
            <span class="font-bold">UGX {{ product.total_revenue.toLocaleString() }}</span>
          </li>
        </ul>
      </div>

      <div class="bg-white p-6 rounded shadow">
        <h2 class="text-xl font-bold mb-4">Least Performing Products</h2>
        <ul class="divide-y divide-gray-200">
          <li v-for="product in leastProducts" :key="product.product_id" class="py-2 flex justify-between">
            <span>{{ product.product_name }}</span>
            <span class="font-bold">UGX {{ product.total_revenue.toLocaleString() }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- ---------------- Optional KPIs ---------------- -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white p-6 rounded shadow">
        <h2 class="text-lg font-bold mb-2">Outstanding Sales (Receivables)</h2>
        <div class="text-2xl font-bold text-red-500">UGX {{ outstandingSales.toLocaleString() }}</div>
      </div>
      <div class="bg-white p-6 rounded shadow">
        <h2 class="text-lg font-bold mb-2">Outstanding Purchase Orders (Payables)</h2>
        <div class="text-2xl font-bold text-red-500">UGX {{ outstandingPO.toLocaleString() }}</div>
      </div>
      <div class="bg-white p-6 rounded shadow">
        <h2 class="text-lg font-bold mb-2">Total Purchase Orders</h2>
        <div class="text-2xl font-bold">{{ totalPurchaseOrders }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import LineChart from '../components/LineChart.vue';
import api from '../api';

export default {
  components: { LineChart },
  data() {
    return {
      // Metrics
      totalProducts: 0,
      totalSales: 0,
      totalExpenses: 0,
      totalCustomers: 0,
      totalSuppliers: 0,
      totalPurchaseOrders: 0,
      outstandingSales: 0,
      outstandingPO: 0,

      // Charts
      salesChartData: { labels: [], datasets: [] },
      expensesChartData: { labels: [], datasets: [] },

      // Products
      bestProducts: [],
      leastProducts: [],
    };
  },
  computed: {
    metricCards() {
      return [
        { title: 'Products', value: this.totalProducts, subtitle: 'Active products in inventory' },
        { title: 'Customers', value: this.totalCustomers, subtitle: 'Total registered customers' },
        { title: 'Suppliers', value: this.totalSuppliers, subtitle: 'Total suppliers' },
        { title: 'Sales', value: 'UGX ' + this.totalSales.toLocaleString(), subtitle: 'Total sales made' },
        { title: 'Expenses', value: 'UGX ' + this.totalExpenses.toLocaleString(), subtitle: 'Total expenses' },
        { title: 'Purchase Orders', value: this.totalPurchaseOrders, subtitle: 'Total purchase orders' },
        { title: 'Outstanding Sales', value: 'UGX ' + this.outstandingSales.toLocaleString(), subtitle: 'Pending receivables' },
        { title: 'Outstanding PO', value: 'UGX ' + this.outstandingPO.toLocaleString(), subtitle: 'Pending payments' },
      ];
    },
  },
  methods: {
    async fetchDashboard() {
      try {
        const res = await api.get('/dashboard/metrics');
        const data = res.data;

        this.totalProducts = data.totalProducts;
        this.totalSales = data.totalSales;
        this.totalExpenses = data.totalExpenses;
        this.totalCustomers = data.totalCustomers;
        this.totalSuppliers = data.totalSuppliers;
        this.totalPurchaseOrders = data.totalPurchaseOrders;
        this.outstandingSales = data.outstandingSales;
        this.outstandingPO = data.outstandingPO;

        // Charts
        this.salesChartData = {
          labels: data.salesLast7Days.map(d => d.day),
          datasets: [
            {
              label: 'Sales',
              data: data.salesLast7Days.map(d => d.amount),
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.2)',
              tension: 0.3
            }
          ]
        };

        this.expensesChartData = {
          labels: data.expensesLast7Days.map(d => d.day),
          datasets: [
            {
              label: 'Expenses',
              data: data.expensesLast7Days.map(d => d.amount),
              borderColor: '#ef4444',
              backgroundColor: 'rgba(239, 68, 68, 0.2)',
              tension: 0.3
            }
          ]
        };

        this.bestProducts = data.bestPerformingProducts || [];
        this.leastProducts = data.leastPerformingProducts || [];

      } catch (err) {
        console.error('Failed to fetch dashboard metrics:', err);
      }
    },
  },
  mounted() {
    this.fetchDashboard();
  },
};
</script>

<style scoped>
/* Optional: Customize card hover effect */
</style>
