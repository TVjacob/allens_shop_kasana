<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Customer Management</h1>

    <!-- Add/Edit Customer Form -->
    <div class="mb-6">
      <h2 class="font-bold mb-2">Add / Edit Customer</h2>
      <form @submit.prevent="submitCustomer" class="flex gap-2 flex-wrap mb-4">
        <input
          v-model="customerForm.name"
          placeholder="Customer Name"
          class="border p-2 rounded"
          required
        />
        <input v-model="customerForm.phone" placeholder="Phone" class="border p-2 rounded" />
        <input v-model="customerForm.email" type="email" placeholder="Email" class="border p-2 rounded" />
        <input v-model="customerForm.address" placeholder="Address" class="border p-2 rounded" />

        <button class="bg-indigo-500 text-white px-4 py-2 rounded">
          {{ editingCustomer ? 'Update' : 'Add' }} Customer
        </button>

        <button
          v-if="editingCustomer"
          type="button"
          @click="cancelEdit"
          class="bg-gray-500 text-white px-4 py-2 rounded"
        >
          Cancel
        </button>
      </form>

      <!-- ✅ Inline error message display -->
      <p v-if="errorMessage" class="text-red-600 font-semibold">{{ errorMessage }}</p>
    </div>

    <!-- Search Customers -->
    <div class="mb-4 flex gap-2 flex-wrap">
      <input
        v-model="searchQuery"
        placeholder="Search by name, phone, or email"
        @input="searchCustomers"
        class="border p-2 rounded flex-1"
      />
      <button @click="fetchCustomers" class="bg-gray-300 px-4 py-2 rounded">Reset</button>
      <button @click="exportExcel" class="bg-yellow-500 text-white px-4 py-2 rounded">Export Excel</button>
      <button @click="exportPDF" class="bg-red-500 text-white px-4 py-2 rounded">Export PDF</button>
    </div>

    <!-- Customers Table -->
    <div v-if="loading" class="text-gray-500 text-center py-4">Loading customers...</div>

    <table v-else class="min-w-full bg-white border shadow-md">
      <thead>
        <tr class="bg-gray-100">
          <th class="p-2 border">ID</th>
          <th class="p-2 border">Name</th>
          <th class="p-2 border">Phone</th>
          <th class="p-2 border">Email</th>
          <th class="p-2 border">Address</th>
          <th class="p-2 border">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="customer in filteredCustomers" :key="customer.id" class="hover:bg-gray-50">
          <td class="p-2 border">{{ customer.id }}</td>
          <td class="p-2 border">{{ customer.name }}</td>
          <td class="p-2 border">{{ customer.phone }}</td>
          <td class="p-2 border">{{ customer.email }}</td>
          <td class="p-2 border">{{ customer.address }}</td>
          <td class="p-2 border flex gap-2">
            <button
              @click="editCustomer(customer)"
              class="bg-blue-400 text-white px-2 py-1 rounded"
            >
              Edit
            </button>
            <button
              @click="deleteCustomer(customer.id)"
              class="bg-red-500 text-white px-2 py-1 rounded"
            >
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
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
      customers: [],
      filteredCustomers: [],
      customerForm: { id: null, name: '', phone: '', email: '', address: '' },
      editingCustomer: false,
      searchQuery: '',
      errorMessage: '',
      loading: false,
      searchTimeout: null, // 🔹 debounce timer
    };
  },
  async mounted() {
    await this.fetchCustomers();
  },
  methods: {
    async fetchCustomers() {
      try {
        this.loading = true;
        const res = await api.get('/customer/');
        this.customers = res.data;
        this.filteredCustomers = res.data;
      } catch (err) {
        console.error(err);
        this.errorMessage = 'Failed to load customers.';
      } finally {
        this.loading = false;
      }
    },

    // 🔹 Live Search with Debounce + case-insensitive match
    async searchCustomers() {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(async () => {
        const query = this.searchQuery.trim().toLowerCase();

        if (!query) {
          this.filteredCustomers = this.customers;
          return;
        }

        try {
          this.loading = true;
          const res = await api.get('/customer/search', {
            params: { query },
          });

          if (res.data && res.data.length > 0) {
            this.filteredCustomers = res.data;
          } else {
            // fallback local filtering
            this.filteredCustomers = this.customers.filter(
              (c) =>
                (c.name && c.name.toLowerCase().includes(query)) ||
                (c.phone && c.phone.toLowerCase().includes(query)) ||
                (c.email && c.email.toLowerCase().includes(query))
            );
          }
        } catch (err) {
          console.error('Search error:', err);
        } finally {
          this.loading = false;
        }
      }, 300);
    },

    async submitCustomer() {
      this.errorMessage = '';

      // ✅ Validation
      if (!this.customerForm.name.trim()) {
        this.errorMessage = 'Customer name is required.';
      } else if (this.customerForm.phone && !/^[0-9+\-\s]{7,15}$/.test(this.customerForm.phone)) {
        this.errorMessage = 'Invalid phone number format.';
      } else if (this.customerForm.email && !/^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$/.test(this.customerForm.email)) {
        this.errorMessage = 'Invalid email address.';
      }

      if (this.errorMessage) return;

      try {
        this.loading = true;
        if (this.editingCustomer) {
          await api.put(`/customer/${this.customerForm.id}`, this.customerForm);
        } else {
          await api.post('/customer/', this.customerForm);
        }

        this.customerForm = { id: null, name: '', phone: '', email: '', address: '' };
        this.editingCustomer = false;
        await this.fetchCustomers();
      } catch (err) {
        console.error('Error saving customer:', err);
        this.errorMessage = 'Something went wrong while saving the customer.';
      } finally {
        this.loading = false;
      }
    },

    editCustomer(customer) {
      this.customerForm = { ...customer };
      this.editingCustomer = true;
      this.errorMessage = '';
    },

    cancelEdit() {
      this.customerForm = { id: null, name: '', phone: '', email: '', address: '' };
      this.editingCustomer = false;
      this.errorMessage = '';
    },

    async deleteCustomer(id) {
      if (confirm('Are you sure you want to delete this customer?')) {
        try {
          await api.delete(`/customer/${id}`);
          this.fetchCustomers();
        } catch (err) {
          console.error(err);
          this.errorMessage = 'Failed to delete customer.';
        }
      }
    },

    exportExcel() {
      const ws = XLSX.utils.json_to_sheet(this.filteredCustomers);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Customers');
      XLSX.writeFile(wb, 'customers.xlsx');
    },

    exportPDF() {
      const doc = new jsPDF();
      doc.text('Customer List', 14, 15);
      const rows = this.filteredCustomers.map((c) => [
        c.id,
        c.name,
        c.phone,
        c.email,
        c.address,
      ]);
      doc.autoTable({
        startY: 20,
        head: [['ID', 'Name', 'Phone', 'Email', 'Address']],
        body: rows,
      });
      doc.save('customers.pdf');
    },
  },
};
</script>

<style scoped>
input {
  @apply border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-indigo-400;
}
button {
  transition: 0.2s;
}
button:hover {
  opacity: 0.9;
}
</style>
