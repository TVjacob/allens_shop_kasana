<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-semibold mb-6 text-gray-800">📦 Inventory Management</h1>

    <!-- Tabs -->
    <div class="mb-6 flex gap-3 border-b pb-2">
      <button @click="activeTab='products'" :class="tabClass('products')">Products</button>
      <button @click="activeTab='categories'" :class="tabClass('categories')">Categories</button>
    </div>

    <!-- ---------------- Products Tab ---------------- -->
    <div v-if="activeTab==='products'" class="animate-fadeIn">
      <!-- Add/Edit Product Form -->
      <form @submit.prevent="submitProduct" class="mb-6 flex flex-wrap gap-3 items-center bg-white p-4 rounded-xl shadow">
        <input v-model="productForm.name" placeholder="Product Name" class="input" required />
        <input v-model="productForm.sku" placeholder="SKU" class="input" required />
        <input v-model.number="productForm.price" type="number" min="1" placeholder="Price" class="input" />
        <select v-model="productForm.category_id" class="input">
          <option disabled value="">Select Category</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>

        <button :disabled="loading" class="btn-primary">
          {{ editingProduct ? 'Update' : 'Add' }} Product
        </button>
        <button
          v-if="editingProduct"
          type="button"
          @click="cancelProductEdit"
          class="btn-secondary"
        >
          Cancel
        </button>
      </form>

      <!-- Search Product -->
      <div class="mb-6 flex gap-3 flex-wrap items-center">
        <input
          v-model="searchQuery"
          placeholder="Search by name or SKU"
          @input="searchProducts"
          class="input flex-1"
        />
        <button @click="fetchProducts" class="btn-gray">Reset</button>
        <button @click="exportExcel" class="btn-warning">Export Excel</button>
        <button @click="exportPDF" class="btn-danger">Export PDF</button>
      </div>

      <div v-if="loading" class="text-gray-600 text-center py-6">Loading products...</div>

      <!-- Products Table -->
      <div v-else class="overflow-x-auto rounded-xl shadow bg-white">
        <table class="min-w-full border-collapse text-sm">
          <thead>
            <tr class="bg-gray-100 text-gray-700">
              <th v-for="h in ['ID','Name','SKU','Price','Category','Stock Qty','Actions']" :key="h" class="th">{{ h }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="product in products"
              :key="product.id"
              class="hover:bg-blue-50 transition"
            >
              <td class="td text-center">{{ product.id }}</td>
              <td class="td font-medium">{{ product.name }}</td>
              <td class="td">{{ product.sku }}</td>
              <td class="td">{{ formatPrice(product.price) }}</td>
              <td class="td">{{ getCategoryName(product.category_id) }}</td>
              <td class="td text-center">{{ product.quantity ?? 0 }}</td>
              <td class="td text-center">
                <button @click="editProduct(product)" class="btn-sm bg-blue-500 hover:bg-blue-600">Edit</button>
                <button @click="deleteProduct(product.id)" class="btn-sm bg-red-500 hover:bg-red-600">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ---------------- Categories Tab ---------------- -->
    <div v-if="activeTab==='categories'" class="animate-fadeIn">
      <!-- Add/Edit Category Form -->
      <form @submit.prevent="submitCategory" class="flex gap-3 flex-wrap mb-4 bg-white p-4 rounded-xl shadow">
        <input v-model="categoryForm.name" placeholder="Category Name" class="input" required />
        <button :disabled="loading" class="btn-primary">
          {{ editingCategory ? 'Update' : 'Add' }} Category
        </button>
        <button
          v-if="editingCategory"
          type="button"
          @click="cancelCategoryEdit"
          class="btn-secondary"
        >
          Cancel
        </button>
      </form>

      <div v-if="loading" class="text-gray-600 text-center py-6">Loading categories...</div>

      <!-- Categories Table -->
      <div v-else class="overflow-x-auto rounded-xl shadow bg-white">
        <table class="min-w-full border-collapse text-sm">
          <thead>
            <tr class="bg-gray-100 text-gray-700">
              <th class="th">ID</th>
              <th class="th">Name</th>
              <th class="th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in categories" :key="cat.id" class="hover:bg-blue-50 transition">
              <td class="td text-center">{{ cat.id }}</td>
              <td class="td">{{ cat.name }}</td>
              <td class="td text-center">
                <button @click="editCategory(cat)" class="btn-sm bg-blue-500 hover:bg-blue-600">Edit</button>
                <button @click="deleteCategory(cat.id)" class="btn-sm bg-red-500 hover:bg-red-600">Delete</button>
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
import api from '../api';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

export default {
  data() {
    return {
      activeTab: 'products',
      products: [],
      allProducts: [], // 🔹 keep all for local filtering
      categories: [],
      productForm: { id: null, name: '', sku: '', price: 0, category_id: '' },
      editingProduct: false,
      categoryForm: { id: null, name: '' },
      editingCategory: false,
      searchQuery: '',
      searchTimeout: null,
      loading: false,
      notification: '',
    };
  },
  methods: {
    tabClass(tab) {
      return `px-4 py-2 rounded-t-lg font-semibold transition ${
        this.activeTab === tab
          ? 'bg-blue-500 text-white shadow'
          : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
      }`;
    },
    showNotification(msg, duration = 3000) {
      this.notification = msg;
      setTimeout(() => (this.notification = ''), duration);
    },

    // --- Categories ---
    async fetchCategories() {
      try {
        this.loading = true;
        const res = await api.get('/inventory/categories');
        this.categories = res.data;
      } catch {
        this.showNotification('Failed to load categories.');
      } finally {
        this.loading = false;
      }
    },
    async submitCategory() {
      try {
        this.loading = true;
        if (!this.categoryForm.name.trim()) {
          return this.showNotification('Category name is required.');
        }
        if (this.editingCategory) {
          await api.put(`/inventory/categories/${this.categoryForm.id}`, this.categoryForm);
          this.showNotification('Category updated successfully!');
        } else {
          await api.post('/inventory/categories', this.categoryForm);
          this.showNotification('Category added successfully!');
        }
        this.categoryForm = { id: null, name: '' };
        this.editingCategory = false;
        this.fetchCategories();
      } catch {
        this.showNotification('Error saving category.');
      } finally {
        this.loading = false;
      }
    },
    editCategory(cat) {
      this.categoryForm = { ...cat };
      this.editingCategory = true;
    },
    cancelCategoryEdit() {
      this.categoryForm = { id: null, name: '' };
      this.editingCategory = false;
    },
    async deleteCategory(id) {
      if (!confirm('Delete this category?')) return;
      try {
        await api.delete(`/inventory/categories/${id}`);
        this.showNotification('Category deleted.');
        this.fetchCategories();
      } catch {
        this.showNotification('Failed to delete category.');
      }
    },

    // --- Products ---
    async fetchProducts() {
      try {
        this.loading = true;
        const res = await api.get('/inventory/products');
        this.products = res.data;
        this.allProducts = res.data;
      } catch {
        this.showNotification('Failed to load products.');
      } finally {
        this.loading = false;
      }
    },
    async submitProduct() {
      if (!this.productForm.name.trim()) return this.showNotification('Product name is required.');
      if (!this.productForm.sku.trim()) return this.showNotification('SKU is required.');
      if (this.productForm.price <= 0) return this.showNotification('Enter a valid price.');
      if (!this.productForm.category_id) return this.showNotification('Select a category.');

      try {
        this.loading = true;
        if (this.editingProduct) {
          await api.put(`/inventory/products/${this.productForm.id}`, this.productForm);
          this.showNotification('Product updated successfully!');
        } else {
          await api.post('/inventory/products', this.productForm);
          this.showNotification('Product added successfully!');
        }
        this.productForm = { id: null, name: '', sku: '', price: 0, category_id: '' };
        this.editingProduct = false;
        this.fetchProducts();
      } catch {
        this.showNotification('Error saving product.');
      } finally {
        this.loading = false;
      }
    },
    editProduct(product) {
      this.productForm = { ...product };
      this.editingProduct = true;
    },
    cancelProductEdit() {
      this.productForm = { id: null, name: '', sku: '', price: 0, category_id: '' };
      this.editingProduct = false;
    },
    async deleteProduct(id) {
      if (!confirm('Delete this product?')) return;
      try {
        await api.delete(`/inventory/products/${id}`);
        this.showNotification('Product deleted.');
        this.fetchProducts();
      } catch {
        this.showNotification('Failed to delete product.');
      }
    },

    // --- Search (live, debounced, local + fallback API) ---
    async searchProducts() {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(async () => {
        const query = this.searchQuery.trim().toLowerCase();
        if (!query) {
          this.products = this.allProducts;
          return;
        }

        // local filter
        const localResults = this.allProducts.filter(
          (p) =>
            p.name.toLowerCase().includes(query) ||
            p.sku.toLowerCase().includes(query)
        );

        if (localResults.length) {
          this.products = localResults;
        } else {
          try {
            this.loading = true;
            const res = await api.get('/inventory/products/search', {
              params: { query },
            });
            this.products = res.data;
          } catch {
            this.showNotification('Search failed.');
          } finally {
            this.loading = false;
          }
        }
      }, 300);
    },

    // --- Excel / PDF ---
    exportExcel() {
      const ws = XLSX.utils.json_to_sheet(this.products);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Products');
      XLSX.writeFile(wb, 'products.xlsx');
    },
    exportPDF() {
      const doc = new jsPDF();
      doc.autoTable({
        head: [['ID', 'Name', 'SKU', 'Price', 'Category', 'Stock qty']],
        body: this.products.map((p) => [
          p.id,
          p.name,
          p.sku,
          this.formatPrice(p.price),
          this.getCategoryName(p.category_id),
          p.quantity ?? 0,
        ]),
      });
      doc.save('products.pdf');
    },

    formatPrice(value) {
      return new Intl.NumberFormat('en-UG', { style: 'currency', currency: 'UGX' }).format(value);
    },
    getCategoryName(catId) {
      const cat = this.categories.find((c) => c.id === catId);
      return cat ? cat.name : '';
    },
  },
  mounted() {
    this.fetchCategories();
    this.fetchProducts();
  },
};
</script>

<style scoped>
.input {
  @apply border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none transition;
}
.btn-primary {
  @apply bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow;
}
.btn-secondary {
  @apply bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition shadow;
}
.btn-warning {
  @apply bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 transition shadow;
}
.btn-danger {
  @apply bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition shadow;
}
.btn-gray {
  @apply bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 transition shadow;
}
.btn-sm {
  @apply text-white text-xs px-3 py-1 rounded shadow transition;
}
.th {
  @apply p-2 border font-semibold text-left;
}
.td {
  @apply p-2 border text-gray-800;
}
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
