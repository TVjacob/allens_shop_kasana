<template>
    <tr :class="`text-${color}-600`">
      <td class="p-2 border-b" :style="{ paddingLeft: `${level * 20}px` }">
        {{ account.account_name }}
      </td>
      <td class="p-2 border-b text-right">{{ account.opening_balance.toLocaleString() }}</td>
      <td class="p-2 border-b text-right">{{ account.movement.toLocaleString() }}</td>
      <td class="p-2 border-b text-right">{{ account.closing_balance.toLocaleString() }}</td>
    </tr>
  
    <!-- Render children recursively -->
    <template v-for="child in account.children" :key="child.account_id">
      <CashFlowRow :account="child" :level="level + 1" :color="color" />
    </template>
  </template>
  
  <script setup>
  defineProps({
    account: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 0
    },
    color: {
      type: String,
      default: 'green' // 'green' for inflows, 'red' for outflows
    }
  });
  </script>
  
  <style scoped>
  /* Optional: subtle hover highlight for rows */
  tr:hover {
    background-color: rgba(0, 0, 0, 0.02);
  }
  </style>
  