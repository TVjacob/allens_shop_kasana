<template>
  <div class="h-16 w-full bg-white shadow flex items-center justify-between px-6">
    <!-- Page Title -->
    <div class="font-bold text-lg">{{ pageTitle }}</div>

    <!-- User Info & Logout -->
    <div class="flex items-center gap-4">
      <!-- User Avatar Placeholder -->
      <div class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-700 font-bold">
        {{ userInitials }}
      </div>

      <!-- User Details -->
      <div class="flex flex-col text-right">
        <span class="font-semibold text-gray-800">{{ user.name }}</span>
        <span class="text-sm text-gray-500">{{ user.role }}</span>
      </div>

      <!-- Profile Button (optional) -->
      <button
        @click="goToProfile"
        class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
      >
        Profile
      </button>

      <!-- Logout Button -->
      <button
        @click="logout"
        class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
      >
        Logout
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../api';

export default {
  setup() {
    const route = useRoute();
    const router = useRouter();

    // --- Load user from localStorage ---
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    // --- Generate initials for placeholder avatar ---
    const userInitials = computed(() => {
      if (!user.name) return '';
      return user.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase();
    });

    // --- Dynamic page title ---
    const pageTitle = computed(() => {
      switch (route.path) {
        case '/': return 'Dashboard';
        case '/products': return 'Products';
        case '/customers': return 'Customers';
        case '/sales': return 'Sales';
        case '/supplier': return 'Supplier';
        case '/purchases': return 'Purchases';
        case '/reports': return 'Reports';
        case '/expenses': return 'Expenses';
        case '/users': return 'Users';
        case '/purchaselist': return 'Purchase List';
        case '/saleslist': return 'Sales List';
        case '/accounts': return 'Accounts';
        default: return '';
      }
    });

    // --- Logout function ---
    const logout = () => {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      if (api.defaults.headers.common['Authorization']) {
        delete api.defaults.headers.common['Authorization'];
      }
      router.push('/login');
    };

    // --- Go to profile page (optional) ---
    const goToProfile = () => {
      router.push('/profile');
    };

    return { user, userInitials, pageTitle, logout, goToProfile };
  },
};
</script>
