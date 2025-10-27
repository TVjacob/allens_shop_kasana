<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">User & Permission Management</h1>

    <!-- Tabs -->
    <div class="flex border-b mb-4">
      <button
        class="px-4 py-2"
        :class="activeTab === 'users' ? 'border-b-2 border-indigo-500 font-bold' : ''"
        @click="activeTab = 'users'"
      >
        Users
      </button>
      <button
        class="px-4 py-2"
        :class="activeTab === 'permissions' ? 'border-b-2 border-indigo-500 font-bold' : ''"
        @click="activeTab = 'permissions'"
      >
        Permissions
      </button>
      <button
        class="px-4 py-2"
        :class="activeTab === 'assign' ? 'border-b-2 border-indigo-500 font-bold' : ''"
        @click="activeTab = 'assign'"
      >
        Assign Permissions
      </button>
    </div>

    <!-- Users Tab -->
    <div v-if="activeTab === 'users'">
      <h2 class="font-bold mb-2">{{ editingUser ? 'Edit User' : 'Add User' }}</h2>
      <form @submit.prevent="submitUser" class="flex gap-2 flex-wrap mb-4">
        <input v-model="userForm.username" placeholder="Username" class="border p-2 rounded" required />
        <input v-model="userForm.password" type="password" placeholder="Password" class="border p-2 rounded" :required="!editingUser" />
        <select v-model="userForm.role" class="border p-2 rounded">
          <option>Staff</option>
          <option>Admin</option>
        </select>
        <button class="bg-indigo-500 text-white px-4 py-2 rounded">{{ editingUser ? 'Update' : 'Add' }}</button>
        <button v-if="editingUser" type="button" @click="cancelUserEdit" class="bg-gray-500 text-white px-4 py-2 rounded">Cancel</button>
      </form>

      <table class="min-w-full bg-white border">
        <thead>
          <tr>
            <th class="p-2 border">ID</th>
            <th class="p-2 border">Username</th>
            <th class="p-2 border">Role</th>
            <th class="p-2 border">Status</th>
            <th class="p-2 border">Permissions</th>
            <th class="p-2 border">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td class="p-2 border">{{ user.id }}</td>
            <td class="p-2 border">{{ user.username }}</td>
            <td class="p-2 border">{{ user.role }}</td>
            <td class="p-2 border">{{ user.status === 1 ? 'Active' : 'Inactive' }}</td>
            <td class="p-2 border">{{ user.permissions.join(', ') }}</td>
            <td class="p-2 border flex gap-2">
              <button @click="editUser(user)" class="bg-blue-400 text-white px-2 py-1 rounded">Edit</button>
              <button @click="deleteUser(user.id)" class="bg-red-500 text-white px-2 py-1 rounded">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Permissions Tab -->
    <div v-if="activeTab === 'permissions'">
      <h2 class="font-bold mb-2">Add Permission</h2>
      <form @submit.prevent="submitPermission" class="flex gap-2 flex-wrap mb-4">
        <input v-model="permissionForm.name" placeholder="Permission Name" class="border p-2 rounded" required />
        <input v-model="permissionForm.description" placeholder="Description" class="border p-2 rounded" />
        <button class="bg-green-500 text-white px-4 py-2 rounded">Add Permission</button>
      </form>

      <table class="min-w-full bg-white border">
        <thead>
          <tr>
            <th class="p-2 border">ID</th>
            <th class="p-2 border">Name</th>
            <th class="p-2 border">Description</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="perm in permissions" :key="perm.id">
            <td class="p-2 border">{{ perm.id }}</td>
            <td class="p-2 border">{{ perm.name }}</td>
            <td class="p-2 border">{{ perm.description }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Assign Permissions Tab -->
    <div v-if="activeTab === 'assign'">
      <h2 class="font-bold mb-2">Assign Permission to User</h2>
      <form @submit.prevent="assignPermission" class="flex gap-2 flex-wrap mb-4">
        <select v-model="assignForm.user_id" class="border p-2 rounded" required>
          <option value="">Select User</option>
          <option v-for="user in users" :value="user.id" :key="user.id">{{ user.username }}</option>
        </select>
        <select v-model="assignForm.permission_id" class="border p-2 rounded" required>
          <option value="">Select Permission</option>
          <option v-for="perm in permissions" :value="perm.id" :key="perm.id">{{ perm.name }}</option>
        </select>
        <button class="bg-indigo-500 text-white px-4 py-2 rounded">Assign</button>
      </form>
    </div>
  </div>
</template>

<script>
import api from '../api';

export default {
  data() {
    return {
      activeTab: 'users',
      users: [],
      permissions: [],
      userForm: { id: null, username: '', password: '', role: 'Staff' },
      permissionForm: { name: '', description: '' },
      assignForm: { user_id: '', permission_id: '' },
      editingUser: false
    };
  },
  methods: {
    async fetchUsers() {
      try {
        const res = await api.get('/users/');
        this.users = res.data;
      } catch (err) {
        console.error('Error fetching users:', err.response?.data || err);
      }
    },
    async fetchPermissions() {
      try {
        const res = await api.get('/users/permissions');
        this.permissions = res.data;
      } catch (err) {
        console.error('Error fetching permissions:', err.response?.data || err);
      }
    },
    async submitUser() {
      try {
        if (this.editingUser) {
          await api.put(`/users/${this.userForm.id}`, this.userForm);
        } else {
          await api.post('/users/', this.userForm);
        }
        this.resetUserForm();
        this.fetchUsers();
      } catch (err) {
        console.error('Error saving user:', err.response?.data || err);
      }
    },
    editUser(user) {
      this.userForm = { ...user, password: '' };
      this.editingUser = true;
    },
    cancelUserEdit() {
      this.resetUserForm();
    },
    resetUserForm() {
      this.userForm = { id: null, username: '', password: '', role: 'Staff' };
      this.editingUser = false;
    },
    async deleteUser(userId) {
      if (!confirm('Are you sure you want to delete this user?')) return;
      try {
        await api.delete(`/users/${userId}`);
        this.fetchUsers();
      } catch (err) {
        console.error('Error deleting user:', err.response?.data || err);
      }
    },
    async submitPermission() {
      try {
        await api.post('/users/permissions', this.permissionForm);
        this.permissionForm = { name: '', description: '' };
        this.fetchPermissions();
      } catch (err) {
        console.error('Error creating permission:', err.response?.data || err);
      }
    },
    async assignPermission() {
      try {
        await api.post(`/users/${this.assignForm.user_id}/permissions/${this.assignForm.permission_id}`);
        alert('Permission assigned!');
        this.assignForm = { user_id: '', permission_id: '' };
        this.fetchUsers();
      } catch (err) {
        console.error('Error assigning permission:', err.response?.data || err);
      }
    }
  },
  mounted() {
    this.fetchUsers();
    this.fetchPermissions();
  }
};
</script>

<style scoped>
button {
  cursor: pointer;
}
</style>
