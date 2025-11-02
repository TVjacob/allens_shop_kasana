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
      <form @submit.prevent="submitProduct" class="mb-6 bg-white p-6 rounded-2xl shadow-md space-y-6">
        <div class="grid md:grid-cols-3 gap-4">
          <div>
            <label class="label">Product Name</label>
            <input v-model="productForm.name" class="input" placeholder="Enter name" required />
          </div>
          <div>
            <label class="label">Track No / SKU</label>
            <input v-model="productForm.sku" class="input" placeholder="Enter SKU" required />
          </div>
          <div>
            <label class="label">Category</label>
            <select v-model="productForm.category_id" class="input" required>
              <option value="">Select Category</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
        </div>

        <!-- Product Units Section -->
        <div class="bg-gradient-to-b from-gray-50 to-white border rounded-2xl p-6 mt-4 shadow-sm">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">🧾 Product Units</h2>
            <button type="button" @click="addUnit" class="px-4 py-1.5 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-all shadow-sm">
              + Add Unit
            </button>
          </div>

          <div v-if="productForm.units.length === 0" class="text-gray-500 italic text-sm bg-gray-50 p-4 rounded-lg">
            No units added yet. Click “+ Add Unit” to begin.
          </div>

          <div
            v-for="(unit, index) in productForm.units"
            :key="index"
            class="grid md:grid-cols-5 gap-4 mb-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm transition hover:shadow-md"
          >
            <div>
              <label class="label">Unit Name</label>
              <input v-model="unit.unit_name" placeholder="e.g. Bottle, Box, Crate" class="input" required />
            </div>

            <div>
              <label class="label">Qty per Base</label>
              <input v-model.number="unit.conversion_quantity" type="number" min="1" placeholder="1" class="input" required />
            </div>

            <div>
              <label class="label">Retail Price (UGX)</label>
              <input v-model.number="unit.retail_price" type="number" placeholder="UGX 0" class="input" />
            </div>

            <div>
              <label class="label">Wholesale Price (UGX)</label>
              <input v-model.number="unit.wholesale_price" type="number" placeholder="UGX 0" class="input" />
            </div>

            <div>
              <label class="label">Cost Price for  shell or bottle</label>
              <input v-model.number="unit.cost_price" type="number" placeholder="UGX 0" class="input" />
            </div>

            <div class="flex flex-col items-center justify-center col-span-1 md:col-span-1">
              <label class="label text-center">is it returnable</label>
              <div class="flex items-center gap-2">
                <input type="checkbox" v-model="unit.is_returnable" class="scale-125 accent-blue-600" />
                <button type="button" @click="removeUnit(index)" class="btn-sm bg-red-500 hover:bg-red-600">✕</button>
              </div>
            </div>
          </div>
        </div>

        <div class="flex gap-3 mt-4">
          <button class="btn-primary" :disabled="loading">{{ editingProduct ? 'Update Product' : 'Add Product' }}</button>
          <button v-if="editingProduct" type="button" @click="cancelProductEdit" class="btn-secondary">Cancel</button>
        </div>
      </form>

      <!-- Search -->
      <div class="flex flex-wrap gap-3 mb-4">
        <input v-model="searchQuery" @input="searchProducts" class="input flex-1" placeholder="Search by name or SKU" />
        <button @click="fetchProducts" class="btn-gray">Reset</button>
      </div>

      <!-- Products Table -->
      <div class="overflow-x-auto bg-white rounded-2xl shadow">
        <table class="min-w-full border-collapse text-sm">
          <thead class="bg-gray-100 text-gray-700">
            <tr>
              <th class="th">Name</th>
              <th class="th">SKU</th>
              <th class="th">Category</th>
              <th class="th text-center">Units</th>
              <th class="th text-center">Stock</th>
              <th class="th text-center">Purchase Price</th>


              <th class="th text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="product in products" :key="product.id">
              <tr class="hover:bg-blue-50 cursor-pointer" @click="toggleExpand(product.id)">
                <td class="td font-medium">{{ product.name }}</td>
                <td class="td">{{ product.sku }}</td>
                <td class="td">{{ getCategoryName(product.category_id) }}</td>
                <td class="td text-center">{{ product.units?.length ?? 0 }}</td>
                <td class="td text-center">{{ product.quantity ?? 0 }}</td>
                <td class="td text-center">{{ formatPrice(product.last_purchase_price ?? 0 )}}</td>

                <td class="td text-center">
                  <button @click.stop="editProduct(product)" class="btn-sm bg-blue-500 hover:bg-blue-600">Edit</button>
                  <button @click.stop="deleteProduct(product.id)" class="btn-sm bg-red-500 hover:bg-red-600">Delete</button>
                </td>
              </tr>

              <!-- Expandable Units Row -->
              <tr v-if="expandedProduct === product.id">
                <td colspan="5" class="bg-gray-50 p-4 rounded-b-xl">
                  <h3 class="font-semibold text-gray-700 mb-2">Units & Containers:</h3>
                  <div class="grid md:grid-cols-5 gap-4">
                    <div v-for="u in product.units" :key="u.id" class="p-3 bg-white rounded-xl shadow-sm border border-gray-200">
                      <div class="font-medium text-gray-800">{{ u.unit_name }}</div>
                      <div class="text-gray-600 text-sm">Qty/Base: <span class="font-semibold">{{ u.conversion_quantity }}</span></div>
                      <div class="text-gray-600 text-sm">Retail: <span class="font-semibold text-green-600">{{ formatPrice(u.retail_price) }}</span></div>
                      <div class="text-gray-600 text-sm">Wholesale: <span class="font-semibold text-blue-600">{{ formatPrice(u.wholesale_price) }}</span></div>
                      <div class="text-gray-600 text-sm">Cost: <span class="font-semibold">{{ formatPrice(u.cost_price) }}</span></div>
                      <div class="text-gray-600 text-sm">Refundable: 
                        <span class="font-semibold" :class="u.is_returnable ? 'text-green-600' : 'text-red-600'">
                          {{ u.is_returnable ? '✔️' : '❌' }}
                        </span>
                      </div>

                      <div v-if="u.containers && u.containers.length > 0" class="mt-2">
                        <div class="font-semibold text-gray-700 mb-1">Containers:</div>
                        <ul class="text-sm text-gray-600 list-disc list-inside">
                          <li v-for="c in u.containers" :key="c.id">
                            {{ c.name }} - In Stock: {{ c.total_in_stock || 0 }}
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ---------------- Categories Tab ---------------- -->
    <div v-if="activeTab==='categories'" class="animate-fadeIn">
      <form @submit.prevent="submitCategory" class="flex gap-3 flex-wrap mb-4 bg-white p-4 rounded-2xl shadow">
        <input v-model="categoryForm.name" placeholder="Category Name" class="input" required />
        <button :disabled="loading" class="btn-primary">{{ editingCategory ? 'Update' : 'Add' }} Category</button>
        <button v-if="editingCategory" type="button" @click="cancelCategoryEdit" class="btn-secondary">Cancel</button>
      </form>

      <div class="overflow-x-auto bg-white rounded-2xl shadow">
        <table class="min-w-full border-collapse text-sm">
          <thead class="bg-gray-100 text-gray-700">
            <tr>
              <th class="th">ID</th>
              <th class="th">Name</th>
              <th class="th text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in categories" :key="cat.id" class="hover:bg-blue-50">
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
      <div v-if="notification" class="fixed bottom-4 right-4 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg text-sm">
        {{ notification }}
      </div>
    </transition>
  </div>
