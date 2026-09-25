<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api/client";

interface TaskRow {
  id: string;
  name: string;
  state: string;
  robot_id: string | null;
}

const tasks = ref<TaskRow[]>([]);
const name = ref("巡检-走廊");
const error = ref("");

async function refresh() {
  tasks.value = await api<TaskRow[]>("/api/v1/tasks");
}

async function startTask(id: string) {
  error.value = "";
  try {
    await api(`/api/v1/tasks/${id}/start`, { method: "POST" });
    await refresh();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "启动失败";
  }
}

async function createTask() {
  error.value = "";
  try {
    await api("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify({
        name: name.value,
        robot_id: "robot-01",
        skills: [{ type: "navigate_to", params: { point_id: "P1" } }],
      }),
    });
    await refresh();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "创建失败";
  }
}

onMounted(() => {
  refresh().catch((err) => {
    error.value = err instanceof Error ? err.message : "加载失败";
  });
});
</script>

<template>
  <section class="card">
    <h1>任务编排</h1>
    <p class="hint">M1 仅创建/列表/取消骨架；全链路调度（含电梯）在 M2 接入状态机。</p>
    <form class="row" @submit.prevent="createTask">
      <input v-model="name" />
      <button type="submit">创建任务</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
    <ul>
      <li v-for="t in tasks" :key="t.id">
        {{ t.name }} · {{ t.state }} · {{ t.robot_id }}
        <button v-if="t.state === 'Created'" type="button" @click="startTask(t.id)">启动</button>
      </li>
      <li v-if="!tasks.length">暂无任务</li>
    </ul>
  </section>
</template>
