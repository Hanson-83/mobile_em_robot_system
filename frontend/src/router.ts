import { createRouter, createWebHistory } from "vue-router";

import { token } from "./api";
import AlarmsView from "./views/AlarmsView.vue";
import ApprovalsView from "./views/ApprovalsView.vue";
import LoginView from "./views/LoginView.vue";
import MapView from "./views/MapView.vue";
import PointsView from "./views/PointsView.vue";
import ReportsView from "./views/ReportsView.vue";
import SettingsView from "./views/SettingsView.vue";
import TasksView from "./views/TasksView.vue";
import TrendsView from "./views/TrendsView.vue";
import UsersView from "./views/UsersView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: LoginView },
    { path: "/", redirect: "/map" },
    { path: "/map", component: MapView },
    { path: "/tasks", component: TasksView },
    { path: "/points", component: PointsView },
    { path: "/trends", component: TrendsView },
    { path: "/alarms", component: AlarmsView },
    { path: "/reports", component: ReportsView },
    { path: "/users", component: UsersView },
    { path: "/settings", component: SettingsView },
    { path: "/approvals", component: ApprovalsView },
  ],
});

router.beforeEach((to) => {
  if (to.path !== "/login" && !token()) {
    return "/login";
  }
  if (to.path === "/login" && token()) {
    return "/map";
  }
  return true;
});

export default router;
