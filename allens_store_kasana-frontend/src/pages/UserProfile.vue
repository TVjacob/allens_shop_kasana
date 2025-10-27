<template>
    <div class="h-16 w-full bg-white shadow flex items-center justify-between px-6">
      <!-- Page Title -->
      <div class="font-bold text-lg">{{ pageTitle }}</div>
  
      <!-- User Profile Card -->
      <div class="relative" @click="toggleDropdown">
        <div class="flex items-center gap-3 cursor-pointer">
          <!-- Profile Picture Placeholder -->
          <div class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold">
            {{ userInitials }}
          </div>
  
          <!-- User Info -->
          <div class="hidden md:flex flex-col text-right">
            <span class="font-semibold">{{ user.username }}</span>
            <span class="text-sm text-gray-500">{{ user.role }}</span>
          </div>
  
          <!-- Dropdown Arrow -->
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
  
        <!-- Dropdown Menu -->
        <div v-if="dropdownOpen" class="absolute right-0 mt-2 w-48 bg-white shadow-lg rounded border border-gray-200 z-50">
          <button @click="logout" class="w-full text-left px-4 py-2 hover:bg-gray-100">Logout</button>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, computed, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import api from '../api';
  
  export default {
    setup() {
      const router = useRouter();
      const dropdownOpen = ref(false);
      const user = ref({ username: 'Loading...', role: 'Staff' });
  
      // Get user from localStorage (or API)
      onMounted(() => {
        const storedUser = JSON.parse(localStorage.getItem('user')) || {};
        user.value.username = storedUser.username || 'Guest';
        user.value.role = storedUser.role || 'Staff';
      });
  
      const toggleDropdown = () => {
        dropdownOpen.value = !dropdownOpen.value;
      };
  
      const logout = () => {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        if (api.defaults.headers.common['Authorization']) {
          delete api.defaults.headers.common['Authorization'];
        }
        router.push('/login');
      };
  
      // Get user initials for profile placeholder
      const userInitials = computed(() => {
        return user.value.username
          .split(' ')
          .map(n => n[0])
          .join('')
          .toUpperCase();
      });
  
      return { user, dropdownOpen, toggleDropdown, logout, userInitials };
    },
    props: {
      pageTitle: {
        type: String,
        default: 'Dashboard'
      }
    }
  };
  </script>
  
  <style scoped>
  /* Optional: Smooth dropdown animation */
  </style>
  