<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf } from "../api/client";

type Features = {
  audit_trail: boolean;
  e_sign: boolean;
  elevator_skills: boolean;
  session_on_disconnect: string;
  on_conflict: string;
};

const features = ref<Features | null>(null);
const error = ref("");
const notice = ref("");

async function load() {
  features.value = await api<Features>("/api/v1/settings/features");
}

onMounted(async () => {
  try {
    await load();
  } catch (e) {
    error.value = messageOf(e);
  }
});

async function save() {
  if (!features.value) return;
  error.value = "";
  notice.value = "";
  try {
    features.value = await api<Features>("/api/v1/settings/features", {
      method: "PATCH",
      body: JSON.stringify({
        audit_trail: features.value.audit_trail,
        e_sign: features.value.e_sign,
      }),
    });
    notice.value = "已保存";
  } catch (e) {
    error.value = messageOf(e);
  }
}
</script>

<template>
  <section>
    <h1>系统开关</h1>
    <form v-if="features" class="grid" @submit.prevent="save">
      <label><input v-model="features.audit_trail" type="checkbox" /> 审计追踪 audit_trail</label>
      <label><input v-model="features.e_sign" type="checkbox" /> 电子签名 e_sign（开启后改限值须批准）</label>
      <p>电梯技能：{{ features.elevator_skills }}；断线：{{ features.session_on_disconnect }}；冲突：{{ features.on_conflict }}</p>
      <button type="submit">保存</button>
    </form>
    <p v-if="notice">{{ notice }}</p>
    <p v-if="error" class="err">{{ error }}</p>
  </section>
</template>
