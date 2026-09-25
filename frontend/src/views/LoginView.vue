<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../api/client";

const username = ref("admin");
const password = ref("admin");
const error = ref("");
const router = useRouter();

async function onSubmit() {
  error.value = "";
  try {
    await login(username.value, password.value);
    await router.push("/map");
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}
</script>

<template>
  <section>
    <h1>登录</h1>
    <p>开发占位账号：admin / admin（生产须替换用户库）。</p>
    <form @submit.prevent="onSubmit">
      <label>用户 <input v-model="username" /></label>
      <label>密码 <input v-model="password" type="password" /></label>
      <button type="submit">进入</button>
    </form>
    <p v-if="error" class="err">{{ error }}</p>
  </section>
</template>

<style scoped>
form {
  display: grid;
  gap: 0.5rem;
  max-width: 20rem;
}
.err {
  color: #b00020;
}
</style>
