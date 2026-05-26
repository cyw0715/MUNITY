import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  // 管理员端
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('../views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      { path: '', name: 'AdminHome', component: () => import('../views/admin/Home.vue') },
      { path: 'staff', name: 'AdminStaff', component: () => import('../views/admin/StaffManage.vue') },
      { path: 'committees', name: 'AdminCommittees', component: () => import('../views/admin/Committees.vue') }
    ]
  },
  // 学团端
  {
    path: '/staff',
    name: 'StaffLayout',
    component: () => import('../views/staff/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'staff' },
    children: [
      { path: '', name: 'StaffHome', component: () => import('../views/staff/Home.vue') },
      { path: 'delegates', name: 'StaffDelegates', component: () => import('../views/staff/Delegates.vue') },
      { path: 'delegations', name: 'StaffDelegations', component: () => import('../views/staff/Delegations.vue') },
      { path: 'agenda', name: 'StaffAgenda', component: () => import('../views/staff/Agenda.vue') },
      { path: 'rollcall', name: 'StaffRollCall', component: () => import('../views/staff/RollCall.vue') },
      { path: 'meeting', name: 'StaffMeeting', component: () => import('../views/staff/Meeting.vue') },
      { path: 'vote', name: 'StaffVote', component: () => import('../views/staff/Vote.vue') },
      { path: 'directives', name: 'StaffDirectives', component: () => import('../views/staff/Directives.vue') },
      { path: 'documents', name: 'StaffDocuments', component: () => import('../views/staff/Documents.vue') },
      { path: 'updates', name: 'StaffUpdates', component: () => import('../views/staff/Updates.vue') },
      { path: 'records', name: 'StaffRecords', component: () => import('../views/staff/Records.vue') },
      { path: 'archive', name: 'StaffArchive', component: () => import('../views/staff/Archive.vue') },
      { path: 'timeline', name: 'StaffTimeline', component: () => import('../views/staff/Timeline.vue') }
    ]
  },
  // 代表端
  {
    path: '/delegate',
    name: 'DelegateLayout',
    component: () => import('../views/delegate/Dashboard.vue'),
    meta: { requiresAuth: true, role: 'delegate' },
    children: [
      { path: '', name: 'DelegateHome', component: () => import('../views/delegate/Home.vue') },
      { path: 'submit', name: 'DelegateSubmit', component: () => import('../views/delegate/Submit.vue') },
      { path: 'agenda', name: 'DelegateAgenda', component: () => import('../views/delegate/Agenda.vue') },
      { path: 'updates', name: 'DelegateUpdates', component: () => import('../views/delegate/Updates.vue') },
      { path: 'meeting-files', name: 'DelegateMeetingFiles', component: () => import('../views/delegate/MeetingFiles.vue') }
    ]
  },
  { path: '/', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.role && authStore.user?.role !== to.meta.role) {
    next('/login')
  } else {
    next()
  }
})

export default router
