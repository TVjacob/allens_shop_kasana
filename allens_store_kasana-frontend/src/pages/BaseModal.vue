<template>
    <transition name="fade">
      <div
        v-if="localShow"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      >
        <div
          class="bg-white rounded-lg shadow-lg max-w-lg w-full overflow-hidden"
          @click.stop
        >
          <!-- Modal Header -->
          <div class="px-6 py-4 border-b flex justify-between items-center">
            <h2 class="text-lg font-semibold">{{ title }}</h2>
            <button
              class="text-gray-500 hover:text-gray-700"
              @click="close"
            >
              ✕
            </button>
          </div>
  
          <!-- Modal Body -->
          <div class="p-6">
            <slot />
          </div>
  
          <!-- Optional Footer Slot -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </transition>
  </template>
  
  <script setup>
  import { ref, watch } from 'vue';
  
  defineProps({
    modelValue: { type: Boolean, default: false },
    title: { type: String, default: 'Modal' }
  });
  
  const emit = defineEmits(['update:modelValue']);
  
  // Local reactive state
  const localShow = ref(false);
  
  // Sync local state with external modelValue
  watch(
    () => modelValue,
    (val) => {
      localShow.value = val;
    },
    { immediate: true }
  );
  
  // Emit changes when localShow changes
  watch(localShow, (val) => {
    emit('update:modelValue', val);
  });
  
  // Close helper
  const close = () => {
    localShow.value = false;
  };
  </script>
  
  <style>
  /* Simple fade transition */
  .fade-enter-active, .fade-leave-active {
    transition: opacity 0.2s ease;
  }
  .fade-enter-from, .fade-leave-to {
    opacity: 0;
  }
  </style>
  