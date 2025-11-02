<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Expenses Management</h1>

    <!-- Add Expense Button -->
    <button
      @click="showModal = true"
      class="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded shadow transition transform hover:scale-105 mb-4"
    >
      + Add Expense
    </button>

    <!-- Grand Total -->
    <div class="mb-4 p-4 bg-gray-100 rounded shadow hover:shadow-lg transition transform hover:scale-[1.01]">
      <h2 class="text-lg font-bold">
        Grand Total Paid: <span class="text-green-600">{{ grandTotal.toFixed(2) }}</span>
      </h2>
    </div>

    <!-- Search & Export -->
    <div class="mb-4 flex flex-wrap gap-2">
      <input
        v-model="searchQuery"
        placeholder="Search description or reference"
        class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition"
      />
      <button @click="searchExpenses" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded shadow transition transform hover:scale-105">Search</button>
      <button @click="fetchExpenses" class="bg-gray-300 hover:bg-gray-400 px-4 py-2 rounded shadow transition transform hover:scale-105">Reset</button>
      <button @click="exportExcel" class="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded shadow transition transform hover:scale-105">Export Excel</button>
      <button @click="exportPDF" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded shadow transition transform hover:scale-105">Export PDF</button>

      <!-- Add Expense Item Button -->
      <button
        @click="showItemModal = true"
        class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded shadow transition transform hover:scale-105 mb-4 ml-2"
      >
        + Add Expense Item
      </button>
    </div>

    <!-- Expenses Table -->
    <div class="overflow-x-auto border rounded-lg shadow-lg">
      <table class="min-w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="p-3 border-b text-center"></th>
            <th class="p-3 border-b text-left">ID</th>
            <th class="p-3 border-b text-left">Description</th>
            <th class="p-3 border-b text-right">Total Amount</th>
            <th class="p-3 border-b text-left">Reference</th>
            <th class="p-3 border-b text-left">Expense Date</th>
            <th class="p-3 border-b text-left">Transaction No</th>
            <th class="p-3 border-b text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(expense, index) in expenses" :key="expense.id">
            <tr
              class="transition-all duration-300 hover:bg-gray-50 hover:shadow-sm cursor-pointer transform hover:scale-[1.01]"
            >
              <td class="p-3 text-center">
                <button @click="toggleExpand(expense.id, index)" class="text-blue-600 font-bold transition transform hover:scale-110">
                  {{ expandedRows.includes(expense.id) ? '-' : '+' }}
                </button>
              </td>
              <td class="p-3">{{ expense.id }}</td>
              <td class="p-3">{{ expense.description }}</td>
              <td class="p-3 text-right">{{ expense.total_amount.toFixed(2) }}</td>
              <td class="p-3">{{ expense.reference }}</td>
              <td class="p-3">{{ formatDate(expense.expense_date) }}</td>
              <td class="p-3">{{ expense.transaction_no }}</td>
              <td class="p-3 text-center flex flex-wrap gap-1 justify-center">
                <button @click="editExpense(expense)" class="bg-blue-400 hover:bg-blue-500 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">Edit</button>
                <button @click="deleteExpense(expense.id)" class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">Delete</button>
                <router-link :to="`/reports/expenses/${expense.id}`" class="text-indigo-600 underline hover:text-indigo-800 transition">
                  View
                </router-link>
              </td>
            </tr>

            <!-- Expanded Details with accordion animation -->
            <tr>
              <td colspan="8" class="p-0 border">
                <div
                  class="overflow-hidden transition-all duration-500 ease-in-out"
                  :style="{ height: expandedRowHeights[expense.id] || 0 + 'px' }"
                  ref="expandedRowsRefs"
                >
                  <div class="p-4 bg-gray-50 border-t shadow-inner">
                    <h3 class="font-semibold mb-2">Expense Items</h3>
                    <table class="w-full border text-sm">
                      <thead>
                        <tr>
                          <th class="p-2 border">Account</th>
                          <th class="p-2 border">Item Name</th>
                          <th class="p-2 border">Description</th>
                          <th class="p-2 border">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="item in expense.items" :key="`item-${item.id}`" class="hover:bg-gray-100 transition">
                          <td class="p-2 border">{{ getAccountName(item.account_id) }}</td>
                          <td class="p-2 border">{{ item.item_name }}</td>
                          <td class="p-2 border">{{ item.description }}</td>
                          <td class="p-2 border">{{ item.amount.toFixed(2) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Expense Modal -->
    <div v-if="showModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 animate-fadeInModal">
      <div class="bg-white rounded-lg p-6 w-full max-w-[806px] relative shadow-xl transform transition-all scale-95 animate-scaleUp">
        <h2 class="text-xl font-bold mb-4">{{ editingExpense ? 'Edit Expense' : 'Add Expense' }}</h2>
        <button @click="closeModal" class="absolute top-2 right-2 text-gray-600 hover:text-gray-800 transition transform hover:scale-110">✖</button>

        <!-- Expense Header -->
        <div class="grid grid-cols-2 gap-4 mb-4">
          <input v-model="expenseForm.description" placeholder="Expense Description" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input v-model="expenseForm.reference" placeholder="Reference" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input list="paymentAccounts" v-model="expenseForm.payment_account_name" placeholder="Payment Account (Cash/Bank)" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" @focus="fetchCashBankAccounts('')"/>
          <datalist id="paymentAccounts">
            <option v-for="acc in cashBankAccounts" :key="acc.id" :value="acc.name"></option>
          </datalist>
          <input v-model="expenseForm.expense_date" type="date" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
        </div>

        <!-- Expense Items -->
        <h3 class="font-bold mb-2">Expense Items</h3>
        <div v-for="(item, index) in expenseForm.items" :key="`item-${index}`" class="grid grid-cols-5 gap-2 mb-2">
          <input list="expenseAccounts" v-model="item.account_name" placeholder="Select Expense Account" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" @focus="fetchExpenseAccounts('')"/>
          <datalist id="expenseAccounts">
            <option v-for="acc in expenseAccounts" :key="acc.id" :value="acc.name"></option>
          </datalist>
          <input v-model="item.item_name" placeholder="Item Name" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input v-model="item.description" placeholder="Item Description" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <input v-model.number="item.amount" type="number" placeholder="Amount" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
          <button type="button" @click="removeItem(index)" class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">✖</button>
        </div>

        <button type="button" @click="addItem" class="bg-gray-300 hover:bg-gray-400 px-4 py-2 rounded shadow transition transform hover:scale-105 mb-4">+ Add Item</button>

        <!-- Amount Paid -->
        <div class="mb-4">
          <label class="block text-sm font-bold mb-1">Amount Paid</label>
          <input type="number" :value="amountPaid.toFixed(2)" class="border p-2 rounded w-full bg-gray-100" disabled />
        </div>

        <!-- Submit -->
        <div class="flex justify-end">
          <button @click="submitExpense" class="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-2 rounded shadow transition transform hover:scale-105">
            {{ editingExpense ? 'Update Expense' : 'Create Expense' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add Expense Item Modal -->
    <div v-if="showItemModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 animate-fadeInModal">
      <div class="bg-white rounded-lg p-6 w-full max-w-md relative shadow-xl transform transition-all scale-95 animate-scaleUp">
        <h2 class="text-xl font-bold mb-4">Add Expense Item</h2>
        <button @click="closeItemModal" class="absolute top-2 right-2 text-gray-600 hover:text-gray-800 transition transform hover:scale-110">✖</button>

        <div class="grid gap-4 mb-4">
          <input v-model="expenseItemForm.name" placeholder="Expense Item Name" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />

          <select v-model="expenseItemForm.account_subtype" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition">
            <option value="" disabled>Select Expense Type</option>
            <option v-for="acc in expenseSubtypes" :key="acc" :value="acc">{{ acc }}</option>
          </select>
        </div>

        <div class="flex justify-end">
          <button @click="submitExpenseItem" class="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-2 rounded shadow transition transform hover:scale-105">
            Save Item
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../api";
import * as XLSX from "xlsx";
import jsPDF from "jspdf";
import "jspdf-autotable";

export default {
  data() {
    return {
      expenses: [],
      searchQuery: "",
      showModal: false,
      editingExpense: false,
      expandedRows: [],
      expandedRowHeights: {},
      expenseForm: {
        id: null,
        description: "",
        payment_account_name: "",
        payment_account_id: null,
        expense_date: "",
        reference: "",
        items: [{ account_name: "", account_id: null, item_name: "", description: "", amount: 0 }],
      },
      cashBankAccounts: [],
      expenseAccounts: [],
      showItemModal: false,
      expenseItemForm: {
        name: "",
        account_subtype: "",
      },
      expenseSubtypes: [],
    };
  },
  computed: {
    grandTotal() {
      return this.expenses.reduce((sum, expense) => sum + (expense.total_amount || 0), 0);
    },
    amountPaid() {
      return this.expenseForm.items.reduce((total, item) => total + (item.amount || 0), 0);
    },
  },
  methods: {
    getAccountName(accountId) {
      const acc = this.expenseAccounts.find(a => a.id === accountId);
      return acc ? acc.name : "Unknown Account";
    },
    async fetchCashBankAccounts(search = "") {
      try {
        const res = await api.get("/accounts/cash-bank", { params: { search } });
        this.cashBankAccounts = res.data;
      } catch (err) {
        console.error("Error fetching cash/bank accounts:", err);
      }
    },
    async fetchExpenseAccounts(search = "") {
      try {
        const res = await api.get("/accounts/expense-account", { params: { search } });
        this.expenseAccounts = res.data;
      } catch (err) {
        console.error("Error fetching expense accounts:", err);
      }
    },
    async fetchExpenseSubtypes() {
      try {
        const res = await api.get("/accounts/");
        this.expenseSubtypes = [...new Set(res.data.filter(a => a.account_type === "EXPENSE").map(a => a.account_subtype))];
      } catch (err) {
        console.error("Error fetching expense subtypes:", err);
      }
    },
    addItem() {
      this.expenseForm.items.push({ account_name: "", account_id: null, item_name: "", description: "", amount: 0 });
    },
        // Close expense item modal
    closeItemModal() {
      this.expenseItemForm = { name: "", account_subtype: "" };
      this.showItemModal = false;
      // this.removeEscapeListener();
    },
    removeItem(index) {
      this.expenseForm.items.splice(index, 1);
    },
    validateExpense() {
      if (!this.expenseForm.description.trim()) {
        alert("Expense description is required.");
        return false;
      }
      if (!this.expenseForm.payment_account_id) {
        alert("Please select a valid payment account.");
        return false;
      }
      if (!this.expenseForm.expense_date) {
        alert("Expense date is required.");
        return false;
      }
      if (this.expenseForm.items.length === 0) {
        alert("At least one expense item is required.");
        return false;
      }
      for (const [i, item] of this.expenseForm.items.entries()) {
        if (!item.account_id) {
          alert(`Item ${i + 1}: Valid expense account is required.`);
          return false;
        }
        if (!item.item_name.trim()) {
          alert(`Item ${i + 1}: Item name is required.`);
          return false;
        }
        if (!item.amount || item.amount <= 0) {
          alert(`Item ${i + 1}: Amount must be greater than 0.`);
          return false;
        }
      }
      return true;
    },
    async submitExpense() {
      const paymentAcc = this.cashBankAccounts.find(a => a.name === this.expenseForm.payment_account_name);
      if (!paymentAcc) {
        alert("Please select a valid Cash/Bank account!");
        return;
      }
      this.expenseForm.payment_account_id = paymentAcc.id;
      for (const item of this.expenseForm.items) {
        const acc = this.expenseAccounts.find(a => a.name === item.account_name);
        if (!acc) {
          alert(`Invalid expense account for item "${item.item_name}"`);
          return;
        }
        item.account_id = acc.id;
      }
      if (!this.validateExpense()) return;

      try {
        if (this.editingExpense) {
          await api.put(`/expenses/${this.expenseForm.id}`, this.expenseForm);
          alert("✅ Expense updated successfully!");
        } else {
          await api.post("/expenses/", this.expenseForm);
          alert("✅ Expense created successfully!");
        }
        this.closeModal();
        this.fetchExpenses();
      } catch (err) {
        console.error("❌ Error submitting expense:", err);
        alert("Failed to submit expense. " + (err.response?.data?.error || err.message));
      }
    },
    async submitExpenseItem() {
  if (!this.expenseItemForm.name.trim() || !this.expenseItemForm.account_subtype) {
    alert("Expense Item Name and Type are required!");
    return;
  }

  try {
    const payload = {
      name: this.expenseItemForm.name.trim(),
      account_subtype: this.expenseItemForm.account_subtype
    };

    const res = await api.post("/accounts/expense-items", payload);
    alert(`✅ Expense Item "${this.expenseItemForm.name}" created successfully!`);

    // Refresh expense accounts list so the new item can be selected
    await this.fetchExpenseAccounts();

    // Close the modal and reset form
    this.closeItemModal();
  } catch (err) {
    console.error("❌ Error creating expense item:", err);
    alert("Failed to create expense item. " + (err.response?.data?.error || err.message));
  }
},

    editExpense(expense) {
      this.expenseForm = {
        id: expense.id,
        description: expense.description,
        payment_account_name: this.cashBankAccounts.find(a => a.id === expense.payment_account_id)?.name || "",
        payment_account_id: expense.payment_account_id,
        expense_date: expense.expense_date.split("T")[0],
        reference: expense.reference,
        items: expense.items.map(i => ({
          account_name: this.expenseAccounts.find(a => a.id === i.account_id)?.name || "",
          account_id: i.account_id,
          item_name: i.item_name,
          description: i.description,
          amount: i.amount
        })),
      };
      this.editingExpense = true;
      this.showModal = true;
    },
    closeModal() {
      this.resetForm();
      this.showModal = false;
    },
    resetForm() {
      this.expenseForm = {
        id: null,
        description: "",
        payment_account_name: "",
        payment_account_id: null,
        expense_date: "",
        reference: "",
        items: [{ account_name: "", account_id: null, item_name: "", description: "", amount: 0 }],
      };
      this.editingExpense = false;
    },
    async fetchExpenses() {
      try {
        const res = await api.get("/expenses/");
        this.expenses = res.data;
        this.$nextTick(() => this.updateExpandedHeights());
      } catch (err) {
        console.error("❌ Error fetching expenses:", err);
        alert("Failed to load expenses. Please try again.");
      }
    },
    async deleteExpense(id) {
      if (confirm("Are you sure you want to delete this expense?")) {
        try {
          await api.delete(`/expenses/${id}`);
          alert("🗑️ Expense deleted successfully!");
          this.fetchExpenses();
        } catch (err) {
          console.error("❌ Error deleting expense:", err);
          alert("Failed to delete expense. Please try again.");
        }
      }
    },
    async searchExpenses() {
      try {
        const res = await api.get("/expenses/");
        this.expenses = res.data.filter(
          e => e.description.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
               (e.reference && e.reference.toLowerCase().includes(this.searchQuery.toLowerCase()))
        );
        this.$nextTick(() => this.updateExpandedHeights());
      } catch (err) {
        console.error("❌ Error searching expenses:", err);
        alert("Search failed. Please try again.");
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return "";
      const d = new Date(dateStr);
      return d.toLocaleDateString();
    },
    toggleExpand(id, index) {
      const i = this.expandedRows.indexOf(id);
      if (i > -1) {
        this.expandedRows.splice(i, 1);
      } else {
        this.expandedRows.push(id);
      }
      this.$nextTick(() => this.updateExpandedHeights());
    },
    updateExpandedHeights() {
      if (!this.$refs.expandedRowsRefs) return;
      this.expenses.forEach((exp, idx) => {
        const el = this.$refs.expandedRowsRefs[idx];
        if (el) {
          this.expandedRowHeights[exp.id] = el.scrollHeight;
        }
      });
    },
    exportExcel() {
      try {
        const ws = XLSX.utils.json_to_sheet(this.expenses);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Expenses");
        XLSX.writeFile(wb, "expenses.xlsx");
      } catch (err) {
        console.error("❌ Error exporting Excel:", err);
        alert("Failed to export Excel.");
      }
    },
    exportPDF() {
      try {
        const doc = new jsPDF();
        doc.autoTable({
          head: [["ID", "Description", "Total Amount", "Reference", "Expense Date", "Transaction No"]],
          body: this.expenses.map(e => [
            e.id, e.description, e.total_amount, e.reference, this.formatDate(e.expense_date), e.transaction_no
          ])
        });
        doc.save("expenses.pdf");
      } catch (err) {
        console.error("❌ Error exporting PDF:", err);
        alert("Failed to export PDF.");
      }
    },
  },
  mounted() {
    this.fetchExpenses();
    this.fetchCashBankAccounts();
    this.fetchExpenseAccounts();
    this.fetchExpenseSubtypes();
  }
};
</script>

<style scoped>
@keyframes fadeInModal {
  0% { opacity: 0; }
  100% { opacity: 1; }
}
.animate-fadeInModal { animation: fadeInModal 0.3s ease-in-out forwards; }

@keyframes scaleUp {
  0% { transform: scale(0.95); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.animate-scaleUp { animation: scaleUp 0.3s ease-out forwards; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px);}
  to { opacity: 1; transform: translateY(0);}
}
.animate-fadeIn { animation: fadeIn 0.5s ease-in-out forwards; }
</style>
