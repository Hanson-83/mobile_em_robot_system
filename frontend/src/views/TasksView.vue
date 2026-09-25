<script setup lang="ts">
import { ref } from "vue";
import { api } from "../api/client";

const result = ref("");
const error = ref("");
const busy = ref(false);

async function createTask() {
  busy.value = true;
  error.value = "";
  try {
    result.value = JSON.stringify(
      await api("/api/v1/tasks", {
        method: "POST",
        body: JSON.stringify({
          robot_id: "robot-01",
          point_id: "P1",
          elevator_id: "elev-01",
          elevator_floor: 2,
        }),
      }),
      null,
      2,
    );
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section>
    <h1>任务编排（M1 冒烟）</h1>
    <p>下发 Fake 全链路：导航 → 电梯 Call/Enter/Exit → 仪表读数。</p>
    <button :disabled="busy" @click="createTask">创建并执行示例任务</button>
    <p v-if="error" class="err">{{ error }}</p>
    <pre v-if="result">{{ result }}</pre>
  </section>
</template>

<style scoped>
.err {
  color: #b00020;
}
pre {
  background: #f4f4f4;
  padding: 0.75rem;
}
</style>
