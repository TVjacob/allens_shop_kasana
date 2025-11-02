<template>
  <header class="h-16 w-full bg-white/90 backdrop-blur-md shadow-lg flex items-center justify-between px-6 z-20 sticky top-0">
    <!-- Page Title -->
    <div class="font-bold text-lg text-gray-800">{{ pageTitle }}</div>

    <!-- User Info & Actions -->
    <div class="flex items-center gap-4">
      <!-- User Avatar -->
      <div
        class="w-10 h-10 rounded-full bg-indigo-500 text-white flex items-center justify-center font-semibold text-sm shadow-md"
      >
        {{ userInitials }}
      </div>

      <!-- User Details -->
      <div class="flex flex-col text-right">
        <span class="font-semibold text-gray-800">{{ user.name }}</span>
        <span class="text-sm text-gray-500">{{ user.role }}</span>
      </div>

      <!-- Profile Button -->
      <button
        @click="goToProfile"
        class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-sm transition"
      >
        Profile
      </button>

      <!-- Logout Button -->
      <button
        @click="logout"
        class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm transition"
      >
        Logout
      </button>
    </div>
  </header>
</template>

<script>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api';

export default {
  setup() {
    const route = useRoute();
    const router = useRouter();

    const user = JSON.parse(localStorage.getItem('user') || '{}');

    const userInitials = computed(() => {
      if (!user.name) return '';
      return user.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase();
    });

    const pageTitle = computed(() => {
      const titles = {
        '/': 'Dashboard',
        '/products': 'Products',
        '/customers': 'Customers',
        '/sales': 'Sales',
        '/supplier': 'Supplier',
        '/purchases': 'Purchases',
        '/reports': 'Reports',
        '/customereturns': 'Customer Returns',
        '/enter_returnables': 'Enter Returnables',
        '/expenses': 'Expenses',
        '/users': 'Users',
        '/purchaselist': 'Purchase List',
        '/saleslist': 'Sales List',
        '/accounts': 'Accounts',
      };
      return titles[route.path] || '';
    });

    const logout = () => {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      if (api.defaults.headers.common['Authorization']) {
        delete api.defaults.headers.common['Authorization'];
      }
      router.push('/login');
    };

    const goToProfile = () => {
      router.push('/profile');
    };

    return { user, userInitials, pageTitle, logout, goToProfile };
  },
};
</script>

<style scoped>
header {
  /* Optional subtle shadow for depth */
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}
button {
  transition: all 0.2s ease-in-out;
}
button:hover {
  transform: translateY(-1px);
}
</style>
