<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import { api } from "../api";

interface Task {
  id: string;
  robot_id: string;
  status: string;
  error_code: string | null;
  error_message: string | null;
}

const robotId = ref("robot-01");
const pointId = ref("point-a");
const tasks = ref<Task[]>([]);
const message = ref("");
let timer = 0;

async function refresh(): Promise<void> {
  const body = await api<{ items: Task[] }>("/api/v1/tasks");
  tasks.value = body.items.slice().reverse();
}

async function createTask(): Promise<void> {
  message.value = "";
  try {
    await api("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify({ robot_id: robotId.value, point_id: pointId.value }),
    });
    await api("/api/v1/scheduler/drain", { method: "POST" });
    await refresh();
    message.value = "任务已执行";
  } catch (err) {
    message.value = err instanceof Error ? err.message : "下发失败";
  }
}

async function cancel(id: string): Promise<void> {
  await api(`/api/v1/tasks/${id}/cancel`, { method: "POST" });
  await refresh();
}

onMounted(() => {
  void refresh();
  timer = window.setInterval(() => {
    void refresh().catch(() => undefined);
  }, 3000);
});

onUnmounted(() => {
  window.clearInterval(timer);
});
</script>

<template>
  <section>
    <h2>任务编排</h2>
    <form class="card row" @submit.prevent="createTask">
      <label>机器人 <input v-model="robotId" /></label>
      <label>点位 <input v-model="pointId" /></label>
      <button type="submit">下发并执行</button>
    </form>
    <p v-if="message">{{ message }}</p>
    <article class="card">
      <table>
        <thead>
          <tr><th>任务</th><th>机器人</th><th>状态</th><th>错误</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>{{ task.id.slice(0, 8) }}</td>
            <td>{{ task.robot_id }}</td>
            <td>{{ task.status }}</td>
            <td>{{ task.error_code || "" }} {{ task.error_message || "" }}</td>
            <td>
              <button v-if="task.status === 'Queued' || task.status === 'Running'" class="secondary" type="button" @click="cancel(task.id)">取消</button>
            </td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>
