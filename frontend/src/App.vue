<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from "vue-router";
import { clearToken, getToken } from "./api/client";

const router = useRouter();
const links = [
  ["/map", "地图监控"],
  ["/tasks", "任务编排"],
  ["/points", "点位/限值"],
  ["/trends", "实时趋势"],
  ["/alarms", "报警"],
  ["/reports", "报告"],
  ["/users", "用户权限"],
  ["/settings", "系统开关"],
  ["/approvals", "批准中心"],
];

function logout() {
  clearToken();
  void router.push("/login");
}
</script>

<template>
  <div class="shell">
    <header>
      <strong>MER 上位机</strong>
      <nav>
        <RouterLink v-for="[to, label] in links" :key="to" :to="to">{{ label }}</RouterLink>
      </nav>
      <button v-if="getToken()" type="button" class="ghost" @click="logout">退出</button>
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
  color: #1c2833;
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
  flex-wrap: wrap;
  gap: 0.75rem;
  flex: 1;
}
.shell nav a {
  color: #d6e8ff;
  text-decoration: none;
}
.shell nav a.router-link-active {
  text-decoration: underline;
}
.shell main {
  padding: 1rem;
}
button.ghost {
  background: transparent;
  color: #fff;
  border: 1px solid #8fb4d6;
}
table {
  border-collapse: collapse;
  margin-top: 0.75rem;
}
th,
td {
  border: 1px solid #ccc;
  padding: 0.35rem 0.6rem;
  text-align: left;
}
.err {
  color: #b00020;
}
form.grid {
  display: grid;
  gap: 0.5rem;
  max-width: 28rem;
}
</style>
