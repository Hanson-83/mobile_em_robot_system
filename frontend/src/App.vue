<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { clearSession, currentUser } from "./api";

const route = useRoute();
const router = useRouter();
const showNav = computed(() => route.path !== "/login");

function logout(): void {
  clearSession();
  void router.push("/login");
}
</script>

<template>
  <div v-if="showNav" class="layout">
    <nav>
      <h1>环境监测上位机</h1>
      <RouterLink to="/map">地图监控</RouterLink>
      <RouterLink to="/tasks">任务编排</RouterLink>
      <RouterLink to="/points">点位 / 限值</RouterLink>
      <RouterLink to="/trends">实时趋势</RouterLink>
      <RouterLink to="/alarms">报警</RouterLink>
      <RouterLink to="/reports">报告</RouterLink>
      <RouterLink to="/approvals">批准中心</RouterLink>
      <RouterLink to="/users">用户权限</RouterLink>
      <RouterLink to="/settings">系统开关</RouterLink>
      <p class="muted">{{ currentUser() }}</p>
      <button class="secondary" type="button" @click="logout">退出</button>
    </nav>
    <main>
      <RouterView />
    </main>
  </div>
  <RouterView v-else />
</template>
