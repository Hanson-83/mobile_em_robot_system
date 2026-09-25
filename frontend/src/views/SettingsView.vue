<script setup lang="ts">
import { onMounted, ref } from "vue";

import { api } from "../api";

interface Features {
  audit_trail: boolean;
  e_sign: boolean;
  elevator_skills: boolean;
  fail_on_disconnect: boolean;
  resource_mutex_on_conflict: string;
  realtime_channel: string;
  resource_mutex: string;
  auto_backup_interval_minutes: number;
}

const features = ref<Features>({
  audit_trail: false,
  e_sign: false,
  elevator_skills: true,
  fail_on_disconnect: true,
  resource_mutex_on_conflict: "queue",
  realtime_channel: "websocket",
  resource_mutex: "simple",
  auto_backup_interval_minutes: 60,
});
const message = ref("");

async function load(): Promise<void> {
  features.value = await api<Features>("/api/v1/settings/features");
}

async function save(): Promise<void> {
  features.value = await api<Features>("/api/v1/settings/features", {
    method: "PATCH",
    body: JSON.stringify({
      audit_trail: Boolean(features.value.audit_trail),
      e_sign: Boolean(features.value.e_sign),
      elevator_skills: Boolean(features.value.elevator_skills),
      fail_on_disconnect: Boolean(features.value.fail_on_disconnect),
      resource_mutex_on_conflict: features.value.resource_mutex_on_conflict,
      auto_backup_interval_minutes: Number(features.value.auto_backup_interval_minutes),
    }),
  });
  message.value = "已保存";
}

onMounted(() => {
  void load();
});
</script>

<template>
  <section>
    <h2>系统开关</h2>
    <form class="card" @submit.prevent="save">
      <p><label><input v-model="features.audit_trail" type="checkbox" /> 审计追踪 audit_trail</label></p>
      <p><label><input v-model="features.e_sign" type="checkbox" /> 电子签名 e_sign（开启后限值与报告走批准流）</label></p>
      <p><label><input v-model="features.elevator_skills" type="checkbox" /> 电梯技能 elevator_skills</label></p>
      <p><label><input v-model="features.fail_on_disconnect" type="checkbox" /> 断线则任务失败</label></p>
      <p>
        <label>
          资源冲突策略
          <select v-model="features.resource_mutex_on_conflict">
            <option value="queue">排队</option>
            <option value="fail">立即失败</option>
          </select>
        </label>
      </p>
      <button type="submit">保存</button>
      <p v-if="message" class="ok">{{ message }}</p>
      <p>
        <label>
          自动备份间隔（分钟，0 为关闭）
          <input v-model.number="features.auto_backup_interval_minutes" type="number" min="0" step="1" />
        </label>
      </p>
      <p class="muted">实时通道锁定为 {{ features.realtime_channel }}。互斥模式 {{ features.resource_mutex }}。权限变更在下次登录后生效。</p>
    </form>
  </section>
</template>
