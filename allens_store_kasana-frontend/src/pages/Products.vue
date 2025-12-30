<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-semibold mb-6 text-gray-800">📦 Inventory Management</h1>

    <!-- Tabs -->
    <div class="mb-6 flex gap-3 border-b pb-2">
      <button @click="activeTab = 'products'" :class="tabClass('products')">
        Products ({{ products.length }})
      </button>
      <button @click="activeTab = 'categories'" :class="tabClass('categories')">
        Categories ({{ categories.length }})
      </button>
    </div>

    <!-- ================ PRODUCTS TAB ================ -->
    <div v-if="activeTab === 'products'" class="animate-fadeIn">

      <!-- Add/Edit Product Form (Inline at Top) -->
      <form @submit.prevent="submitProduct" class="mb-8 bg-white p-6 rounded-2xl shadow-lg space-y-6">
        <div class="grid md:grid-cols-3 gap-6">
          <div>
            <label class="label">Product Name *</label>
            <input v-model="productForm.name" class="input" placeholder="e.g. Coca Cola" required />
          </div>
          <div>
            <label class="label">SKU / Track No *</label>
            <input v-model="productForm.sku" class="input" placeholder="e.g. CC-001" required />
          </div>
          <div>
            <label class="label">Category *</label>
            <select v-model="productForm.category_id" class="input" required>
              <option value="">Select Category</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
        </div>

        <!-- Units Section -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-2xl p-6">
          <div class="flex justify-between items-center mb-5">
            <h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">🧮 Product Units & Pricing</h2>
            <button type="button" @click="addUnit" class="px-5 py-2 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition shadow">
              + Add Unit
            </button>
          </div>

          <div v-if="productForm.units.length === 0" class="text-center py-8 text-gray-500 italic">
            No units defined. Click "+ Add Unit" to start.
          </div>

          <div v-for="(unit, index) in productForm.units" :key="index" class="grid md:grid-cols-6 gap-4 mb-5 p-5 bg-white rounded-xl shadow border">
            <div>
              <label class="label">Unit Name *</label>
              <input v-model="unit.unit_name" placeholder="e.g. Bottle, Crate" class="input" required />
            </div>
            <div>
              <label class="label">Qty per Base *</label>
              <input v-model.number="unit.conversion_quantity" type="number" min="0.01" step="0.01" class="input" required />
            </div>
            <div>
              <label class="label">Retail Price *</label>
              <input v-model.number="unit.retail_price" type="number" step="100" class="input" required />
            </div>
            <div>
              <label class="label">Wholesale Price</label>
              <input v-model.number="unit.wholesale_price" type="number" step="100" class="input" />
            </div>
            <div>
              <label class="label">Cost Price (Shell/Bottle)</label>
              <input v-model.number="unit.cost_price" type="number" step="50" class="input" />
            </div>
            <div class="flex flex-col justify-center items-center gap-3">
              <label class="label">Returnable?</label>
              <input type="checkbox" v-model="unit.is_returnable" class="w-6 h-6 accent-green-600" />
              <button type="button" @click="removeUnit(index)" class="text-red-600 hover:text-red-800 text-xl">✕</button>
            </div>
          </div>
        </div>

        <div class="flex gap-4">
          <button type="submit" :disabled="loading" class="btn-primary text-lg px-8">
            {{ editingProduct ? 'Update Product' : 'Add Product' }}
          </button>
          <button v-if="editingProduct" type="button" @click="cancelEdit" class="btn-secondary text-lg px-6">
            Cancel
          </button>
        </div>
      </form>

      <!-- Search -->
      <div class="flex gap-4 mb-6">
        <input v-model="searchQuery" @input="debouncedSearch" placeholder="Search by name or SKU..." class="input flex-1" />
        <button @click="fetchProducts" class="btn-gray px-6">Refresh</button>
      </div>

      <!-- Products Table with Expandable Units -->
      <div class="bg-white rounded-2xl shadow overflow-hidden">
        <table class="min-w-full text-sm">
          <thead class="bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700">
            <tr>
              <th class="th">Name</th>
              <th class="th">SKU</th>
              <th class="th">Category</th>
              <th class="th text-center">Units</th>
              <th class="th text-center">Stock</th>
              <th class="th text-center">Last Cost</th>
              <th class="th text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="p in displayedProducts" :key="p.id">
              <tr @click="toggleExpand(p.id)" class="hover:bg-indigo-50 cursor-pointer transition">
                <td class="td font-semibold">{{ p.name }}</td>
                <td class="td">{{ p.sku }}</td>
                <td class="td">{{ getCategoryName(p.category_id) }}</td>
                <td class="td text-center font-medium">{{ p.units?.length || 0 }}</td>
                <td class="td text-center font-bold text-lg" :class="p.quantity > 10 ? 'text-green-600' : 'text-orange-600'">
                  {{ Number(p.quantity).toFixed(2) }}
                </td>
                <td class="td text-center">{{ formatPrice(p.cost_price || 0) }}</td>
                <td class="td text-center space-x-2" @click.stop>
                  <button @click.stop="editProduct(p)" class="btn-sm bg-blue-600 hover:bg-blue-700">Edit</button>
                  <button @click.stop="deleteProduct(p.id)" class="btn-sm bg-red-600 hover:bg-red-700">Delete</button>
                </td>
              </tr>

              <!-- Expanded Row -->
              <tr v-if="expandedProduct === p.id">
                <td colspan="7" class="bg-gradient-to-b from-gray-50 to-white p-6">
                  <h3 class="font-bold text-lg text-gray-800 mb-4">Units Details</h3>
                  <div class="grid md:grid-cols-3 lg:grid-cols-4 gap-5">
                    <div v-for="u in p.units" :key="u.id" class="bg-white p-5 rounded-xl shadow border hover:shadow-lg transition">
                      <div class="font-bold text-indigo-700 text-lg">{{ u.unit_name }}</div>
                      <div class="text-sm text-gray-600 mt-2">Conversion: <strong>{{ u.conversion_quantity }}× base</strong></div>
                      <div class="text-sm mt-1">Retail: <strong class="text-green-600">{{ formatPrice(u.retail_price) }}</strong></div>
                      <div class="text-sm mt-1">Wholesale: <strong class="text-blue-600">{{ formatPrice(u.wholesale_price || 0) }}</strong></div>
                      <div class="text-sm mt-1">Cost: <strong>{{ formatPrice(u.cost_price || 0) }}</strong></div>
                      <div class="text-sm mt-2">
                        Returnable: 
                        <span class="font-bold" :class="u.is_returnable ? 'text-green-600' : 'text-red-600'">
                          {{ u.is_returnable ? 'Yes' : 'No' }}
                        </span>
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

    <!-- ================ CATEGORIES TAB ================ -->
    <div v-if="activeTab === 'categories'" class="animate-fadeIn">
      <form @submit.prevent="submitCategory" class="mb-6 bg-white p-6 rounded-2xl shadow-lg flex gap-4 items-end">
        <div class="flex-1">
          <label class="label">Category Name *</label>
          <input v-model="categoryForm.name" placeholder="e.g. Beverages" class="input" required />
        </div>
        <div>
          <button :disabled="loading" class="btn-primary px-8">
            {{ editingCategory ? 'Update' : 'Add' }} Category
          </button>
          <button v-if="editingCategory" type="button" @click="cancelCategoryEdit" class="btn-secondary ml-3">
            Cancel
          </button>
        </div>
      </form>

      <div class="grid md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div v-for="cat in categories" :key="cat.id" class="bg-white p-6 rounded-2xl shadow hover:shadow-xl transition">
          <h3 class="font-bold text-xl text-gray-800">{{ cat.name }}</h3>
          <p class="text-gray-600 text-sm mt-2">{{ cat.description || 'No description' }}</p>
          <div class="flex gap-3 mt-4">
            <button @click="editCategory(cat)" class="btn-sm bg-blue-600 hover:bg-blue-700 flex-1">Edit</button>
            <button @click="deleteCategory(cat.id)" class="btn-sm bg-red-600 hover:bg-red-700 flex-1">Delete</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Notification -->
    <transition name="fade">
      <div v-if="notification" class="fixed bottom-6 right-6 bg-gray-900 text-white px-6 py-4 rounded-xl shadow-2xl text-sm font-medium z-50">
        {{ notification }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// CHANGE THIS TO YOUR FLASK URL
const API_BASE = 'http://127.0.0.1:5000';

const activeTab = ref('products');
const products = ref([]);
const categories = ref([]);
const displayedProducts = ref([]);
const searchQuery = ref('');
const expandedProduct = ref(null);
const loading = ref(false);
const notification = ref('');

let tempIdCounter = 0;

const productForm = ref({
  id: null,
  name: '',
  sku: '',
  category_id: '',
  units: []
});

const categoryForm = ref({
  id: null,
  name: '',
  description: ''
});

const editingProduct = ref(false);
const editingCategory = ref(false);

// Styling
const tabClass = (tab) => {
  return `px-6 py-3 rounded-t-lg font-semibold transition ${
    activeTab.value === tab
      ? 'bg-blue-600 text-white shadow-lg'
      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
  }`;
};

// API Calls
const fetchProducts = async () => {
  try {
    loading.value = true;
    const res = await axios.get(`${API_BASE}/inventory/products`);
    products.value = res.data;
    displayedProducts.value = res.data;
  } catch (err) {
    notify('Failed to load products');
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const fetchCategories = async () => {
  try {
    const res = await axios.get(`${API_BASE}/inventory/categories`);
    categories.value = res.data;
  } catch {
    notify('Failed to load categories');
  }
};

// Search
let searchTimeout;
const debouncedSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    const q = searchQuery.value.toLowerCase().trim();
    if (!q) {
      displayedProducts.value = products.value;
      return;
    }
    displayedProducts.value = products.value.filter(p =>
      p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q)
    );
  }, 300);
};

