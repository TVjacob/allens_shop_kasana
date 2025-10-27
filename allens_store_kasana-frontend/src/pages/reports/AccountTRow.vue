<template>
    <tr>
      <td :style="{ paddingLeft: `${depth * 20}px` }" class="p-2 border-b">
        {{ account.account_name }}
      </td>
      <td class="p-2 border-b text-right text-green-700">
        {{ formatCurrency(account.opening_debit) }}
      </td>
      <td class="p-2 border-b text-right text-red-700">
        {{ formatCurrency(account.opening_credit) }}
      </td>
      <td class="p-2 border-b text-right text-green-700">
        {{ formatCurrency(account.movement_debit) }}
      </td>
      <td class="p-2 border-b text-right text-red-700">
        {{ formatCurrency(account.movement_credit) }}
      </td>
      <td class="p-2 border-b text-right font-semibold">
        {{ formatCurrency(account.closing_balance) }}
      </td>
    </tr>
  
    <!-- Render children recursively -->
    <AccountRow
      v-for="child in account.children"
      :key="child.account_id"
      :account="child"
      :depth="depth + 1"
    />
  </template>
  
  <script setup>
  import { defineProps } from "vue";
  
  const props = defineProps({
    account: Object,
    depth: { type: Number, default: 0 },
  });
  
  const formatCurrency = (val) =>
    val ? val.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "-";
  </script>
  