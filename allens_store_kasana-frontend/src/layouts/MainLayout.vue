<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main content -->
    <div class="flex-1 flex flex-col bg-gray-100 overflow-auto">
      <Navbar />

      <!-- Optional greeting -->
      <div v-if="$route.meta.showGreeting" class="p-4 bg-blue-100 text-blue-800 font-semibold">
        Hello! Welcome to {{ $route.meta.pageName }} page.
      </div>

      <!-- Child pages render here -->
      <main class="flex-1 p-6">
        <router-view /> <!-- Purchases.vue renders here -->
      </main>
    </div>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue';
import Navbar from '../components/Navbar.vue';

export default {
  components: { Sidebar, Navbar },
};
</script>
