<template>
  <div class="dashboard-wrapper space-y-8">

    <!-- ---------------- NAVBAR ---------------- -->
    <nav class="navbar">
      <h1 class="navbar-title">📦 Inventory Dashboard</h1>
    </nav>

    <!-- ---------------- PERIOD SELECTOR ---------------- -->
    <div class="period-select animated-fade">
      <label class="label">Select Period:</label>

      <select v-model="selectedPeriod" @change="fetchDashboard" class="modern-select">
        <option value="today">Today</option>
        <option value="week">This Week</option>
        <option value="month">This Month</option>
        <option value="custom">Custom</option>
      </select>

      <!-- Custom Range -->
      <div v-if="selectedPeriod === 'custom'" class="date-group">
        <input type="date" v-model="customStartDate" class="modern-input" @change="fetchDashboard">
        <span class="to-text">to</span>
        <input type="date" v-model="customEndDate" class="modern-input" @change="fetchDashboard">
      </div>
    </div>

    <!-- ---------------- METRIC CARDS ---------------- -->
    <div class="grid auto-fit gap-6 animated-fade">
      <div v-for="card in metricCards" :key="card.title" class="metric-card">
        <div class="metric-title">{{ card.title }}</div>
        <div class="metric-value">{{ card.value }}</div>
        <div class="metric-sub">{{ card.subtitle }}</div>
      </div>
    </div>

    <!-- ---------------- CHARTS ---------------- -->
    <div class="grid auto-fit-2 gap-6">
      <div class="chart-box animated-slide">
        <h2 class="chart-title">Sales Last 7 Days</h2>
        <LineChart :chartData="salesChartData" />
      </div>

      <div class="chart-box animated-slide">
        <h2 class="chart-title">Expenses Last 7 Days</h2>
        <LineChart :chartData="expensesChartData" />
      </div>
    </div>

    <!-- ---------------- PRODUCT PERFORMANCE ---------------- -->
    <div class="grid auto-fit-2 gap-6">
      <div class="list-box animated-slide">
        <h2 class="chart-title">Best Performing Products</h2>
        <ul class="product-list">
          <li v-for="p in bestProducts" :key="p.product_id" class="product-item">
            <span>{{ p.product_name }}</span>
            <span class="product-value">UGX {{ p.total_revenue.toLocaleString() }}</span>
          </li>
        </ul>
      </div>

      <div class="list-box animated-slide">
        <h2 class="chart-title">Least Performing Products</h2>
        <ul class="product-list">
          <li v-for="p in leastProducts" :key="p.product_id" class="product-item">
            <span>{{ p.product_name }}</span>
            <span class="product-value">UGX {{ p.total_revenue.toLocaleString() }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- ---------------- KPI CARDS ---------------- -->
    <div class="grid auto-fit-3 gap-6 animated-fade">
      <div class="kpi-card">
        <h2 class="kpi-title">Outstanding Sales</h2>
        <div class="kpi-value red">UGX {{ outstandingSales.toLocaleString() }}</div>
      </div>

      <div class="kpi-card">
        <h2 class="kpi-title">Outstanding Purchase Orders</h2>
        <div class="kpi-value red">UGX {{ outstandingPO.toLocaleString() }}</div>
      </div>

      <div class="kpi-card">
        <h2 class="kpi-title">Sales Profit</h2>
        <div class="kpi-value green">UGX {{ salesProfit.toLocaleString() }}</div>
      </div>

      <div class="kpi-card">
        <h2 class="kpi-title">Profit</h2>
        <div class="kpi-value green">UGX {{ profitInRange.toLocaleString() }}</div>
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
      selectedPeriod: 'today',
      customStartDate: '',
      customEndDate: '',

      totalProducts: 0,
      totalSales: 0,
      salesProfit: 0,
      totalExpenses: 0,
      totalCustomers: 0,
      totalSuppliers: 0,
      totalPurchaseOrders: 0,
      outstandingSales: 0,
      outstandingPO: 0,
      profitInRange: 0,

      salesChartData: { labels: [], datasets: [] },
      expensesChartData: { labels: [], datasets: [] },

      bestProducts: [],
      leastProducts: [],
    };
  },
  computed: {
    metricCards() {
      return [
        { title: 'Products', value: this.totalProducts, subtitle: 'Active products in inventory' },
        { title: 'Customers', value: this.totalCustomers, subtitle: 'Registered customers' },
        { title: 'Suppliers', value: this.totalSuppliers, subtitle: 'Total suppliers' },
        { title: 'Sales', value: 'UGX ' + this.totalSales.toLocaleString(), subtitle: 'Total sales' },
        { title: 'Sales Profit', value: 'UGX ' + this.salesProfit.toLocaleString(), subtitle: 'Revenue - Cost of Goods Sold' },
        { title: 'Expenses', value: 'UGX ' + this.totalExpenses.toLocaleString(), subtitle: 'Total expenses' },
        { title: 'Profit', value: 'UGX ' + this.profitInRange.toLocaleString(), subtitle: 'Sales Profit - Expenses' },
        { title: 'Purchase Orders', value: this.totalPurchaseOrders, subtitle: 'All POs' },
        { title: 'Outstanding Sales', value: 'UGX ' + this.outstandingSales.toLocaleString(), subtitle: 'Pending receivables' },
        { title: 'Outstanding PO', value: 'UGX ' + this.outstandingPO.toLocaleString(), subtitle: 'Pending payments' },
      ];
    },
  },
  methods: {
    async fetchDashboard() {
      try {
        const params = { period: this.selectedPeriod };
        if (this.selectedPeriod === 'custom') {
          params.start_date = this.customStartDate;
          params.end_date = this.customEndDate;
        }

        const res = await api.get('/dashboard/metrics', { params });
        const data = res.data;

        this.totalProducts = data.totalProducts;
        this.totalSales = data.totalSales;
        this.salesProfit = data.sales_profit;
        this.totalExpenses = data.totalExpenses;
        this.profitInRange = data.profitInRange;
        this.totalCustomers = data.totalCustomers;
        this.totalSuppliers = data.totalSuppliers;
        this.totalPurchaseOrders = data.totalPurchaseOrders;
        this.outstandingSales = data.outstandingSales;
        this.outstandingPO = data.outstandingPO;

        this.salesChartData = {
          labels: data.salesLast7Days.map(d => d.day),
          datasets: [
            {
              label: 'Sales',
              data: data.salesLast7Days.map(d => d.amount),
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59,130,246,0.25)',
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
              backgroundColor: 'rgba(239,68,68,0.25)',
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

/* ---------------- NAVBAR ---------------- */
.navbar {
  background: linear-gradient(135deg, #1e1b4b, #4338ca);
  padding: 22px;
  border-radius: 14px;
  text-align: center;
  box-shadow: 0 6px 18px rgba(0,0,0,0.25);
}

.navbar-title {
  font-size: 28px;
  font-weight: 900;
  color: white;
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* ---------------- WRAPPER ---------------- */
.dashboard-wrapper {
  padding: 20px;
  animation: fadeIn 0.6s ease-in-out;
}

.period-select {
  background: rgba(255,255,255,0.9);
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.1);
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Dropdowns */
.modern-select,
.modern-input {
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  padding: 8px 10px;
  background: white;
  transition: .2s;
}

/* ---------------- METRICS ---------------- */
.metric-card {
  padding: 20px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 4px 14px rgba(0,0,0,0.1);
  transition: .2s;
}

.metric-card:hover {
  transform: translateY(-5px);
}

.metric-title {
  color: #64748b;
  font-weight: 600;
}

.metric-value {
  font-size: 30px;
  font-weight: 900;
  margin-top: 8px;
  background: linear-gradient(90deg, #4338ca, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ---------------- KPI ---------------- */
.kpi-card {
  background: white;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.1);
}

.kpi-value.green {
  color: #16a34a;
}

/* ---------------- ANIMATIONS ---------------- */
@keyframes fadeIn { from {opacity:0;} to {opacity:1;} }
.animated-fade { animation: fadeIn .7s ease-in-out; }

</style>
