<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, getToken, messageOf } from "../api/client";

type Report = { id: string; task_id: string; format: string };
type TaskRow = { id: string; state: string };

const reports = ref<Report[]>([]);
const tasks = ref<TaskRow[]>([]);
const taskId = ref("");
const error = ref("");
const preview = ref("");

async function refresh() {
  reports.value = await api<Report[]>("/api/v1/reports");
  tasks.value = await api<TaskRow[]>("/api/v1/tasks");
  if (!taskId.value && tasks.value.length) taskId.value = tasks.value[0].id;
}

onMounted(async () => {
  try {
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
});

async function createReport() {
  error.value = "";
  try {
    await api("/api/v1/reports", {
      method: "POST",
      body: JSON.stringify({ task_id: taskId.value }),
    });
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
}

async function openReport(id: string) {
  error.value = "";
  preview.value = "";
  try {
    const headers = new Headers();
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const res = await fetch(`/api/v1/reports/${id}/file`, { headers });
    if (!res.ok) throw new Error(res.statusText);
    preview.value = await res.text();
  } catch (e) {
    error.value = messageOf(e);
  }
}
</script>

<template>
  <section>
    <h1>报告</h1>
    <p>批报告为 HTML 归档。PDF 引擎尚未选定。</p>
    <form class="grid" @submit.prevent="createReport">
      <label>
        任务
        <select v-model="taskId" required>
          <option v-for="t in tasks" :key="t.id" :value="t.id">{{ t.id }}（{{ t.state }}）</option>
        </select>
      </label>
      <button type="submit">生成报告</button>
    </form>
    <p v-if="error" class="err">{{ error }}</p>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>任务</th>
          <th>格式</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in reports" :key="r.id">
          <td>{{ r.id }}</td>
          <td>{{ r.task_id }}</td>
          <td>{{ r.format }}</td>
          <td><button type="button" @click="openReport(r.id)">查看</button></td>
        </tr>
        <tr v-if="reports.length === 0">
          <td colspan="4">暂无报告</td>
        </tr>
      </tbody>
    </table>
    <pre v-if="preview">{{ preview }}</pre>
  </section>
</template>
