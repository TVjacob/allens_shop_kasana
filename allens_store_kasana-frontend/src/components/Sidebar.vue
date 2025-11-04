<template>
  <div class="relative min-h-screen flex">
    <!-- Background -->
    <div class="absolute inset-0 bg-animated-gradient overflow-hidden z-0">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>

    <!-- Sidebar -->
    <aside
      :class="[
        'bg-gray-900 text-white flex flex-col transition-all duration-300 ease-in-out z-10 shadow-lg',
        collapsed ? 'w-20' : 'w-64',
        isMobile ? (collapsed ? '-translate-x-full fixed z-40 h-full' : 'translate-x-0 fixed z-40 h-full') : 'static'
      ]"
    >
      <!-- Logo -->
      <div class="p-6 font-bold text-xl border-b border-gray-700 flex justify-between items-center text-indigo-400">
        <span v-if="!collapsed" class="text-2xl">Allen's Store</span>
        <button @click="toggleSidebar" class="focus:outline-none hover:text-indigo-300 transition">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      <!-- Menu -->
      <nav class="flex-1 mt-4 overflow-y-auto">
        <ul>
          <li v-for="item in filteredMenuItems" :key="item.name">
            <router-link
              :to="item.path"
              class="flex items-center px-6 py-3 rounded-lg gap-3 transition-all duration-200"
              :class="isActive(item.path) 
                        ? 'bg-indigo-600 text-white shadow-lg' 
                        : 'text-gray-200 hover:bg-indigo-500/30 hover:text-white'"
              @click="isMobile ? toggleSidebar() : null"
            >
              <span class="text-xl">{{ item.icon }}</span>
              <span v-if="!collapsed" class="whitespace-nowrap font-medium">{{ item.name }}</span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- Logout -->
      <div class="p-6 border-t border-gray-700">
        <button
          @click="logout"
          class="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition"
        >
          Logout
        </button>
      </div>
    </aside>

    <!-- Main content slot -->
    <div class="flex-1 z-10 relative">
      <slot></slot>
    </div>
  </div>
</template>

<script>
import { useRoute, useRouter } from 'vue-router';
import api from '../api';

export default {
  props: {
    collapsed: Boolean,
    isMobile: Boolean,
    toggleSidebar: Function
  },
  setup(props) {
    const route = useRoute();
    const router = useRouter();

    const isActive = (path) => route.path === path;

    const logout = () => {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      if (api.defaults.headers.common['Authorization']) {
        delete api.defaults.headers.common['Authorization'];
      }
      router.push('/login');
    };

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const permissions = user.permissions || [];

    const menuItems = [
      { name: 'Dashboard', path: '/', icon: '🏠', permission: null },
      { name: 'Accounts', path: '/accounts', icon: '🏦', permission: 'view_ledger' },
      { name: 'Products', path: '/products', icon: '📦', permission: 'view_inventory' },
      { name: 'Customers', path: '/customers', icon: '👥', permission: 'view_customers' },
      { name: 'Enter Sales', path: '/sales', icon: '💰', permission: 'create_invoice' },
      { name: 'Sales List', path: '/saleslist', icon: '📃', permission: 'view_invoices' },
      // { name: 'Sales List', path: '/saleslist', icon: '📃', permission: 'view_invoices' },
      { name: 'Customer Returns', path: '/customereturns', icon: '↩️', permission: 'view_invoices' },
      {name: 'Enter Returnables', path: '/enter_returnables', icon: '🍾', permission: 'view_invoices' },
      { name: 'Supplier', path: '/supplier', icon: '🚚', permission: 'view_suppliers' },
      { name: 'Enter Purchases', path: '/purchases', icon: '🛒', permission: 'create_purchase' },
      { name: 'Purchase List', path: '/purchaselist', icon: '📋', permission: 'view_purchases' },
      { name: 'Expenses', path: '/expenses', icon: '💸', permission: 'view_expense' },
      { name: 'Reports', path: '/reports', icon: '📊', permission: 'view_reports' },
      { name: 'Users', path: '/users', icon: '👤', permission: 'view_users' },
      {name:'Old Debts ' ,path:'/customermanagement',icon :'💵', permissions:'view_customers'},
    ];

    const filteredMenuItems = menuItems.filter(item => !item.permission || permissions.includes(item.permission));

    return { filteredMenuItems, isActive, logout };
  },
};
</script>

<style scoped>
/* Animated Gradient */
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.bg-animated-gradient {
  background: linear-gradient(135deg, #4f46e5, #ec4899, #8b5cf6);
  background-size: 200% 200%;
  animation: gradientShift 12s ease infinite;
}

/* Floating shapes / orbs */
.floating-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.25;
  filter: blur(50px);
  animation: float 12s ease-in-out infinite;
}
.shape-1 {
  width: 350px;
  height: 350px;
  background: #6366f1;
  top: 5%;
  left: -15%;
  animation-delay: 0s;
}
.shape-2 {
  width: 250px;
  height: 250px;
  background: #ec4899;
  bottom: 5%;
  right: -15%;
  animation-delay: 3s;
}
.shape-3 {
  width: 180px;
  height: 180px;
  background: #8b5cf6;
  top: 60%;
  left: 50%;
  animation-delay: 6s;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-25px) scale(1.05); }
}
</style>
