<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const title = computed(() => (route.meta.title as string) || "页面");
</script>

<template>
  <section class="card">
    <h1>{{ title }}</h1>
    <p class="hint">页面壳已按 plan §3.1 占位，功能将在 M2–M4 补齐。</p>
  </section>
</template>
