<template>
    <div class="p-6 bg-gray-50 min-h-screen">
      <h1 class="text-3xl font-semibold mb-6 text-gray-800">📦 Stock Adjustments</h1>
  
      <!-- Create Adjustment Form -->
      <form @submit.prevent="submitAdjustment" class="bg-white p-6 rounded-2xl shadow-md space-y-6 mb-8">
        <h2 class="text-xl font-semibold text-gray-800">New Adjustment</h2>
  
        <div class="grid md:grid-cols-3 gap-4">
          <!-- Product Combobox -->
          <div class="relative">
            <label class="label">Product</label>
  
            <input
              type="text"
              v-model="searchProduct"
              class="input"
              placeholder="Search product..."
              @focus="showDropdown = true"
              @input="showDropdown = true"
              required
            />
  
            <!-- Dropdown -->
            <ul
              v-if="showDropdown"
              class="absolute z-20 w-full bg-white border rounded-lg max-h-60 overflow-auto shadow"
            >
              <li
                v-for="p in filteredProducts"
                :key="p.id"
                @click="selectProduct(p)"
                class="px-3 py-2 hover:bg-blue-100 cursor-pointer"
              >
                {{ p.name }} || {{ p.quantity }}
              </li>
  
              <li
                v-if="filteredProducts.length === 0"
                class="px-3 py-2 text-gray-500"
              >
                No products found
              </li>
            </ul>
          </div>
  
          <div>
            <label class="label">Adjustment Type</label>
            <select v-model="form.adjustment_type" class="input" required>
              <option value="">Select Type</option>
              <option value="INCREASE">Increase</option>
              <option value="DECREASE">Decrease</option>
            </select>
          </div>
  
          <div>
            <label class="label">Quantity Change</label>
            <input type="number" min="1" v-model.number="form.quantity_change" class="input" required />
          </div>
        </div>
  
        <div class="grid md:grid-cols-2 gap-4">
          <div>
            <label class="label">Reason</label>
            <input v-model="form.reason" class="input" placeholder="Optional" />
          </div>
        </div>
  
        <button class="btn-primary">Submit Adjustment</button>
      </form>
  
      <!-- List of Adjustments -->
      <div class="bg-white p-6 rounded-2xl shadow-md">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Adjustment History</h2>
  
        <div class="overflow-x-auto">
          <table class="min-w-full border-collapse text-sm">
            <thead class="bg-gray-100">
              <tr>
                <th class="th">Product</th>
                <th class="th">Type</th>
                <th class="th text-center">Qty Change</th>
                <th class="th text-center">Previous Qty</th>
                <th class="th text-center">New Qty</th>
                <th class="th">Reason</th>
                <th class="th text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="adj in adjustments" :key="adj.id" class="hover:bg-blue-50">
                <td class="td">{{ adj.product_name }}</td>
                <td class="td">{{ adj.adjustment_type }}</td>
                <td class="td text-center">{{ adj.quantity_change }}</td>
                <td class="td text-center">{{ adj.previous_quantity }}</td>
                <td class="td text-center font-semibold">{{ adj.new_quantity }}</td>
                <td class="td">{{ adj.reason }}</td>
  
                <td class="td text-center">
                  <button @click="deleteAdjustment(adj.id)" class="btn-sm bg-red-500 hover:bg-red-600">
                    Delete
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
  
      <!-- Notification -->
      <transition name="fade">
        <div
          v-if="notification"
          class="fixed bottom-4 right-4 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg text-sm"
        >
          {{ notification }}
        </div>
      </transition>
    </div>
  </template>
  
  <script>
  import api from "../api";
  
  export default {
    data() {
      return {
        products: [],
        adjustments: [],
        notification: "",
        searchProduct: "",
        showDropdown: false,
  
        form: {
          product_id: "",
          adjustment_type: "",
          quantity_change: 1,
          reason: "",
        },
      };
    },
  
    computed: {
      filteredProducts() {
        if (!this.searchProduct) return this.products;
        return this.products.filter((p) =>
          p.name.toLowerCase().includes(this.searchProduct.toLowerCase())
        );
      },
    },
  
    methods: {
      selectProduct(p) {
        this.form.product_id = p.id;
        this.searchProduct = `${p.name} || ${p.quantity}`;
        this.showDropdown = false;
      },
  
      showNotification(msg) {
        this.notification = msg;
        setTimeout(() => (this.notification = ""), 3000);
      },
  
      async fetchProducts() {
        const res = await api.get("/inventory/products");
        this.products = res.data;
      },
  
      async fetchAdjustments() {
        const res = await api.get("/stock-adjustments/");
        this.adjustments = res.data;
      },
  
      async submitAdjustment() {
        try {
          await api.post("/stock-adjustments/", this.form);
          this.showNotification("Stock adjusted successfully!");
          this.resetForm();
          this.fetchAdjustments();
          this.fetchProducts();
        } catch (e) {
          this.showNotification("Error adjusting stock.");
        }
      },
  
      resetForm() {
        this.form = {
          product_id: "",
          adjustment_type: "",
          quantity_change: 1,
          reason: "",
        };
        this.searchProduct = "";
      },
  
      async deleteAdjustment(id) {
        if (!confirm("Delete this adjustment?")) return;
  
        await api.delete(`/stock-adjustments/${id}`);
        this.showNotification("Adjustment removed.");
        this.fetchAdjustments();
        this.fetchProducts();
      },
    },
  
    mounted() {
      this.fetchProducts();
      this.fetchAdjustments();
  
      // Hide dropdown when clicking elsewhere
      document.addEventListener("click", (e) => {
        if (!this.$el.contains(e.target)) {
          this.showDropdown = false;
        }
      });
    },
  };
  </script>
  
  <style scoped>
  .label {
    @apply text-gray-700 font-semibold text-sm mb-1 block;
  }
  .input {
    @apply border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 transition;
  }
  .btn-primary {
    @apply bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow;
  }
  .btn-sm {
    @apply text-white text-xs px-3 py-1 rounded-lg shadow;
  }
  .th {
    @apply border p-2 bg-gray-50 font-semibold text-gray-700;
  }
  .td {
    @apply border p-2;
  }
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.3s;
  }
  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }
  </style>
  