// Units
const addUnit = () => {
  productForm.value.units.push({
    unit_name: '',
    conversion_quantity: 1,
    retail_price: 0,
    wholesale_price: 0,
    cost_price: 0,
    is_returnable: false
  });
};

const removeUnit = (index) => {
  if (productForm.value.units.length <= 1) {
    notify('At least one unit is required');
    return;
  }
  productForm.value.units.splice(index, 1);
};

// Product Actions
const openProductModal = () => {}; // Not needed anymore — form is inline

const editProduct = (product) => {
  productForm.value = {
    id: product.id,
    name: product.name,
    sku: product.sku,
    category_id: product.category_id || '',
    units: product.units && product.units.length > 0
      ? product.units.map(u => ({ ...u }))
      : [{ unit_name: 'Kilo', conversion_quantity: 1, retail_price: 0, wholesale_price: 0, cost_price: 0, is_returnable: false }]
  };
  editingProduct.value = true;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const cancelEdit = () => {
  productForm.value = { id: null, name: '', sku: '', category_id: '', units: [] };
  editingProduct.value = false;
};

const submitProduct = async () => {
  if (!productForm.value.name.trim()) return notify('Product name required');
  if (!productForm.value.sku.trim()) return notify('SKU required');
  if (!productForm.value.category_id) return notify('Select a category');
  if (productForm.value.units.length === 0) return notify('Add at least one unit');
  if (productForm.value.units.some(u => !u.unit_name.trim())) return notify('All units need a name');

  loading.value = true;
  try {
    const payload = {
      name: productForm.value.name.trim(),
      sku: productForm.value.sku.trim(),
      category_id: productForm.value.category_id,
      units: productForm.value.units
    };

    if (editingProduct.value) {
      await axios.put(`${API_BASE}/inventory/products/${productForm.value.id}`, payload);
      notify('Product updated successfully!');
    } else {
      await axios.post(`${API_BASE}/inventory/products`, payload);
      notify('Product added successfully!');
    }

    cancelEdit();
    await fetchProducts();
  } catch (err) {
    console.error(err);
    notify('Failed to save product');
  } finally {
    loading.value = false;
  }
};

const deleteProduct = async (id) => {
  if (!confirm('Delete this product permanently?')) return;
  try {
    await axios.delete(`${API_BASE}/inventory/products/${id}`);
    notify('Product deleted');
    fetchProducts();
  } catch {
    notify('Failed to delete');
  }
};

const toggleExpand = (id) => {
  expandedProduct.value = expandedProduct.value === id ? null : id;
};

// Category Actions
const editCategory = (cat) => {
  categoryForm.value = { ...cat };
  editingCategory.value = true;
};

const cancelCategoryEdit = () => {
  categoryForm.value = { id: null, name: '', description: '' };
  editingCategory.value = false;
};

const submitCategory = async () => {
  if (!categoryForm.value.name.trim()) return notify('Category name required');
  try {
    if (editingCategory.value) {
      await axios.put(`${API_BASE}/inventory/categories/${categoryForm.value.id}`, categoryForm.value);
      notify('Category updated');
    } else {
      await axios.post(`${API_BASE}/inventory/categories`, categoryForm.value);
      notify('Category added');
    }
    cancelCategoryEdit();
    fetchCategories();
  } catch {
    notify('Error saving category');
  }
};

const deleteCategory = async (id) => {
  if (!confirm('Delete this category?')) return;
  try {
    await axios.delete(`${API_BASE}/inventory/categories/${id}`);
    notify('Category deleted');
    fetchCategories();
  } catch {
    notify('Failed to delete');
  }
};

const getCategoryName = (id) => {
  const cat = categories.value.find(c => c.id === id);
  return cat ? cat.name : '-';
};

const formatPrice = (val) => {
  const value = Number(val) || 0;
  return new Intl.NumberFormat('en-UG', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

const notify = (msg, duration = 3500) => {
  notification.value = msg;
  setTimeout(() => notification.value = '', duration);
};

onMounted(() => {
  fetchCategories();
  fetchProducts();
});
</script>

<style scoped>
.label {
  @apply block text-sm font-semibold text-gray-700 mb-2;
}
.input {
  @apply w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none transition;
}
.btn-primary {
  @apply bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 shadow-lg transition;
}
.btn-secondary {
  @apply bg-gray-500 text-white px-6 py-3 rounded-xl font-semibold hover:bg-gray-600 transition;
}
.btn-gray {
  @apply bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium hover:bg-gray-300 transition;
}
.btn-sm {
  @apply px-4 py-2 text-xs rounded-lg text-white font-medium transition shadow;
}
.th {
  @apply px-5 py-4 text-left font-bold text-gray-700 border-b-2 border-gray-300;
}
.td {
  @apply px-5 py-4 border-b text-gray-800;
}
.animate-fadeIn {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>