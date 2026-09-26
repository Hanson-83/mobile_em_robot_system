<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api, messageOf } from "../api/client";

type Sample = { metric: string; value: number; unit?: string; task_id?: string };

const metric = ref("0.5um");
const series = ref<Sample[]>([]);
const error = ref("");

const points = computed(() => {
  if (!series.value.length) return "";
  const values = series.value.map((s) => s.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return series.value
    .map((s, i) => {
      const x = series.value.length === 1 ? 160 : (i / (series.value.length - 1)) * 320;
      const y = 140 - ((s.value - min) / span) * 120;
      return `${x},${y}`;
    })
    .join(" ");
});

async function load() {
  error.value = "";
  try {
    const data = await api<{ series: Sample[] }>(`/api/v1/trends?metric=${encodeURIComponent(metric.value)}`);
    series.value = data.series;
  } catch (e) {
    error.value = messageOf(e);
  }
}

onMounted(load);
</script>

<template>
  <section>
    <h1>实时趋势</h1>
    <p>历史序列来自已完成任务的测量。实时推送仍为 WebSocket 占位。</p>
    <form class="grid" @submit.prevent="load">
      <label>
        指标
        <select v-model="metric">
          <option>0.5um</option>
          <option>0.1um</option>
          <option>1.0um</option>
          <option>5.0um</option>
          <option>temperature_c</option>
          <option>humidity_pct</option>
          <option>speed_mps</option>
        </select>
      </label>
      <button type="submit">查询</button>
    </form>
    <p v-if="error" class="err">{{ error }}</p>
    <svg v-if="series.length" viewBox="0 0 320 160" width="100%" height="180">
      <polyline fill="none" stroke="#17324d" stroke-width="2" :points="points" />
    </svg>
    <p v-else>暂无曲线</p>
    <table v-if="series.length">
      <thead>
        <tr>
          <th>任务</th>
          <th>值</th>
          <th>单位</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(s, i) in series" :key="i">
          <td>{{ s.task_id }}</td>
          <td>{{ s.value }}</td>
          <td>{{ s.unit }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
