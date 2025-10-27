<template>
    <tr>
      <td class="p-2 border-b text-center">{{ counter.next() }}</td>
      <td class="p-2 border-b" :style="{ paddingLeft: level * 20 + 'px' }">{{ account.name }}</td>
      <td class="p-2 border-b">{{ account.code }}</td>
      <td class="p-2 border-b">{{ account.account_subtype || '-' }}</td>
    </tr>
    <!-- Recursive children -->
    <AccountRow
      v-for="child in account.children"
      :key="child.id"
      :account="child"
      :level="level + 1"
      :counter="counter"
    />
  </template>
  
  <script setup>
  import { defineProps } from 'vue';
  
  const props = defineProps({
    account: { type: Object, required: true },
    level: { type: Number, default: 0 },
    counter: { type: Object, required: true }
  });
  </script>
  
  <style scoped>
  </style>
  