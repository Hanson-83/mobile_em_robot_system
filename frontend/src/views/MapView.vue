<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api/client";

const robots = ref<unknown[]>([]);
const maps = ref<unknown[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    robots.value = await api("/api/v1/robots");
    maps.value = await api("/api/v1/maps");
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
});
</script>

<template>
  <section>
    <h1>地图监控（壳）</h1>
    <p>地图中间表示与 AMR 厂地图格式待用户确认；当前为占位图层。</p>
    <p v-if="error" class="err">{{ error }}</p>
    <pre>{{ JSON.stringify({ maps, robots }, null, 2) }}</pre>
  </section>
</template>

<style scoped>
.err {
  color: #b00020;
}
pre {
  background: #f4f4f4;
  padding: 0.75rem;
}
</style>
