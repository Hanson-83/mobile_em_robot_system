<script setup lang="ts">
import { useRouter, useRoute } from "vue-router";
import { getToken, setToken } from "./api/client";

const router = useRouter();
const route = useRoute();

const links = [
  { to: "/map", label: "地图监控" },
  { to: "/tasks", label: "任务编排" },
  { to: "/points", label: "点位/限值" },
  { to: "/trends", label: "实时趋势" },
  { to: "/alarms", label: "报警" },
  { to: "/reports", label: "报告" },
  { to: "/users", label: "用户权限" },
  { to: "/features", label: "系统开关" },
  { to: "/approvals", label: "批准中心" },
];

function logout() {
  setToken(null);
  router.push("/login");
}
</script>

<template>
  <div class="app">
    <header v-if="route.path !== '/login'" class="top">
      <strong>MER 上位机</strong>
      <nav>
        <router-link v-for="l in links" :key="l.to" :to="l.to">{{ l.label }}</router-link>
      </nav>
      <button v-if="getToken()" type="button" @click="logout">退出</button>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>
