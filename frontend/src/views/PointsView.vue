<script setup lang="ts">
import { onMounted, ref } from "vue";

import { ApiError, api } from "../api";

interface Point {
  id: string;
  name: string;
  map_id: string;
  pose: { x: number; y: number; theta: number };
  limits: Record<string, { min?: number; max?: number; unit?: string }>;
}

const points = ref<Point[]>([]);
const message = ref("");
const form = ref({ id: "", name: "", x: 1, y: 1, maxParticle: 1000 });

async function load(): Promise<void> {
  const body = await api<{ items: Point[] }>("/api/v1/points");
  points.value = body.items;
}

async function createPoint(): Promise<void> {
  message.value = "";
  await api("/api/v1/points", {
    method: "POST",
    body: JSON.stringify({
      id: form.value.id,
      map_id: "map-demo",
      name: form.value.name,
      pose: { x: form.value.x, y: form.value.y, theta: 0 },
      limits: { "particle.0.5um": { max: form.value.maxParticle, unit: "counts" } },
    }),
  });
  await load();
}

async function saveLimits(point: Point): Promise<void> {
  message.value = "";
  try {
    await api(`/api/v1/settings/limits`, {
      method: "PATCH",
      body: JSON.stringify({ point_id: point.id, limits: point.limits }),
    });
    message.value = `${point.id} 限值已更新`;
  } catch (err) {
    if (err instanceof ApiError && err.code === "APPROVAL_REQUIRED") {
      message.value = `已提交批准请求 ${String(err.details.approval_id ?? "")}`;
      return;
    }
    message.value = err instanceof Error ? err.message : "更新失败";
  }
}

async function remove(id: string): Promise<void> {
  try {
    await api(`/api/v1/points/${id}`, { method: "DELETE" });
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "删除失败";
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section>
    <h2>点位 / 限值</h2>
    <p v-if="message">{{ message }}</p>
    <form class="card row" @submit.prevent="createPoint">
      <label>编号 <input v-model="form.id" required /></label>
      <label>名称 <input v-model="form.name" required /></label>
      <label>X <input v-model.number="form.x" type="number" step="0.1" /></label>
      <label>Y <input v-model.number="form.y" type="number" step="0.1" /></label>
      <label>0.5μm 上限 <input v-model.number="form.maxParticle" type="number" /></label>
      <button type="submit">新增点位</button>
    </form>
    <article class="card">
      <table>
        <thead>
          <tr><th>点位</th><th>坐标</th><th>0.5μm 上限</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="point in points" :key="point.id">
            <td>{{ point.name }} ({{ point.id }})</td>
            <td>{{ point.pose.x }}, {{ point.pose.y }}</td>
            <td>
              <input
                v-if="point.limits['particle.0.5um']"
                v-model.number="point.limits['particle.0.5um'].max"
                type="number"
              />
            </td>
            <td>
              <button type="button" @click="saveLimits(point)">保存限值</button>
              <button class="secondary" type="button" @click="remove(point.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>
