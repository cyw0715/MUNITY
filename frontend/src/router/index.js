import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ensureCommitteeFeatures } from '../composables/useCommitteeFeatures'

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
      { path: 'motion-types', name: 'StaffMotionTypes', component: () => import('../views/staff/MotionTypes.vue') },
      { path: 'document-types', name: 'StaffDocumentTypes', component: () => import('../views/staff/DocumentTypes.vue') },
      { path: 'async-messages', name: 'StaffAsyncMessages', component: () => import('../views/staff/AsyncMessages.vue'), meta: { feature: 'updates' } },
      { path: 'directives', name: 'StaffDirectives', component: () => import('../views/staff/Directives.vue'), meta: { feature: 'directives' } },
      { path: 'documents', name: 'StaffDocuments', component: () => import('../views/staff/Documents.vue') },
      { path: 'updates', name: 'StaffUpdates', component: () => import('../views/staff/Updates.vue'), meta: { feature: 'updates' } },
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
      { path: 'submit', redirect: '/delegate/submit-document' },
      {
        path: 'submit-directive',
        name: 'DelegateSubmitDirective',
        component: () => import('../views/delegate/Submit.vue'),
        props: { mode: 'directive' },
        // 未启用「指令管理」的会场不提供提交指令入口
        meta: { feature: 'directives' },
      },
      {
        path: 'submit-document',
        name: 'DelegateSubmitDocument',
        component: () => import('../views/delegate/Submit.vue'),
        props: { mode: 'document' },
      },
      { path: 'async-messages', name: 'DelegateAsyncMessages', component: () => import('../views/delegate/AsyncMessages.vue'), meta: { feature: 'updates' } },
      { path: 'agenda', name: 'DelegateAgenda', component: () => import('../views/delegate/Agenda.vue') },
      { path: 'updates', name: 'DelegateUpdates', component: () => import('../views/delegate/Updates.vue'), meta: { feature: 'updates' } },
      { path: 'meeting-files', name: 'DelegateMeetingFiles', component: () => import('../views/delegate/MeetingFiles.vue') },
      { path: 'endorsements', name: 'DelegateEndorsements', component: () => import('../views/delegate/Endorsements.vue') }
    ]
  },
  { path: '/', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
    return
  }
  if (to.meta.role && authStore.user?.role !== to.meta.role) {
    next('/login')
    return
  }

  // 按会场功能开关拦截：直接输入 URL 也不放行（后端另有 require_feature 兜底）
  if (to.meta.feature && authStore.user?.role !== 'admin') {
    const role = authStore.user?.role
    const features = await ensureCommitteeFeatures(role, authStore.user?.id)
    if (features !== null && !features.includes(to.meta.feature)) {
      const home = { admin: '/admin', staff: '/staff', delegate: '/delegate' }[role] || '/login'
      next(to.path === home ? undefined : home)
      return
    }
  }

  next()
})

export default router
