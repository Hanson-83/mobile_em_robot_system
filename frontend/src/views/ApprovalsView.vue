<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf } from "../api/client";

type Approval = {
  id: string;
  state: string;
  action?: string;
  requester?: string;
  meaning?: string;
};

const items = ref<Approval[]>([]);
const error = ref("");
const password = ref("");
const meaning = ref("确认");

async function refresh() {
  items.value = await api<Approval[]>("/api/v1/approvals");
}

onMounted(async () => {
  try {
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
});

async function decide(id: string, decision: "approved" | "rejected") {
  error.value = "";
  try {
    await api(`/api/v1/approvals/${id}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision, password: password.value, meaning: meaning.value }),
    });
    await refresh();
  } catch (e) {
    error.value = messageOf(e);
  }
}
</script>

<template>
  <section>
    <h1>批准中心</h1>
    <p>签名开启后，限值变更出现在这里。审批人不能是发起人，并需再次输入口令。</p>
    <form class="grid">
      <label>签署口令 <input v-model="password" type="password" /></label>
      <label>含义 <input v-model="meaning" /></label>
    </form>
    <p v-if="error" class="err">{{ error }}</p>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>状态</th>
          <th>动作</th>
          <th>发起人</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in items" :key="a.id">
          <td>{{ a.id }}</td>
          <td>{{ a.state }}</td>
          <td>{{ a.action }}</td>
          <td>{{ a.requester }}</td>
          <td v-if="a.state === 'Pending'">
            <button type="button" @click="decide(a.id, 'approved')">批准</button>
            <button type="button" @click="decide(a.id, 'rejected')">驳回</button>
          </td>
          <td v-else></td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="5">暂无批准请求</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
