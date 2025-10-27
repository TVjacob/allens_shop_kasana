<template>
    <div class="p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold">Expense Report</h2>
        <div class="flex gap-2">
            <button
                @click="goBack"
                class="bg-gray-300 text-black px-4 py-2 rounded no-print"
                >
                Back
                </button>
                <button
                @click="printReport"
                class="bg-indigo-500 text-white px-4 py-2 rounded no-print"
                >
                Print
                </button>

        </div>
      </div>
  
      <div v-if="loading" class="text-gray-500">Loading...</div>
      <div v-else id="report-content">
        <!-- Header Info -->
        <div class="mb-4 p-4 bg-gray-100 rounded shadow">
          <p><strong>Description:</strong> {{ expense.description }}</p>
          <p><strong>Reference:</strong> {{ expense.reference }}</p>
          <p><strong>Expense Date:</strong> {{ expense.expense_date }}</p>
          <p><strong>Total Amount:</strong> {{ formatCurrency(expense.total_amount) }}</p>
          <p><strong>Payment Account:</strong> {{ expense.payment_account.name }}</p>
        </div>
  
        <!-- Expense Items Table -->
        <table class="min-w-full border text-sm">
          <thead>
            <tr class="bg-gray-200">
              <th class="p-2 border">Account</th>
              <th class="p-2 border">Item Name</th>
              <th class="p-2 border">Description</th>
              <th class="p-2 border">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in expense.items" :key="item.item_id">
              <td class="p-2 border">{{ item.account.name }}</td>
              <td class="p-2 border">{{ item.item_name }}</td>
              <td class="p-2 border">{{ item.description }}</td>
              <td class="p-2 border">{{ formatCurrency(item.amount) }}</td>
            </tr>
          </tbody>
        </table>
  
        <!-- Export Button -->
        <div class="mt-4 flex justify-end gap-2">
          <button
            @click="exportExcel"
            class="bg-yellow-500 text-white px-4 py-2 rounded"
          >
            Export Excel
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted } from "vue";
  import { useRoute, useRouter } from "vue-router";
  import api from "@/api";
  import * as XLSX from "xlsx";
  
  export default {
    name: "ExpenseReport",
    setup() {
      const route = useRoute();
      const router = useRouter();
      const expense = ref(null);
      const loading = ref(true);
  
      const fetchExpense = async () => {
        try {
          const res = await api.get(`/expenses/expense/${route.params.id}`);
          expense.value = res.data;
        } catch (err) {
          console.error("Error fetching expense:", err);
        } finally {
          loading.value = false;
        }
      };
  
      const formatCurrency = (value) => {
        if (value == null) return "UGX 0";
        return new Intl.NumberFormat("en-UG", {
          style: "currency",
          currency: "UGX",
          currencyDisplay: "code",
          minimumFractionDigits: 0,
        }).format(value);
      };
  
      const exportExcel = () => {
        if (!expense.value) return;
  
        const data = expense.value.items.map((item) => ({
          Account: item.account.name,
          "Item Name": item.item_name,
          Description: item.description,
          Amount: item.amount,
        }));
  
        // Add header row
        data.unshift({
          Account: "Header",
          "Item Name": "Description",
          Description: expense.value.description,
          Amount: expense.value.total_amount,
        });
  
        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Expense Report");
        XLSX.writeFile(wb, `expense_${expense.value.expense_id}.xlsx`);
      };
  
      const goBack = () => {
        router.push("/expenses");
      };
  
    //   const printReport = () => {
    //     const originalContent = document.body.innerHTML;
    //     const reportContent = document.getElementById("report-content").innerHTML;
    //     document.body.innerHTML = reportContent;
    //     window.print();
    //     document.body.innerHTML = originalContent;
    //     window.location.reload(); // reload to restore Vue bindings
    //   };
//     const printReport = () => {
//   if (!expense.value) return;

//   // Pre-format the amounts
//   const totalAmount = new Intl.NumberFormat("en-UG", {
//     style: "currency",
//     currency: "UGX",
//     currencyDisplay: "code",
//     minimumFractionDigits: 0,
//   }).format(expense.value.total_amount);

//   const itemsHtml = expense.value.items
//     .map(item => {
//       const amount = new Intl.NumberFormat("en-UG", {
//         style: "currency",
//         currency: "UGX",
//         currencyDisplay: "code",
//         minimumFractionDigits: 0,
//       }).format(item.amount);

//       return `
//         <tr>
//           <td>${item.account.name}</td>
//           <td>${item.item_name}</td>
//           <td>${item.description}</td>
//           <td>${amount}</td>
//         </tr>
//       `;
//     })
//     .join("");

//   const html = `
//     <html>
//       <head>
//         <title>Expense Report</title>
//         <style>
//           body { font-family: Arial, sans-serif; padding: 20px; }
//           h2 { margin-bottom: 20px; }
//           table { border-collapse: collapse; width: 100%; margin-top: 10px; }
//           th, td { border: 1px solid #000; padding: 8px; text-align: left; }
//           th { background-color: #f0f0f0; }
//           .header-info p { margin: 4px 0; }
//         </style>
//       </head>
//       <body>
//         <h2>Expense Report</h2>
//         <div class="header-info">
//           <p><strong>Description:</strong> ${expense.value.description}</p>
//           <p><strong>Reference:</strong> ${expense.value.reference}</p>
//           <p><strong>Expense Date:</strong> ${expense.value.expense_date}</p>
//           <p><strong>Total Amount:</strong> ${totalAmount}</p>
//           <p><strong>Payment Account:</strong> ${expense.value.payment_account.name}</p>
//         </div>
//         <table>
//           <thead>
//             <tr>
//               <th>Account</th>
//               <th>Item Name</th>
//               <th>Description</th>
//               <th>Amount</th>
//             </tr>
//           </thead>
//           <tbody>
//             ${itemsHtml}
//           </tbody>
//         </table>
//       </body>
//     </html>
//   `;

//   const printWindow = window.open("", "_blank", "width=800,height=600");
//   printWindow.document.write(html);
//   printWindow.document.close();
//   printWindow.focus();
//   printWindow.print();
//   printWindow.close();
// };


const printReport = () => {
    window.print();
  };
  
      onMounted(fetchExpense);
  
      return { expense, loading, formatCurrency, exportExcel, goBack, printReport };
    },
  };
  </script>
  
  <style scoped>
@media print {
  body * {
    visibility: hidden !important;
  }
  #report-content,
  #report-content * {
    visibility: visible !important;
  }
  #report-content {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
  }
  /* Hide buttons */
  .no-print {
    display: none !important;
  }
}

  </style>
  