<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../api/client";

const router = useRouter();
const username = ref("admin");
const password = ref("admin");
const error = ref("");
const loading = ref(false);

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await login(username.value, password.value);
    await router.push("/map");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="card narrow">
    <h1>登录</h1>
    <p class="hint">开发默认账号 admin / admin（请在部署环境修改密码）。</p>
    <form @submit.prevent="onSubmit">
      <label>用户名 <input v-model="username" autocomplete="username" /></label>
      <label>密码 <input v-model="password" type="password" autocomplete="current-password" /></label>
      <button type="submit" :disabled="loading">{{ loading ? "登录中…" : "登录" }}</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </section>
</template>
