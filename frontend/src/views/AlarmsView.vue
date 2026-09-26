<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { api, getToken, messageOf } from "../api/client";

type Alarm = { id: string; state: string; severity?: string; message?: string; task_id?: string };

const alarms = ref<Alarm[]>([]);
const error = ref("");
const csv = ref("");
const liveHint = ref("");
let socket: WebSocket | null = null;

async function refresh() {
  alarms.value = await api<Alarm[]>("/api/v1/alarms");
}

onMounted(async () => {
  try {
    await refresh();
    const token = getToken();
    if (!token) return;
    const proto = location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${proto}://${location.host}/api/v1/ws?token=${encodeURIComponent(token)}`);
    socket.onmessage = (ev) => {
      const data = JSON.parse(String(ev.data)) as { type?: string; alarms?: Alarm[] };
      if (data.type === "snapshot" && data.alarms) {
        alarms.value = data.alarms;
        liveHint.value = "报警列表由实时通道刷新";
      }
    };
  } catch (e) {
    error.value = messageOf(e);
  }
});

onUnmounted(() => socket?.close());

async function act(id: string, op: "ack" | "close") {
  error.value = "";
  try {
    await api(`/api/v1/alarms/${id}/${op}`, { method: "POST" });
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
}

async function exportCsv() {
  error.value = "";
  try {
    const data = await api<{ content: string }>("/api/v1/alarms/export");
    csv.value = data.content;
  } catch (e) {
    error.value = messageOf(e);
  }
}
</script>

<template>
  <section>
    <h1>报警</h1>
    <p>{{ liveHint }}</p>
    <button type="button" @click="exportCsv">导出 CSV</button>
    <p v-if="error" class="err">{{ error }}</p>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>状态</th>
          <th>级别</th>
          <th>说明</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in alarms" :key="a.id">
          <td>{{ a.id }}</td>
          <td>{{ a.state }}</td>
          <td>{{ a.severity }}</td>
          <td>{{ a.message }}</td>
          <td>
            <button v-if="a.state === 'active'" type="button" @click="act(a.id, 'ack')">确认</button>
            <button v-if="a.state !== 'closed'" type="button" @click="act(a.id, 'close')">关闭</button>
          </td>
        </tr>
        <tr v-if="alarms.length === 0">
          <td colspan="5">暂无报警</td>
        </tr>
      </tbody>
    </table>
    <pre v-if="csv">{{ csv }}</pre>
  </section>
</template>
