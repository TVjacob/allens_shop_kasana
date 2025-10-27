<template>
    <template v-for="child in children" :key="child.id">
      <tr v-show="!child.hidden">
        <td class="p-2 border-b">
          <button
            v-if="child.children.length"
            @click="$emit('toggle', child)"
            class="mr-2"
          >
            {{ child.expanded ? '▼' : '▶' }}
          </button>
          <span :style="{ paddingLeft: child.level * 20 + 'px' }">{{ child.name }}</span>
        </td>
        <td class="p-2 border-b text-right">{{ child.balance.toLocaleString() }}</td>
      </tr>
      <AccountChildren
        v-if="child.children.length"
        :children="child.children"
        @toggle="$emit('toggle', $event)"
      />
    </template>
  </template>
  
  <script setup>
  defineProps({
    children: {
      type: Array,
      required: true
    }
  });
  </script>
  
  <style scoped>
  button {
    background: transparent;
    border: none;
    cursor: pointer;
    font-weight: bold;
  }
  </style>
  