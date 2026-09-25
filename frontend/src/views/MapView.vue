<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import { api, token } from "../api";

interface Pose {
  x: number;
  y: number;
  theta: number;
}
interface Point {
  id: string;
  name: string;
  pose: Pose;
}
interface MapItem {
  id: string;
  name: string;
  width_m: number;
  height_m: number;
  points: Point[];
}
interface Robot {
  id: string;
  name: string;
  status: { mode: string; online: boolean; battery_pct: number | null; pose: Pose | null; estop: boolean };
}

const maps = ref<MapItem[]>([]);
const robots = ref<Robot[]>([]);
const message = ref("");
let timer = 0;
let socket: WebSocket | undefined;

async function load(): Promise<void> {
  const mapBody = await api<{ items: MapItem[] }>("/api/v1/maps");
  const robotBody = await api<{ items: Robot[] }>("/api/v1/robots");
  maps.value = mapBody.items;
  robots.value = robotBody.items;
}

onMounted(() => {
  void load().catch((err: unknown) => {
    message.value = err instanceof Error ? err.message : "加载失败";
  });
  timer = window.setInterval(() => {
    void load().catch(() => undefined);
  }, 5000);
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${location.host}/api/v1/ws?token=${encodeURIComponent(token())}`);
  socket.onopen = () => {
    socket?.send(JSON.stringify({ topics: ["pose", "task", "alarm", "measurement"] }));
  };
  socket.onmessage = (event) => {
    const body = JSON.parse(String(event.data)) as { topic?: string };
    if (body.topic === "hello" || body.topic === "subscribed" || body.topic === "heartbeat") {
      return;
    }
    void load().catch(() => undefined);
  };
});

onUnmounted(() => {
  window.clearInterval(timer);
  socket?.close();
});
</script>

<template>
  <section>
    <h2>地图监控</h2>
    <p v-if="message" class="error">{{ message }}</p>
    <article v-for="item in maps" :key="item.id" class="card">
      <h3>{{ item.name }}</h3>
      <svg class="map" :viewBox="`0 0 ${item.width_m} ${item.height_m}`">
        <rect :width="item.width_m" :height="item.height_m" fill="#e7f0ea" />
        <g v-for="point in item.points" :key="point.id">
          <circle :cx="point.pose.x" :cy="item.height_m - point.pose.y" r="0.35" fill="#0b6e4f" />
          <text :x="point.pose.x + 0.4" :y="item.height_m - point.pose.y" font-size="0.7">{{ point.name }}</text>
        </g>
        <g v-for="robot in robots" :key="robot.id">
          <circle
            v-if="robot.status.pose"
            :cx="robot.status.pose.x"
            :cy="item.height_m - robot.status.pose.y"
            r="0.45"
            :fill="robot.status.estop ? '#9f2d2d' : '#1d4e89'"
          />
        </g>
      </svg>
    </article>
    <article class="card">
      <table>
        <thead>
          <tr><th>机器人</th><th>在线</th><th>模式</th><th>电量</th><th>位姿</th></tr>
        </thead>
        <tbody>
          <tr v-for="robot in robots" :key="robot.id">
            <td>{{ robot.name }}</td>
            <td>{{ robot.status.online ? "在线" : "离线" }}</td>
            <td>{{ robot.status.mode }}</td>
            <td>{{ robot.status.battery_pct ?? "-" }}</td>
            <td v-if="robot.status.pose">{{ robot.status.pose.x.toFixed(1) }}, {{ robot.status.pose.y.toFixed(1) }}</td>
            <td v-else>-</td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>
