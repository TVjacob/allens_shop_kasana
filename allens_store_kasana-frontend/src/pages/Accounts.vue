<template>
    <div class="p-6 max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6 text-gray-800 animate-fadeIn">Accounts Management</h1>
  
      <!-- Add Account Button -->
      <button
        @click="showModal = true"
        class="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded shadow transition transform hover:scale-105 mb-4"
      >
        + Add Account
      </button>
  
      <!-- Tabs -->
      <div class="flex gap-2 mb-4">
        <button :class="tab === 'list' ? 'bg-indigo-500 text-white' : 'bg-gray-200'" class="px-4 py-2 rounded" @click="tab='list'">Accounts List</button>
        <button :class="tab === 'chart' ? 'bg-indigo-500 text-white' : 'bg-gray-200'" class="px-4 py-2 rounded" @click="tab='chart'">Chart of Accounts</button>
      </div>
  
      <!-- Export button -->
      <div v-if="tab === 'list'" class="mb-2 flex justify-end">
        <button @click="exportToExcel" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded shadow">Export to Excel</button>
      </div>
  
      <!-- Accounts Table -->
      <div v-if="tab === 'list'" class="overflow-x-auto border rounded-lg shadow-lg mb-6">
        <table class="min-w-full border-collapse" id="accounts-table">
          <thead class="bg-gray-100">
            <tr>
              <th class="p-3 border-b text-left">ID</th>
              <th class="p-3 border-b text-left">Name</th>
              <th class="p-3 border-b text-left">Code</th>
              <th class="p-3 border-b text-left">Type</th>
              <th class="p-3 border-b text-left">Subtype</th>
              <th class="p-3 border-b text-left">Parent</th>
              <th class="p-3 border-b text-left">Status</th>
              <th class="p-3 border-b text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="acc in accounts" :key="acc.id" class="hover:bg-gray-50 transition transform hover:scale-[1.01]">
              <td class="p-3">{{ acc.id }}</td>
              <td class="p-3">{{ acc.name }}</td>
              <td class="p-3">{{ acc.code }}</td>
              <td class="p-3">{{ acc.account_type }}</td>
              <td class="p-3">{{ acc.account_subtype }}</td>
              <td class="p-3">{{ acc.parent_name || '-' }}</td>
              <td class="p-3">{{ acc.status === 1 ? 'Active' : acc.status === 9 ? 'Deleted' : 'Inactive' }}</td>
              <td class="p-3 text-center flex flex-wrap gap-1 justify-center">
                <button @click="editAccount(acc)" class="bg-blue-400 hover:bg-blue-500 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">Edit</button>
                <button @click="deleteAccount(acc.id)" class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded shadow transition transform hover:scale-105">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
  
      <!-- Chart of Accounts (collapsible) -->
      <div v-if="tab === 'chart'" class="mt-4">
        <div v-for="(types, type) in groupedAccounts" :key="type" class="mb-4">
          <h2 @click="toggleType(type)" class="cursor-pointer text-xl font-bold mb-2 flex items-center gap-2">
            <span>{{ type }}</span>
            <span>{{ collapsedTypes[type] ? '+' : '-' }}</span>
          </h2>
          <div v-show="!collapsedTypes[type]" class="ml-4">
            <div v-for="(subtypes, subtype) in types" :key="subtype" class="mb-2">
              <h3 @click="toggleSubtype(type, subtype)" class="cursor-pointer font-semibold mb-1 flex items-center gap-2">
                <span>{{ subtype }}</span>
                <span>{{ collapsedSubtypes[type]?.[subtype] ? '+' : '-' }}</span>
              </h3>
              <div v-show="!collapsedSubtypes[type]?.[subtype]" class="ml-4">
                <div v-for="(parents, parentName) in subtypes" :key="parentName" class="ml-4 mb-1">
                  <h4 @click="toggleParent(type, subtype, parentName)" class="italic cursor-pointer flex items-center gap-2">
                    <span>{{ parentName }}</span>
                    <span>{{ collapsedParents[type]?.[subtype]?.[parentName] ? '+' : '-' }}</span>
                  </h4>
                  <ul v-show="!collapsedParents[type]?.[subtype]?.[parentName]" class="ml-4 list-disc">
                    <li v-for="acc in parents" :key="acc.id">{{ acc.code }} - {{ acc.name }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
  
      <!-- Modal -->
      <div v-if="showModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 animate-fadeInModal">
        <div class="bg-white rounded-lg p-6 w-full max-w-2xl relative shadow-xl transform transition-all scale-95 animate-scaleUp">
          <h2 class="text-xl font-bold mb-4">{{ editingAccount ? 'Edit Account' : 'Add Account' }}</h2>
          <button @click="closeModal" class="absolute top-2 right-2 text-gray-600 hover:text-gray-800 transition transform hover:scale-110">✖</button>
          <div class="grid grid-cols-2 gap-4 mb-4">
            <input v-model="accountForm.name" placeholder="Account Name" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
            <input v-model="accountForm.code" placeholder="Account Code (optional)" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition" />
            <select v-model="accountForm.account_type" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition">
              <option value="" disabled>Select Account Type</option>
              <option v-for="type in accountTypes" :key="type" :value="type">{{ type }}</option>
            </select>
            <select v-model="accountForm.account_subtype" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition">
              <option value="" disabled>Select Account Subtype</option>
              <option v-for="subtype in subtypesForType(accountForm.account_type)" :key="subtype" :value="subtype">{{ subtype }}</option>
            </select>
            <select v-model="accountForm.parent_id" class="border p-2 rounded shadow-sm focus:ring-2 focus:ring-indigo-400 transition">
              <option value="">No Parent</option>
              <option v-for="acc in accounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
            </select>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-bold mb-1">Description</label>
            <textarea v-model="accountForm.description" placeholder="Description" class="border p-2 rounded shadow-sm w-full focus:ring-2 focus:ring-indigo-400 transition"></textarea>
          </div>
          <div class="flex justify-end">
            <button @click="submitAccount" class="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-2 rounded shadow transition transform hover:scale-105">{{ editingAccount ? 'Update Account' : 'Create Account' }}</button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import api from "../api";
  import * as XLSX from "xlsx";
  
  export default {
    data() {
      return {
        tab: "list",
        accounts: [],
        accountForm: { id: null, name: "", code: "", account_type: "", account_subtype: "", parent_id: null, description: "" },
        editingAccount: false,
        showModal: false,
        accountTypes: ["ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"],
        subtypes: {
          ASSET: ["Cash", "Bank", "Accounts Receivable", "Inventory", "Prepaid Expenses", "Fixed Asset"],
          LIABILITY: ["Accounts Payable", "Accrued Liabilities", "Long Term Debt"],
          EQUITY: ["Owner's Equity", "Retained Earnings"],
          REVENUE: ["Sales Revenue", "Service Revenue"],    
          EXPENSE: ["Cost of Goods Sold", "Rent Expense", "Salaries Expense", "Utilities Expense"]
        },
        searchQuery: "",
        collapsedTypes: {},
        collapsedSubtypes: {},
        collapsedParents: {}
      };
    },
    computed: {
      groupedAccounts() {
        const result = {};
        this.accounts.forEach(acc => {
          if (!result[acc.account_type]) result[acc.account_type] = {};
          const subtype = acc.account_subtype || "No Subtype";
          if (!result[acc.account_type][subtype]) result[acc.account_type][subtype] = {};
          const parentName = acc.parent_name || "No Parent";
          if (!result[acc.account_type][subtype][parentName]) result[acc.account_type][subtype][parentName] = [];
          result[acc.account_type][subtype][parentName].push(acc);
        });
        return result;
      }
    },
    methods: {
      toggleType(type) {
        this.$set(this.collapsedTypes, type, !this.collapsedTypes[type]);
      },
      toggleSubtype(type, subtype) {
        if (!this.collapsedSubtypes[type]) this.$set(this.collapsedSubtypes, type, {});
        this.$set(this.collapsedSubtypes[type], subtype, !this.collapsedSubtypes[type][subtype]);
      },
      toggleParent(type, subtype, parent) {
        if (!this.collapsedParents[type]) this.$set(this.collapsedParents, type, {});
        if (!this.collapsedParents[type][subtype]) this.$set(this.collapsedParents[type], subtype, {});
        this.$set(this.collapsedParents[type][subtype], parent, !this.collapsedParents[type][subtype][parent]);
      },
      subtypesForType(type) { return this.subtypes[type] || []; },
      async fetchAccounts() {
        try {
          const res = await api.get("/accounts/");
          this.accounts = res.data;
        } catch (err) { console.error(err); }
      },
      editAccount(acc) { this.accountForm = { ...acc }; this.editingAccount = true; this.showModal = true; },
      async submitAccount() {
        try {
          if (this.editingAccount) await api.put(`/accounts/${this.accountForm.id}`, this.accountForm);
          else await api.post("/accounts/", this.accountForm);
          this.closeModal();
          this.fetchAccounts();
        } catch (err) { console.error(err); alert("Failed to submit account."); }
      },
      async deleteAccount(id) { 
        if(confirm("Are you sure?")) { 
          try { await api.delete(`/accounts/${id}`); this.fetchAccounts(); } 
          catch(err){ console.error(err); alert("Failed to delete account."); }
        }
      },
      closeModal() { this.accountForm={id:null,name:"",code:"",account_type:"",account_subtype:"",parent_id:null,description:""}; this.editingAccount=false; this.showModal=false; },
      exportToExcel() {
        const ws = XLSX.utils.json_to_sheet(this.accounts);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Accounts");
        XLSX.writeFile(wb, "accounts.xlsx");
      }
    },
    mounted() { this.fetchAccounts(); }
  };
  </script>
  