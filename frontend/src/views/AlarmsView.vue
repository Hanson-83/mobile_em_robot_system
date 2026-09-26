<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf } from "../api/client";

type Alarm = { id: string; state: string; severity?: string; message?: string; task_id?: string };

const alarms = ref<Alarm[]>([]);
const error = ref("");
const csv = ref("");

async function refresh() {
  alarms.value = await api<Alarm[]>("/api/v1/alarms");
}

onMounted(async () => {
  try {
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
});

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
