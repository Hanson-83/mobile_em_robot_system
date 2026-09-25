<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { api, setSession } from "../api";

const router = useRouter();
const username = ref("admin");
const password = ref("");
const error = ref("");

async function submit(): Promise<void> {
  error.value = "";
  try {
    const result = await api<{ access_token: string; username: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: username.value, password: password.value }),
    });
    setSession(result.access_token, result.username);
    await router.push("/map");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "登录失败";
  }
}
</script>

<template>
  <form class="card login" @submit.prevent="submit">
    <h2>登录</h2>
    <p class="muted">开发种子账号 admin / Admin123!。生产环境必须关闭种子并更换密钥。</p>
    <div class="row">
      <label>账号 <input v-model="username" autocomplete="username" /></label>
      <label>口令 <input v-model="password" type="password" autocomplete="current-password" /></label>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <button type="submit">登录</button>
  </form>
</template>
