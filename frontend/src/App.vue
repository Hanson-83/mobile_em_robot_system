<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div class="shell">
    <header>
      <strong>MER 上位机</strong>
      <nav>
        <RouterLink to="/login">登录</RouterLink>
        <RouterLink to="/map">地图监控</RouterLink>
        <RouterLink to="/tasks">任务编排</RouterLink>
      </nav>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: sans-serif;
}
.shell header {
  display: flex;
  gap: 1rem;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #17324d;
  color: #fff;
}
.shell nav {
  display: flex;
  gap: 0.75rem;
}
.shell nav a {
  color: #d6e8ff;
}
.shell main {
  padding: 1rem;
}
</style>
