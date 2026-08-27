import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useTitle } from "@vueuse/core";
import NProgress from "nprogress";

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/",
    component: () => import("@/layouts/AuthLayout.vue"),
    children: [
      {
        path: "login",
        name: "Login",
        component: () => import("@/views/auth/Login.vue"),
        meta: { guest: true },
      },
      {
        path: "register",
        name: "Register",
        component: () => import("@/views/auth/Register.vue"),
        meta: { guest: true },
      },
    ],
  },
  {
    path: "/app",
    component: () => import("@/layouts/AppLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "dashboard",
        name: "Dashboard",
        component: () => import("@/views/Dashboard.vue"),
      },
      {
        path: "alumni",
        name: "AlumniList",
        component: () => import("@/views/Alumni.vue"),
      },
      {
        path: "alumni/:id",
        name: "AlumniDetail",
        component: () => import("@/views/AlumniDetail.vue"),
      },
      {
        path: "sources",
        name: "Sources",
        component: () => import("@/views/Sources.vue"),
      },
      {
        path: "profile",
        name: "Profile",
        component: () => import("@/views/Profile.vue"),
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Configure NProgress
NProgress.configure({ showSpinner: false });

router.beforeEach((to, from, next) => {
  NProgress.start();
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated();

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: "Login" });
  } else if (to.meta.guest && isAuthenticated) {
    next({ name: "Dashboard" });
  } else {
    next();
  }
});

router.afterEach((to) => {
  // Dynamic Title
  const title = useTitle();
  const baseTitle = "Sistem Pelacakan Alumni";
  title.value = to.name ? `${to.name} | ${baseTitle}` : baseTitle;

  NProgress.done();
});

export default router;
