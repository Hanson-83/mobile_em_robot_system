<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { api, getToken, messageOf } from "../api/client";

type Pose = { x?: number; y?: number; theta?: number };
type Robot = { id: string; status?: { pose?: Pose; mode?: string; battery_pct?: number; online?: boolean; estop?: boolean } };
type MapPoint = { id?: string; name?: string; x?: number; y?: number };
type MapRec = { id: string; name?: string; format?: string; points?: MapPoint[]; note?: string };

const robots = ref<Robot[]>([]);
const maps = ref<MapRec[]>([]);
const error = ref("");
const liveHint = ref("正在连接实时通道");
let socket: WebSocket | null = null;

function connectLive() {
  const token = getToken();
  if (!token) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${proto}://${location.host}/api/v1/ws?token=${encodeURIComponent(token)}`);
  socket.onmessage = (ev) => {
    const data = JSON.parse(String(ev.data)) as { type?: string; robots?: Robot[] };
    if (data.type === "snapshot" && data.robots) {
      robots.value = data.robots;
      liveHint.value = "实时通道已连接";
    }
  };
  socket.onerror = () => {
    liveHint.value = "实时通道未连通，显示最近一次查询";
  };
}

onMounted(async () => {
  try {
    robots.value = await api<Robot[]>("/api/v1/robots");
    maps.value = await api<MapRec[]>("/api/v1/maps");
    connectLive();
  } catch (e) {
    error.value = messageOf(e);
  }
});

onUnmounted(() => socket?.close());
</script>

<template>
  <section>
    <h1>地图监控</h1>
    <p>位姿来自 Fake AMR。地图格式暂为 GeoJSON 点位占位。</p>
    <p v-if="error" class="err">{{ error }}</p>
    <h2>机器人</h2>
    <svg viewBox="0 0 240 140" width="100%" height="160" class="map">
      <rect x="0" y="0" width="240" height="140" fill="#f4f7fb" stroke="#c5d0dc" />
      <g v-for="r in robots" :key="r.id">
        <circle
          :cx="20 + (r.status?.pose?.x || 0) * 12"
          :cy="110 - (r.status?.pose?.y || 0) * 12"
          r="6"
          fill="#17324d"
        />
        <text
          :x="28 + (r.status?.pose?.x || 0) * 12"
          :y="114 - (r.status?.pose?.y || 0) * 12"
          font-size="12"
        >
          {{ r.id }}
        </text>
      </g>
    </svg>
    <p class="live">{{ liveHint }}</p>
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

<style scoped>
.map {
  background: #fff;
  max-width: 36rem;
}
</style>
