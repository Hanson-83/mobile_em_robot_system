import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import MapView from "../views/MapView.vue";
import TasksView from "../views/TasksView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/login" },
    { path: "/login", component: LoginView },
    { path: "/map", component: MapView },
    { path: "/tasks", component: TasksView },
  ],
});
