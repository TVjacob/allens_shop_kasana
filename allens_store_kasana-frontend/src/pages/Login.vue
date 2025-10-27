<template>
  <div class="relative flex items-center justify-center min-h-screen overflow-hidden">
    <!-- 🔮 Animated Gradient Background -->
    <div class="absolute inset-0 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 animate-gradient"></div>

    <!-- ✨ Floating geometric shapes -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>

    <!-- 💎 Login Card -->
    <div class="relative bg-white/90 backdrop-blur-md p-8 rounded-2xl shadow-2xl w-full max-w-md z-10">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-extrabold text-indigo-700 drop-shadow-sm">Allen's Shop</h1>
        <p class="text-gray-600 text-sm">Kasana Branch Login</p>
      </div>

      <form @submit.prevent="loginUser" class="space-y-5">
        <div>
          <label class="block mb-1 font-medium text-gray-700">Username</label>
          <input
            type="text"
            v-model="username"
            placeholder="Enter your username"
            class="w-full border border-gray-300 px-4 py-2.5 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
            required
          />
        </div>

        <div>
          <label class="block mb-1 font-medium text-gray-700">Password</label>
          <input
            type="password"
            v-model="password"
            placeholder="Enter your password"
            class="w-full border border-gray-300 px-4 py-2.5 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
            required
          />
        </div>

        <transition name="fade">
          <div
            v-if="error"
            class="text-red-600 text-sm bg-red-50 border border-red-200 p-2 rounded-md text-center"
          >
            {{ error }}
          </div>
        </transition>

        <button
          type="submit"
          class="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-semibold hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-400 transition"
        >
          Login
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-gray-500">
        © {{ new Date().getFullYear() }} Allen's Shop — All rights reserved.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../api";

const username = ref("");
const password = ref("");
const error = ref("");
const router = useRouter();

const loginUser = async () => {
  error.value = "";
  try {
    const res = await api.post("/users/login", {
      username: username.value,
      password: password.value,
    });

    const { user, token } = res.data;
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", token);
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;

    router.push("/dashboard");
  } catch (err) {
    if (err.response && err.response.data.error) {
      error.value = err.response.data.error;
    } else {
      error.value = "Login failed. Please try again.";
    }
  }
};
</script>

<style scoped>
/* 🌀 Gradient background animation */
@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}
.animate-gradient {
  background-size: 200% 200%;
  animation: gradientShift 10s ease infinite;
}

/* ✨ Floating shapes styling */
.floating-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.25;
  filter: blur(40px);
  animation: float 10s ease-in-out infinite;
}
.shape-1 {
  width: 250px;
  height: 250px;
  background: #6366f1;
  top: 10%;
  left: -10%;
  animation-delay: 0s;
}
.shape-2 {
  width: 200px;
  height: 200px;
  background: #ec4899;
  bottom: 10%;
  right: -10%;
  animation-delay: 2s;
}
.shape-3 {
  width: 150px;
  height: 150px;
  background: #8b5cf6;
  top: 60%;
  left: 50%;
  animation-delay: 4s;
}
@keyframes float {
  0%, 100% {
    transform: translateY(0px) scale(1);
  }
  50% {
    transform: translateY(-30px) scale(1.05);
  }
}

/* ⚡ Fade transition for error message */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
