<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf } from "../api/client";

type User = { username: string; roles: string[] };

const users = ref<User[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    users.value = await api<User[]>("/api/v1/users");
  } catch (e) {
    error.value = messageOf(e);
  }
});
</script>

<template>
  <section>
    <h1>用户权限</h1>
    <p>账号来自环境变量 MER_DEV_USERS_JSON，本页只读。生产目录尚未接入。</p>
    <p v-if="error" class="err">{{ error }}</p>
    <table>
      <thead>
        <tr>
          <th>用户</th>
          <th>角色</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.username">
          <td>{{ u.username }}</td>
          <td>{{ u.roles.join(", ") }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
