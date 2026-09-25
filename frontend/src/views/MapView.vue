<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api/client";

interface RobotRow {
  robot_id: string;
  mode: string;
  battery_pct: number | null;
  online: boolean;
  pose?: { x: number; y: number } | null;
}

const robots = ref<RobotRow[]>([]);
const maps = ref<Array<{ id: string; name: string }>>([]);
const error = ref("");

onMounted(async () => {
  try {
    robots.value = await api<RobotRow[]>("/api/v1/robots");
    maps.value = await api<Array<{ id: string; name: string }>>("/api/v1/maps");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载失败";
  }
});
</script>

<template>
  <section class="card">
    <h1>地图监控</h1>
    <p class="hint">
      地图中间表示尚未标准化（待确认）。当前为占位画布 + Fake 机器人位姿。
    </p>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="map-shell">
      <div
        v-for="r in robots"
        :key="r.robot_id"
        class="dot"
        :style="{ left: `${(r.pose?.x ?? 0) * 24 + 20}px`, top: `${(r.pose?.y ?? 0) * 24 + 20}px` }"
        :title="r.robot_id"
      />
    </div>
    <ul>
      <li v-for="r in robots" :key="r.robot_id">
        {{ r.robot_id }} · {{ r.mode }} · 电量 {{ r.battery_pct ?? "-" }}% ·
        位姿 ({{ r.pose?.x ?? 0 }}, {{ r.pose?.y ?? 0 }})
      </li>
      <li v-for="m in maps" :key="m.id">地图：{{ m.name }} ({{ m.id }})</li>
    </ul>
  </section>
</template>
