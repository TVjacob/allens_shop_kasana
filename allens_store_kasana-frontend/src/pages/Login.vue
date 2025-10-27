<template>
    <div class="flex items-center justify-center h-screen bg-gray-100">
      <div class="bg-white p-8 rounded shadow-md w-96">
        <h2 class="text-2xl font-bold mb-6 text-center">Allen's Shop  ||  Kasana Branch  Login</h2>
        <form @submit.prevent="loginUser">
          <div class="mb-4">
            <label class="block mb-1 font-medium">Username</label>
            <input
              type="text"
              v-model="username"
              class="w-full border px-3 py-2 rounded"
              required
            />
          </div>
          <div class="mb-4">
            <label class="block mb-1 font-medium">Password</label>
            <input
              type="password"
              v-model="password"
              class="w-full border px-3 py-2 rounded"
              required
            />
          </div>
          <div v-if="error" class="mb-4 text-red-600">{{ error }}</div>
          <button
            type="submit"
            class="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from "vue";
  import { useRouter } from "vue-router";
  import api from "../api"; // Use your api instance
  
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
  
      // Store user info and JWT token
    //   const { user, token } = res.data;
    //   localStorage.setItem("user", JSON.stringify(user));
    //   localStorage.setItem("token", token);
    const { user, token } = res.data;
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", token);
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;

  
      // Set default Authorization header for future requests
    //   api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  
      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err) {
      if (err.response && err.response.data.error) {
        error.value = err.response.data.error;
      } else {
        error.value = "Login failed. Try again.";
      }
    }
  };
  </script>
  
  <style scoped>
  body {
    margin: 0;
    font-family: Arial, sans-serif;
  }
  </style>
  