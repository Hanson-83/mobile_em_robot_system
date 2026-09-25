<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api";

interface Approval {
  id: string;
  action: string;
  state: string;
  object_ref: string;
  requester: string;
  expires_at: string;
}

const items = ref<Approval[]>([]);
const password = ref("");
const meaning = ref("确认变更");
const message = ref("");

async function load(): Promise<void> {
  items.value = (await api<{ items: Approval[] }>("/api/v1/approvals")).items;
}

async function decide(id: string, action: "approve" | "reject"): Promise<void> {
  message.value = "";
  try {
    await api(`/api/v1/approvals/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify({ password: password.value, meaning: meaning.value }),
    });
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "审批失败";
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section>
    <h2>批准中心</h2>
    <p class="muted">仅在电子签名开启后，限值变更和报告批准会进入此列表。审批需再次输入口令作为签名。</p>
    <div class="card row">
      <label>签名口令 <input v-model="password" type="password" /></label>
      <label>含义 <input v-model="meaning" /></label>
      <button type="button" @click="load">刷新</button>
    </div>
    <p v-if="message" class="error">{{ message }}</p>
    <article class="card">
      <table>
        <thead>
          <tr><th>对象</th><th>动作</th><th>状态</th><th>发起人</th><th>到期</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.object_ref }}</td>
            <td>{{ item.action }}</td>
            <td>{{ item.state }}</td>
            <td>{{ item.requester }}</td>
            <td>{{ item.expires_at }}</td>
            <td v-if="item.state === 'Pending'">
              <button type="button" @click="decide(item.id, 'approve')">批准</button>
              <button class="danger" type="button" @click="decide(item.id, 'reject')">驳回</button>
            </td>
            <td v-else></td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>
