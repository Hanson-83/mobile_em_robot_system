<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { ApiError, api, messageOf } from "../api/client";

type Point = { id: string; name: string; map_id?: string; pose?: { x?: number; y?: number } };
type Limits = { e_sign: boolean; limits: Record<string, { max?: number; unit?: string }> };

const points = ref<Point[]>([]);
const limits = ref<Limits | null>(null);
const error = ref("");
const notice = ref("");
const approvalId = ref("");
const id = ref("");
const name = ref("");
const tempMax = ref("");

async function refresh() {
  points.value = await api<Point[]>("/api/v1/points");
  limits.value = await api<Limits>("/api/v1/settings/limits");
  const max = limits.value.limits.temperature_c?.max;
  if (max !== undefined) tempMax.value = String(max);
}

onMounted(async () => {
  try {
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
});

async function createPoint() {
  error.value = "";
  notice.value = "";
  try {
    await api("/api/v1/points", {
      method: "POST",
      body: JSON.stringify({ id: id.value, name: name.value, map_id: "map-01", pose: { x: 0, y: 0 } }),
    });
    id.value = "";
    name.value = "";
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
}

async function removePoint(pointId: string) {
  error.value = "";
  try {
    await api(`/api/v1/points/${pointId}`, { method: "DELETE" });
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
}

async function saveLimit() {
  error.value = "";
  notice.value = "";
  try {
    await api("/api/v1/settings/limits", {
      method: "PATCH",
      body: JSON.stringify({ temperature_c: { max: Number(tempMax.value) } }),
    });
    notice.value = "限值已生效";
    await refresh();
  } catch (e) {
    if (e instanceof ApiError && e.code === "APPROVAL_REQUIRED") {
      approvalId.value = String(e.details?.approval_id || "");
      notice.value = "限值尚未生效，请到批准中心由其他用户签署";
      error.value = "";
      return;
    }
    error.value = messageOf(e);
  }
}
</script>

<template>
  <section>
    <h1>点位 / 限值</h1>
    <p v-if="limits">电子签名：{{ limits.e_sign ? "开启（改限值走批准流）" : "关闭（直接生效）" }}</p>
    <form class="grid" @submit.prevent="createPoint">
      <label>点位 ID <input v-model="id" required /></label>
      <label>名称 <input v-model="name" required /></label>
      <button type="submit">新增点位</button>
    </form>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>名称</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in points" :key="p.id">
          <td>{{ p.id }}</td>
          <td>{{ p.name }}</td>
          <td><button type="button" @click="removePoint(p.id)">删除</button></td>
        </tr>
        <tr v-if="points.length === 0">
          <td colspan="3">暂无点位</td>
        </tr>
      </tbody>
    </table>
    <h2>温度上限（℃）</h2>
    <form class="grid" @submit.prevent="saveLimit">
      <label>max <input v-model="tempMax" type="number" step="0.1" required /></label>
      <button type="submit">保存限值</button>
    </form>
    <p v-if="notice">
      {{ notice }}
      <RouterLink v-if="approvalId" to="/approvals">打开批准中心</RouterLink>
    </p>
    <p v-if="error" class="err">{{ error }}</p>
  </section>
</template>
