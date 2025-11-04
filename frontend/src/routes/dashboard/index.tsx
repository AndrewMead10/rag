import { createFileRoute, redirect } from '@tanstack/react-router'
import { usePageData } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, Activity, Clock } from 'lucide-react'
import type { DashboardData } from '@/lib/types'
import { api } from '@/lib/api'
import { queryClient } from '@/routes/__root'

export const Route = createFileRoute('/dashboard/')({
  beforeLoad: async () => {
    try {
      await queryClient.ensureQueryData({
        queryKey: ['user'],
        queryFn: api.auth.getCurrentUser,
      })
      return {}
    } catch {
      throw redirect({ to: '/auth/login', search: { redirect: undefined } })
    }
  },
  component: DashboardPage,
})

function DashboardPage() {
  const { data, isLoading, error } = usePageData('dashboard')

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="text-center">Loading...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="text-center text-red-600">
            Error loading dashboard: {String((error as any)?.message || 'Unknown error')}
          </div>
        </div>
      </div>
    )
  }

  const dashboardData = data as DashboardData

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData.system_metrics.total_users}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData.system_metrics.active_users}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pending Resets</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData.system_metrics.pending_resets}
                </div>
              </CardContent>
            </Card>
          </div>
          
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
              <CardDescription>Your account details and status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Email:</span> {dashboardData.user_stats.email}
                </div>
                <div>
                  <span className="font-medium">User ID:</span> {dashboardData.user_stats.user_id}
                </div>
                <div>
                  <span className="font-medium">Account Created:</span>{' '}
                  {new Date(dashboardData.user_stats.account_created).toLocaleDateString()}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
  )
}
