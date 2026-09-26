import { createRouter, createWebHistory } from "vue-router";
import { getToken } from "../api/client";
import LoginView from "../views/LoginView.vue";
import MapView from "../views/MapView.vue";
import TasksView from "../views/TasksView.vue";
import PointsView from "../views/PointsView.vue";
import TrendsView from "../views/TrendsView.vue";
import AlarmsView from "../views/AlarmsView.vue";
import ReportsView from "../views/ReportsView.vue";
import UsersView from "../views/UsersView.vue";
import SettingsView from "../views/SettingsView.vue";
import ApprovalsView from "../views/ApprovalsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/map" },
    { path: "/login", component: LoginView },
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
  if (to.path !== "/login" && !getToken()) return "/login";
  if (to.path === "/login" && getToken()) return "/map";
  return true;
});
