<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api";

interface User {
  id: string;
  username: string;
  display_name: string;
  roles: string[];
}
interface Group {
  id: string;
  name: string;
  user_ids: string[];
}

const users = ref<User[]>([]);
const groups = ref<Group[]>([]);
const form = ref({ username: "", password: "", display_name: "", role: "viewer" });
const groupName = ref("");
const message = ref("");

async function load(): Promise<void> {
  users.value = (await api<{ items: User[] }>("/api/v1/users")).items;
  groups.value = (await api<{ items: Group[] }>("/api/v1/groups")).items;
}

async function createUser(): Promise<void> {
  message.value = "";
  try {
    await api("/api/v1/users", {
      method: "POST",
      body: JSON.stringify({
        username: form.value.username,
        password: form.value.password,
        display_name: form.value.display_name,
        roles: [form.value.role],
      }),
    });
    form.value = { username: "", password: "", display_name: "", role: "viewer" };
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "创建失败";
  }
}

async function createGroup(): Promise<void> {
  await api("/api/v1/groups", { method: "POST", body: JSON.stringify({ name: groupName.value, user_ids: [] }) });
  groupName.value = "";
  await load();
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section>
    <h2>用户 / 组 / 角色</h2>
    <p v-if="message" class="error">{{ message }}</p>
    <form class="card row" @submit.prevent="createUser">
      <label>账号 <input v-model="form.username" required /></label>
      <label>显示名 <input v-model="form.display_name" /></label>
      <label>口令 <input v-model="form.password" type="password" required /></label>
      <label>
        角色
        <select v-model="form.role">
          <option value="viewer">查看</option>
          <option value="operator">操作</option>
          <option value="admin">管理</option>
        </select>
      </label>
      <button type="submit">创建用户</button>
    </form>
    <article class="card">
      <table>
        <thead><tr><th>账号</th><th>名称</th><th>角色</th></tr></thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.display_name }}</td>
            <td>{{ user.roles.join(", ") }}</td>
          </tr>
        </tbody>
      </table>
    </article>
    <form class="card row" @submit.prevent="createGroup">
      <label>用户组 <input v-model="groupName" required /></label>
      <button type="submit">创建组</button>
    </form>
    <p class="muted">已有用户组：{{ groups.map((item) => item.name).join("、") || "无" }}</p>
  </section>
</template>
