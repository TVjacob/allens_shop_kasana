<template>
  <router-link
    :to="link"
    class="report-card flex flex-col items-start p-6 bg-white rounded-xl shadow-md hover:shadow-xl transform hover:scale-105 transition-all duration-300 ease-in-out w-full"
  >
    <!-- Optional Icon -->
    <div v-if="icon" class="text-3xl mb-4 text-indigo-600">
      {{ icon }}
    </div>

    <!-- Report Title -->
    <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ title }}</h3>

    <!-- Description / Placeholder -->
    <p v-if="description" class="text-sm text-gray-500">{{ description }}</p>
  </router-link>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  link: { type: String, required: true },
  description: { type: String, default: "" },
  icon: { type: String, default: "" } // Can pass emoji or SVG icon
});
</script>

<style scoped>
.report-card {
  cursor: pointer;
  background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
}

.report-card:hover {
  /* Lift and slight color change */
  background: linear-gradient(180deg, #f3f4f6 0%, #ffffff 100%);
}

h3 {
  letter-spacing: 0.5px;
}
</style>
