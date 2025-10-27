<template>
    <div class="p-6 max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6 text-gray-800">Balance Sheet</h1>
  
      <!-- Toolbar -->
      <div class="flex flex-wrap items-center gap-3 mb-6">
        <button
          @click="$router.push('/reports')"
          class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Back to Reports
        </button>
  
        <div class="flex items-center gap-2">
          <label for="as_of" class="text-sm font-medium text-gray-700">As of:</label>
          <input
            id="as_of"
            type="date"
            v-model="asOf"
            @change="fetchReport"
            class="border border-gray-300 rounded p-2 focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400"
          />
        </div>
  
        <button
          @click="exportPDF"
          class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          Export PDF
        </button>
      </div>
  
      <!-- Summary Info -->
      <div class="mb-4 text-gray-700">
        <div><strong>Date:</strong> {{ report.as_of }}</div>
        <div>
          <strong>Balanced:</strong>
          <span :class="report.summary?.is_balanced ? 'text-green-600' : 'text-red-600'">
            {{ report.summary?.is_balanced ? 'Yes' : 'No' }}
          </span>
        </div>
      </div>
  
      <!-- Balance Sheet Layout -->
      <div id="balance-sheet-content" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- ASSETS -->
        <div class="bg-white rounded-lg shadow p-4 border">
          <h2 class="text-xl font-semibold mb-3 text-indigo-700">Assets</h2>
  
          <div
            v-for="(accounts, subtype) in report.sections?.ASSET"
            :key="subtype"
            class="mb-4"
          >
            <h3 class="font-semibold text-gray-700 mb-1">{{ subtype }}</h3>
            <table class="w-full text-sm border-t">
              <tbody>
                <tr
                  v-for="account in accounts"
                  :key="account.account_id"
                  class="border-b"
                >
                  <td class="py-1">{{ account.account_name }}</td>
                  <td class="py-1 text-right font-medium">
                    {{ formatCurrency(account.balance) }}
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="text-right font-semibold mt-1">
              Subtotal: {{ formatCurrency(report.totals?.ASSET?.subtotals?.[subtype]) }}
            </div>
          </div>
  
          <div class="text-right font-bold text-indigo-700 border-t pt-2">
            Total Assets: {{ formatCurrency(report.summary?.total_assets) }}
          </div>
        </div>
  
        <!-- LIABILITIES & EQUITY -->
        <div class="bg-white rounded-lg shadow p-4 border">
          <h2 class="text-xl font-semibold mb-3 text-indigo-700">Liabilities & Equity</h2>
  
          <!-- Liabilities -->
          <div v-if="report.sections?.LIABILITY" class="mb-6">
            <h3 class="font-semibold text-gray-700 mb-1">Liabilities</h3>
            <div
              v-for="(accounts, subtype) in report.sections.LIABILITY"
              :key="subtype"
              class="mb-4"
            >
              <table class="w-full text-sm border-t">
                <tbody>
                  <tr
                    v-for="account in accounts"
                    :key="account.account_id"
                    class="border-b"
                  >
                    <td class="py-1">{{ account.account_name }}</td>
                    <td class="py-1 text-right font-medium">
                      {{ formatCurrency(account.balance) }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div class="text-right font-semibold mt-1">
                Subtotal: {{ formatCurrency(report.totals?.LIABILITY?.subtotals?.[subtype]) }}
              </div>
            </div>
          </div>
  
          <!-- Equity -->
          <div v-if="report.sections?.EQUITY">
            <h3 class="font-semibold text-gray-700 mb-1">Equity</h3>
            <div
              v-for="(accounts, subtype) in report.sections.EQUITY"
              :key="subtype"
              class="mb-4"
            >
              <table class="w-full text-sm border-t">
                <tbody>
                  <tr
                    v-for="account in accounts"
                    :key="account.account_id"
                    class="border-b"
                  >
                    <td class="py-1">{{ account.account_name }}</td>
                    <td class="py-1 text-right font-medium">
                      {{ formatCurrency(account.balance) }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div class="text-right font-semibold mt-1">
                Subtotal: {{ formatCurrency(report.totals?.EQUITY?.subtotals?.[subtype]) }}
              </div>
            </div>
          </div>
  
          <div class="text-right font-bold text-indigo-700 border-t pt-2">
            Total Liabilities + Equity:
            {{ formatCurrency(report.summary?.total_liabilities_equity) }}
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from "vue";
  import api from "@/api";
  import html2pdf from "html2pdf.js";
  
  const asOf = ref(new Date().toISOString().slice(0, 10)); // default today
  const report = ref({});
  
  const fetchReport = async () => {
    try {
      const res = await api.get(`/reports/balance-sheet?as_of=${asOf.value}`);
      report.value = res.data;
    } catch (err) {
      console.error("Error fetching balance sheet:", err);
    }
  };
  
  const formatCurrency = (value) => {
    if (value == null) return "0";
    return value.toLocaleString("en-UG", {
      style: "currency",
      currency: "UGX",
      minimumFractionDigits: 0,
    });
  };
  
  const exportPDF = () => {
    const element = document.getElementById("balance-sheet-content");
    const opt = {
      margin: 0.3,
      filename: `Balance_Sheet_${asOf.value}.pdf`,
      image: { type: "jpeg", quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: "in", format: "a4", orientation: "portrait" },
    };
    html2pdf().set(opt).from(element).save();
  };
  
  onMounted(fetchReport);
  </script>
  
  <style scoped>
  table {
    border-collapse: collapse;
  }
  th,
  td {
    text-align: left;
  }
  td:last-child {
    text-align: right;
  }
  </style>
  