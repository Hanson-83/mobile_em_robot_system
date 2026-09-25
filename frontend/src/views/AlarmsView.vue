<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import { api, token } from "../api";

interface Alarm {
  id: string;
  ts: string;
  severity: string;
  state: string;
  source: string;
  message: string;
  rule_id: string;
}

const alarms = ref<Alarm[]>([]);
const state = ref("");
const message = ref("");
let timer = 0;

async function load(): Promise<void> {
  const query = state.value ? `?state=${state.value}` : "";
  const body = await api<{ items: Alarm[] }>(`/api/v1/alarms${query}`);
  alarms.value = body.items;
}

async function act(id: string, action: "ack" | "close"): Promise<void> {
  message.value = "";
  try {
    await api(`/api/v1/alarms/${id}/${action}`, { method: "POST", body: JSON.stringify({ note: action }) });
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "操作失败";
  }
}

function exportUrl(): string {
  return `/api/v1/alarms/export?token=unused`;
}

async function download(): Promise<void> {
  const response = await fetch("/api/v1/alarms/export", { headers: { Authorization: `Bearer ${token()}` } });
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "alarms.csv";
  link.click();
  URL.revokeObjectURL(url);
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
</script>

<template>
  <section>
    <h2>报警</h2>
    <div class="card row">
      <label>
        状态
        <select v-model="state" @change="load">
          <option value="">全部</option>
          <option value="open">未确认</option>
          <option value="acked">已确认</option>
          <option value="closed">已关闭</option>
        </select>
      </label>
      <button type="button" @click="load">刷新</button>
      <button class="secondary" type="button" @click="download">导出 CSV</button>
    </div>
    <p v-if="message" class="error">{{ message }}</p>
    <article class="card">
      <table>
        <thead>
          <tr><th>时间</th><th>级别</th><th>状态</th><th>来源</th><th>内容</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="alarm in alarms" :key="alarm.id">
            <td>{{ alarm.ts }}</td>
            <td>{{ alarm.severity }}</td>
            <td>{{ alarm.state }}</td>
            <td>{{ alarm.source }}</td>
            <td>{{ alarm.message }}</td>
            <td>
              <button v-if="alarm.state === 'open'" type="button" @click="act(alarm.id, 'ack')">确认</button>
              <button v-if="alarm.state === 'acked'" class="secondary" type="button" @click="act(alarm.id, 'close')">关闭</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="muted">导出地址仅作说明：{{ exportUrl() }}，实际下载走带鉴权的请求。</p>
    </article>
  </section>
</template>
