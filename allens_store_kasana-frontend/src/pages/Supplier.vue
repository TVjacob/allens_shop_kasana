<template>
  <div class="p-6 bg-gray-50 min-h-screen">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Suppliers</h1>

    <!-- Add / Edit Supplier Form -->
    <form
      @submit.prevent="submitSupplier"
      class="mb-8 flex flex-wrap gap-3 bg-white p-4 rounded-xl shadow-sm"
    >
      <input
        v-model="supplierForm.name"
        placeholder="Supplier Name"
        class="form-input"
        required
      />
      <input
        v-model="supplierForm.contact"
        placeholder="Contact"
        class="form-input"
      />
      <input
        v-model="supplierForm.email"
        placeholder="Email"
        type="email"
        class="form-input"
      />

      <button
        type="submit"
        class="btn-primary"
      >
        {{ editing ? 'Update' : 'Add' }} Supplier
      </button>

      <button
        v-if="editing"
        type="button"
        @click="cancelEdit"
        class="btn-secondary"
      >
        Cancel
      </button>
    </form>

    <!-- Search & Export -->
    <div class="mb-4 flex flex-wrap gap-2 items-center">
      <input
        v-model="searchQuery"
        placeholder="🔍 Search by name or contact..."
        class="form-input w-72"
      />
      <button @click="fetchSuppliers" class="btn-gray">Reset</button>
      <button @click="exportExcel" class="btn-warning">Export Excel</button>
      <button @click="exportPDF" class="btn-danger">Export PDF</button>
    </div>

    <!-- Suppliers Table -->
    <div class="overflow-x-auto bg-white rounded-xl shadow-sm border">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100 text-gray-700">
          <tr>
            <th class="table-header">ID</th>
            <th class="table-header">Name</th>
            <th class="table-header">Contact</th>
            <th class="table-header">Email</th>
            <th class="table-header">Actions</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="supplier in filteredSuppliers"
            :key="supplier.id"
            class="hover:bg-gray-50 transition-colors"
          >
            <td class="table-cell">{{ supplier.id }}</td>
            <td class="table-cell">{{ supplier.name }}</td>
            <td class="table-cell">{{ supplier.contact }}</td>
            <td class="table-cell">{{ supplier.email }}</td>
            <td class="table-cell">
              <div class="flex gap-2">
                <button
                  @click="editSupplier(supplier)"
                  class="btn-edit"
                >
                  Edit
                </button>
                <button
                  @click="deleteSupplier(supplier.id)"
                  class="btn-delete"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>

          <tr v-if="filteredSuppliers.length === 0">
            <td colspan="5" class="p-4 text-center text-gray-500">
              No suppliers found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import api from "../api";
import * as XLSX from "xlsx";
import jsPDF from "jspdf";
import "jspdf-autotable";

export default {
  name: "SuppliersPage",
  data() {
    return {
      suppliers: [],
      supplierForm: { id: null, name: "", contact: "", email: "" },
      editing: false,
      searchQuery: "",
    };
  },
  computed: {
    /** 🔍 Live filtered list */
    filteredSuppliers() {
      const q = this.searchQuery.toLowerCase();
      return this.suppliers.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          (s.contact && s.contact.toLowerCase().includes(q))
      );
    },
  },
  methods: {
    /** Fetch all suppliers */
    async fetchSuppliers() {
      try {
        const { data } = await api.get("/suppliers/");
        this.suppliers = data;
      } catch (err) {
        console.error("❌ Error fetching suppliers:", err);
        alert("Failed to fetch suppliers. Please check your connection.");
      }
    },

    /** Add or update supplier */
    async submitSupplier() {
      try {
        if (this.editing) {
          await api.put(`/suppliers/${this.supplierForm.id}`, this.supplierForm);
          alert("✅ Supplier updated successfully!");
        } else {
          await api.post("/suppliers/", this.supplierForm);
          alert("✅ Supplier added successfully!");
        }

        this.resetForm();
        this.fetchSuppliers();
      } catch (err) {
        console.error("❌ Error submitting supplier:", err);
        alert("Failed to save supplier. Please verify your inputs.");
      }
    },

    editSupplier(supplier) {
      this.supplierForm = { ...supplier };
      this.editing = true;
    },

    cancelEdit() {
      this.resetForm();
    },

    resetForm() {
      this.supplierForm = { id: null, name: "", contact: "", email: "" };
      this.editing = false;
    },

    async deleteSupplier(id) {
      if (!confirm("Are you sure you want to delete this supplier?")) return;
      try {
        await api.delete(`/suppliers/${id}`);
        alert("🗑️ Supplier deleted successfully!");
        this.fetchSuppliers();
      } catch (err) {
        console.error("❌ Error deleting supplier:", err);
        alert("Failed to delete supplier. Please try again later.");
      }
    },

    /** 📤 Export to Excel */
    exportExcel() {
      const ws = XLSX.utils.json_to_sheet(
        this.filteredSuppliers.map((s) => ({
          ID: s.id,
          Name: s.name,
          Contact: s.contact,
          Email: s.email,
        }))
      );
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "Suppliers");
      XLSX.writeFile(wb, "Suppliers_List.xlsx");
    },

    /** 📄 Export to PDF */
    exportPDF() {
      const doc = new jsPDF();
      doc.setFontSize(16);
      doc.text("Suppliers List", 14, 15);
      doc.autoTable({
        head: [["ID", "Name", "Contact", "Email"]],
        body: this.filteredSuppliers.map((s) => [
          s.id,
          s.name,
          s.contact,
          s.email,
        ]),
        startY: 25,
      });
      doc.save("Suppliers_List.pdf");
    },
  },
  mounted() {
    this.fetchSuppliers();
  },
};
</script>

<style scoped>
/* 🌈 Modern dashboard-style CSS */

.form-input {
  @apply border border-gray-300 rounded-lg p-2 w-52 focus:ring-2 focus:ring-blue-400 focus:outline-none transition;
}

.btn-primary {
  @apply bg-blue-600 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-700 active:scale-95 transition;
}

.btn-secondary {
  @apply bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 active:scale-95 transition;
}

.btn-gray {
  @apply bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition;
}

.btn-warning {
  @apply bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 active:scale-95 transition;
}

.btn-danger {
  @apply bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 active:scale-95 transition;
}

.btn-edit {
  @apply bg-blue-400 text-white px-3 py-1 rounded-lg hover:bg-blue-500 transition;
}

.btn-delete {
  @apply bg-red-500 text-white px-3 py-1 rounded-lg hover:bg-red-600 transition;
}

.table-header {
  @apply p-3 text-left border-b font-semibold;
}

.table-cell {
  @apply p-3 border-b text-gray-700;
}
</style>
