<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf } from "../api/client";

type TaskRow = { id: string; state: string; robot_id?: string; point_id?: string };

const tasks = ref<TaskRow[]>([]);
const error = ref("");
const busy = ref(false);

async function refresh() {
  tasks.value = await api<TaskRow[]>("/api/v1/tasks");
}

onMounted(async () => {
  try {
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
});

async function createTask() {
  busy.value = true;
  error.value = "";
  try {
    await api("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify({
        robot_id: "robot-01",
        point_id: "P1",
        elevator_id: "elev-01",
        elevator_floor: 2,
      }),
    });
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}

async function stopTask(id: string) {
  error.value = "";
  try {
    await api(`/api/v1/tasks/${id}/stop`, { method: "POST" });
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
}
</script>

<template>
  <section>
    <h1>任务编排</h1>
    <p>下发 Fake 全链路：导航 → 电梯 Call/Enter/Exit → 仪表读数。排队中的任务可停止。</p>
    <button :disabled="busy" @click="createTask">创建并执行示例任务</button>
    <p v-if="error" class="err">{{ error }}</p>
    <h2>任务列表</h2>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>状态</th>
          <th>机器人</th>
          <th>点位</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tasks" :key="t.id">
          <td>{{ t.id }}</td>
          <td>{{ t.state }}</td>
          <td>{{ t.robot_id }}</td>
          <td>{{ t.point_id }}</td>
          <td>
            <button
              v-if="t.state === 'Queued' || t.state === 'Running'"
              type="button"
              @click="stopTask(t.id)"
            >
              停止
            </button>
          </td>
        </tr>
        <tr v-if="tasks.length === 0">
          <td colspan="5">暂无任务</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.err {
  color: #b00020;
}
table {
  margin-top: 1rem;
  border-collapse: collapse;
}
th,
td {
  border: 1px solid #ccc;
  padding: 0.35rem 0.6rem;
}
</style>