</template>

<script>
import api from '../api';

export default {
  data() {
    return {
      activeTab: 'products',
      products: [],
      categories: [],
      productForm: { id: null, name: '', sku: '', category_id: '', units: [] },
      editingProduct: false,
      categoryForm: { id: null, name: '' },
      editingCategory: false,
      expandedProduct: null,
      searchQuery: '',
      loading: false,
      notification: '',
    };
  },
  methods: {
    tabClass(tab) {
      return `px-4 py-2 rounded-t-lg font-semibold transition ${
        this.activeTab === tab
          ? 'bg-blue-600 text-white shadow'
          : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
      }`;
    },
    showNotification(msg, duration = 3000) {
      this.notification = msg;
      setTimeout(() => (this.notification = ''), duration);
    },

    // --- Units ---
    addUnit() {
      this.productForm.units.push({
        unit_name: '',
        conversion_quantity: 1,
        retail_price: 0,
        wholesale_price: 0,
        cost_price: 0,
        is_returnable: false,
        containers: [],
      });
    },
    removeUnit(index) {
      this.productForm.units.splice(index, 1);
    },

    // --- Products ---
    async fetchProducts() {
      try {
        this.loading = true;
        const res = await api.get('/inventory/products');
        this.products = res.data;
      } catch {
        this.showNotification('Failed to load products.');
      } finally {
        this.loading = false;
      }
    },
    async submitProduct() {
      if (!this.productForm.name.trim()) return this.showNotification('Product name is required.');
      if (!this.productForm.sku.trim()) return this.showNotification('SKU is required.');
      if (!this.productForm.category_id) return this.showNotification('Select a category.');
      try {
        this.loading = true;
        if (this.editingProduct) {
          await api.put(`/inventory/products/${this.productForm.id}`, this.productForm);
          this.showNotification('Product updated successfully!');
        } else {
          await api.post(`/inventory/products`, this.productForm);
          this.showNotification('Product added successfully!');
        }
        this.cancelProductEdit();
        this.fetchProducts();
      } catch {
        this.showNotification('Error saving product.');
      } finally {
        this.loading = false;
      }
    },
    editProduct(product) {
      this.productForm = JSON.parse(JSON.stringify(product));
      this.editingProduct = true;
    },
    cancelProductEdit() {
      this.productForm = { id: null, name: '', sku: '', category_id: '', units: [] };
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
    toggleExpand(id) {
      this.expandedProduct = this.expandedProduct === id ? null : id;
    },

    // --- Categories ---
    async fetchCategories() {
      const res = await api.get('/inventory/categories');
      this.categories = res.data;
    },
    async submitCategory() {
      if (!this.categoryForm.name.trim()) return;
      if (this.editingCategory)
        await api.put(`/inventory/categories/${this.categoryForm.id}`, this.categoryForm);
      else await api.post('/inventory/categories', this.categoryForm);
      this.categoryForm = { id: null, name: '' };
      this.editingCategory = false;
      this.fetchCategories();
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
      await api.delete(`/inventory/categories/${id}`);
      this.fetchCategories();
    },

    // formatPrice(v) {
    //   return new Intl.NumberFormat('en-UG', { style: 'currency', currency: 'UGX' }).format(v || 0);
    // },
    formatPrice(v) {
  const value = Number(v) || 0;
  return new Intl.NumberFormat('en-UG', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
},

    getCategoryName(id) {
      const c = this.categories.find((x) => x.id === id);
      return c ? c.name : '';
    },

    searchProducts() {
      const query = this.searchQuery.trim().toLowerCase();
      if (!query) {
        this.fetchProducts();
        return;
      }
      this.products = this.products.filter(
        p => p.name.toLowerCase().includes(query) || p.sku.toLowerCase().includes(query)
      );
    },
  },
  mounted() {
    this.fetchCategories();
    this.fetchProducts();
  },
};
</script>

<style scoped>
.label {
  @apply text-gray-700 font-semibold text-sm mb-1 block;
}
.input {
  @apply border border-gray-300 rounded-lg px-3 py-2 w-full focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition;
}
.btn-primary {
  @apply bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all shadow;
}
.btn-secondary {
  @apply bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-all shadow;
}
.btn-gray {
  @apply bg-gray-100 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-200 transition-all shadow-sm;
}
.btn-sm {
  @apply text-white text-xs px-3 py-1 rounded-lg shadow hover:opacity-90 transition;
}
.th {
  @apply border p-2 text-left font-semibold text-gray-700 bg-gray-50;
}
.td {
  @apply border p-2 text-gray-800;
}

/* Table & hover effects */
table {
  @apply w-full border border-gray-200 rounded-xl overflow-hidden;
}
tr:hover td {
  @apply bg-blue-50 transition;
}

/* Animations */
.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Notification */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
