<template>
    <div class="mb-10">
      <h2 class="text-xl font-semibold mb-4 text-gray-700">{{ title }}</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <ReportCard
          v-for="report in reports"
          :key="report.title"
          :title="report.title"
          :link="report.link"
          :description="report.description"
          :icon="report.icon"
        />
      </div>
    </div>
  </template>
  
  <script setup>
  import ReportCard from '@/components/ReportCard.vue'
  
  defineProps({
    title: { type: String, required: true },
    reports: { type: Array, required: true }
  })
  </script>
  