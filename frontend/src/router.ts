import { createRouter, createWebHistory } from "vue-router";
import { getToken } from "./api/client";
import LoginView from "./views/LoginView.vue";
import MapView from "./views/MapView.vue";
import TasksView from "./views/TasksView.vue";
import PlaceholderView from "./views/PlaceholderView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView },
    { path: "/", redirect: "/map" },
    { path: "/map", component: MapView, meta: { auth: true } },
    { path: "/tasks", component: TasksView, meta: { auth: true } },
    { path: "/points", component: PlaceholderView, meta: { auth: true, title: "点位/限值" } },
    { path: "/trends", component: PlaceholderView, meta: { auth: true, title: "实时趋势" } },
    { path: "/alarms", component: PlaceholderView, meta: { auth: true, title: "报警" } },
    { path: "/reports", component: PlaceholderView, meta: { auth: true, title: "报告" } },
    { path: "/users", component: PlaceholderView, meta: { auth: true, title: "用户权限" } },
    { path: "/features", component: PlaceholderView, meta: { auth: true, title: "系统开关" } },
    { path: "/approvals", component: PlaceholderView, meta: { auth: true, title: "批准中心" } },
  ],
});

router.beforeEach((to) => {
  if (to.meta.auth && !getToken()) {
    return "/login";
  }
  return true;
});
