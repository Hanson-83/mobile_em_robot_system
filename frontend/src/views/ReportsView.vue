<script setup lang="ts">
import { onMounted, ref } from "vue";

import { ApiError, api } from "../api";

interface Report {
  id: string;
  task_ref: string;
  format: string;
  generated_at: string;
  summary: Record<string, unknown>;
  html?: string;
}

const reports = ref<Report[]>([]);
const selected = ref("");
const message = ref("");

async function load(): Promise<void> {
  const body = await api<{ items: Report[] }>("/api/v1/reports");
  reports.value = body.items;
}

async function open(id: string): Promise<void> {
  const report = await api<Report>(`/api/v1/reports/${id}`);
  selected.value = report.html ?? "";
}

async function approve(id: string): Promise<void> {
  message.value = "";
  try {
    await api(`/api/v1/reports/${id}/approve`, { method: "POST" });
    message.value = "报告已标记批准";
    await load();
  } catch (err) {
    if (err instanceof ApiError && err.code === "APPROVAL_REQUIRED") {
      message.value = `需到批准中心处理 ${String(err.details.approval_id ?? "")}`;
      return;
    }
    message.value = err instanceof Error ? err.message : "批准失败";
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section>
    <h2>批报告</h2>
    <p v-if="message">{{ message }}</p>
    <article class="card">
      <table>
        <thead>
          <tr><th>任务</th><th>格式</th><th>时间</th><th>已批准</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="report in reports" :key="report.id">
            <td>{{ report.task_ref.slice(0, 10) }}</td>
            <td>{{ report.format }}</td>
            <td>{{ report.generated_at }}</td>
            <td>{{ report.summary.approved ? "是" : "否" }}</td>
            <td>
              <button type="button" @click="open(report.id)">查看</button>
              <button class="secondary" type="button" @click="approve(report.id)">批准</button>
            </td>
          </tr>
        </tbody>
      </table>
    </article>
    <article v-if="selected" class="card">
      <div v-html="selected"></div>
    </article>
  </section>
</template>
