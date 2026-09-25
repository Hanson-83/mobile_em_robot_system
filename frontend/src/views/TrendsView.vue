<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import { api } from "../api";

interface Measurement {
  id: string;
  metric: string;
  value: number | null;
  unit: string;
  ts: string;
  point_id: string | null;
  quality: string;
}

const metric = ref("temp_c");
const items = ref<Measurement[]>([]);
let timer = 0;

async function load(): Promise<void> {
  const body = await api<{ items: Measurement[] }>(`/api/v1/measurements?metric=${encodeURIComponent(metric.value)}`);
  items.value = body.items.filter((item) => item.quality !== "bad");
}

onMounted(() => {
  void load();
  timer = window.setInterval(() => {
    void load().catch(() => undefined);
  }, 3000);
});

onUnmounted(() => {
  window.clearInterval(timer);
});

function polyline(values: Measurement[]): string {
  if (!values.length) {
    return "";
  }
  const nums = values.map((item) => item.value ?? 0);
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const span = max - min || 1;
  return values
    .map((item, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * 300;
      const y = 100 - (((item.value ?? 0) - min) / span) * 90;
      return `${x},${y}`;
    })
    .join(" ");
}
</script>

<template>
  <section>
    <h2>实时 / 历史趋势</h2>
    <form class="card row" @submit.prevent="load">
      <label>
        指标
        <select v-model="metric">
          <option value="temp_c">温度</option>
          <option value="humidity_rh">湿度</option>
          <option value="air_speed_mps">风速</option>
          <option value="particle.0.5um">粒子 0.5μm</option>
          <option value="particle.5.0um">粒子 5.0μm</option>
        </select>
      </label>
      <button type="submit">查询</button>
    </form>
    <article class="card">
      <svg viewBox="0 0 300 110" style="width: 100%; height: 220px; background: #f7faf8">
        <polyline :points="polyline(items)" fill="none" stroke="#0b6e4f" stroke-width="2" />
      </svg>
      <p class="muted">共 {{ items.length }} 个点。看板默认不画 quality=bad。</p>
      <table>
        <thead>
          <tr><th>时间</th><th>点位</th><th>值</th><th>质量</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.ts }}</td>
            <td>{{ item.point_id }}</td>
            <td>{{ item.value }} {{ item.unit }}</td>
            <td>{{ item.quality }}</td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>
