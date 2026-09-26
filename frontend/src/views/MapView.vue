<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf } from "../api/client";

type Pose = { x?: number; y?: number; theta?: number };
type Robot = { id: string; status?: { pose?: Pose; mode?: string; battery_pct?: number; online?: boolean; estop?: boolean } };
type MapPoint = { id?: string; name?: string; x?: number; y?: number };
type MapRec = { id: string; name?: string; format?: string; points?: MapPoint[]; note?: string };

const robots = ref<Robot[]>([]);
const maps = ref<MapRec[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    robots.value = await api<Robot[]>("/api/v1/robots");
    maps.value = await api<MapRec[]>("/api/v1/maps");
  } catch (e) {
    error.value = messageOf(e);
  }
});
</script>

<template>
  <section>
    <h1>地图监控</h1>
    <p>位姿来自 Fake AMR。地图格式暂为 GeoJSON 点位占位。</p>
    <p v-if="error" class="err">{{ error }}</p>
    <h2>机器人</h2>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>在线</th>
          <th>模式</th>
          <th>电量</th>
          <th>急停</th>
          <th>X</th>
          <th>Y</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in robots" :key="r.id">
          <td>{{ r.id }}</td>
          <td>{{ r.status?.online }}</td>
          <td>{{ r.status?.mode }}</td>
          <td>{{ r.status?.battery_pct }}</td>
          <td>{{ r.status?.estop }}</td>
          <td>{{ r.status?.pose?.x }}</td>
          <td>{{ r.status?.pose?.y }}</td>
        </tr>
      </tbody>
    </table>
    <h2>地图</h2>
    <article v-for="m in maps" :key="m.id">
      <p>{{ m.name || m.id }}（{{ m.format || "unknown" }}）{{ m.note }}</p>
      <ul>
        <li v-for="(p, i) in m.points || []" :key="p.id || i">
          {{ p.name || p.id }} ({{ p.x }}, {{ p.y }})
        </li>
      </ul>
    </article>
  </section>
</template>
