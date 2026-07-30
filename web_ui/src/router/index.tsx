import { createBrowserRouter, Navigate, Link } from 'react-router-dom'
import { lazy } from 'react'
import Login from '../views/Login'

// 登录页保持同步加载，确保未登录用户能尽快看到首屏；其余页面按路由加载，
// 避免登录页被图表、编辑器及后台管理页面的依赖阻塞。
const NotFound = lazy(() => import('../views/NotFound'))
const BasicLayout = lazy(() => import('../components/Layout/BasicLayout'))
const ExportRecords = lazy(() => import('../views/ExportRecords'))
const ArticleListPage = lazy(() => import('../views/ArticleListPage'))
const ChangePassword = lazy(() => import('../views/ChangePassword'))
const EditUser = lazy(() => import('../views/EditUser'))
const AddSubscription = lazy(() => import('../views/AddSubscription'))
const WeChatMpManagement = lazy(() => import('../views/WeChatMpManagement'))
const SubscriptionManagement = lazy(() => import('../views/SubscriptionManagement'))
const ConfigList = lazy(() => import('../views/ConfigList'))
const ConfigDetail = lazy(() => import('../views/ConfigDetail'))
const MessageTaskList = lazy(() => import('../views/MessageTaskList'))
const MessageTaskForm = lazy(() => import('../views/MessageTaskForm'))
const FetchTaskList = lazy(() => import('../views/FetchTaskList'))
const FetchTaskForm = lazy(() => import('../views/FetchTaskForm'))
const NotifyTaskList = lazy(() => import('../views/NotifyTaskList'))
const NotifyTaskForm = lazy(() => import('../views/NotifyTaskForm'))
const SystemTaskList = lazy(() => import('../views/SystemTaskList'))
const NovelReader = lazy(() => import('../views/NovelReader'))
const SysInfo = lazy(() => import('../views/SysInfo'))
const TagList = lazy(() => import('../views/TagList'))
const TagForm = lazy(() => import('../views/TagForm'))
const TagClusterList = lazy(() => import('../views/TagClusterList'))
const TagClusterDetail = lazy(() => import('../views/TagClusterDetail'))
const HotTopics = lazy(() => import('../views/HotTopics'))
const Dashboard = lazy(() => import('../views/Dashboard'))
const Settings = lazy(() => import('../views/Settings'))
const ApiKeyManagement = lazy(() => import('../views/ApiKeyManagement'))
// import { verifyToken } from '@/api/auth'

// 路由守卫组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token')
  
  if (!token) {
    const currentPath = window.location.pathname + window.location.search
    return <Navigate to={`/login?redirect=${encodeURIComponent(currentPath)}`} replace />
  }
  
  return <>{children}</>
}

// 权限检查组件
const PermissionRoute = ({ 
  children, 
  permissions: _permissions
}: { 
  children: React.ReactNode
  permissions?: string[] 
}) => {
  // 这里可以添加权限检查逻辑
  return <>{children}</>
}

const router = createBrowserRouter(
  [
  {
    path: '/login',
    element: <Login />
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <BasicLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <ArticleListPage />
      },
      {
        path: 'articles',
        element: <ArticleListPage />
      },
      {
        path: 'subscriptions',
        element: <SubscriptionManagement />
      },
      {
        path: 'subscriptions/:id',
        element: <SubscriptionManagement />
      },
      {
        path: 'dashboard',
        element: <Dashboard />
      },
      {
        path: 'change-password',
        element: <ChangePassword />
      },
      {
        path: 'edit-user',
        element: <EditUser />
      },
      {
        path: 'settings',
        element: <Settings />
      },
      {
        path: 'add-subscription',
        element: <AddSubscription />
      },
      {
        path: 'wechat/mp',
        element: (
          <PermissionRoute permissions={['wechat:manage']}>
            <WeChatMpManagement />
          </PermissionRoute>
        )
      },
      {
        path: 'configs',
        element: (
          <PermissionRoute permissions={['config:view']}>
            <ConfigList />
          </PermissionRoute>
        )
      },
      {
        path: 'export/records',
        element: (
          <PermissionRoute permissions={['config:view']}>
            <ExportRecords />
          </PermissionRoute>
        )
      },
      {
        path: 'configs/:key',
        element: (
          <PermissionRoute permissions={['config:view']}>
            <ConfigDetail />
          </PermissionRoute>
        )
      },
      {
        path: 'message-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <MessageTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'message-tasks/add',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <MessageTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'message-tasks/edit/:id',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <MessageTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'system-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <SystemTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'fetch-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <FetchTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'fetch-tasks/add',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <FetchTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'fetch-tasks/edit/:id',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <FetchTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'notify-tasks',
        element: (
          <PermissionRoute permissions={['message_task:view']}>
            <NotifyTaskList />
          </PermissionRoute>
        )
      },
      {
        path: 'notify-tasks/add',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <NotifyTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'notify-tasks/edit/:id',
        element: (
          <PermissionRoute permissions={['message_task:edit']}>
            <NotifyTaskForm />
          </PermissionRoute>
        )
      },
      {
        path: 'sys-info',
        element: (
          <PermissionRoute permissions={['admin']}>
            <SysInfo />
          </PermissionRoute>
        )
      },
      {
        path: 'tags',
        element: (
          <PermissionRoute permissions={['tag:view']}>
            <TagList />
          </PermissionRoute>
        )
      },
      {
        path: 'tags/add',
        element: (
          <PermissionRoute permissions={['tag:edit']}>
            <TagForm />
          </PermissionRoute>
        )
      },
      {
        path: 'tags/edit/:id',
        element: (
          <PermissionRoute permissions={['tag:edit']}>
            <TagForm />
          </PermissionRoute>
        )
      },
      {
        path: 'tag-clusters',
        element: (
          <PermissionRoute permissions={['tag:view']}>
            <TagClusterList />
          </PermissionRoute>
        )
      },
      {
        path: 'tag-clusters/:id',
        element: (
          <PermissionRoute permissions={['tag:view']}>
            <TagClusterDetail />
          </PermissionRoute>
        )
      },
      {
        path: 'hot-topics',
        element: <HotTopics />
      },
      {
        path: 'api-keys',
        element: (
          <PermissionRoute permissions={['admin']}>
            <ApiKeyManagement />
          </PermissionRoute>
        ),
        errorElement: (
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-4">错误</h1>
              <p className="text-muted-foreground mb-4">加载 API Key 管理页面时出错</p>
              <Link to="/" className="text-primary hover:underline">返回首页</Link>
            </div>
          </div>
        )
      },
      {
        path: '*',
        element: <NotFound />
      }
    ]
  },
  {
    path: '/reader',
    element: (
      <ProtectedRoute>
        <NovelReader />
      </ProtectedRoute>
    )
  }
  ],
  {
    future: {
      v7_relativeSplatPath: true,
    },
  }
)

export default router
