import {
  Cloud,
  Globe,
  AppWindow,
  Server,
  Box,
} from 'lucide-react'
import { useDashboardOverview } from '../../features/dashboard'
import { Breadcrumbs, PageHeader } from '../../shared/components'
import { useAuth } from '../../contexts/AuthContext'
import {
  ComponentsOverview,
  StatsGrid,
  ComponentsByEnvironment,
  ComponentsByCluster,
  WelcomeSection,
} from '../../components/home'

function Home() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const { data: dashboard, isLoading } = useDashboardOverview()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!dashboard) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'Home', path: '/' }]} />
        <div className="text-center py-8 text-slate-500">
          <p>No data available</p>
        </div>
      </div>
    )
  }

  const stats = [
    ...(isAdmin ? [
      {
        label: 'Clusters',
        value: dashboard.clusters,
        icon: Cloud,
        path: '/clusters',
        bgColor: 'bg-blue-50',
        iconColor: 'text-blue-600',
        borderColor: 'border-blue-100',
        description: 'Kubernetes clusters managed by the platform. Each cluster can host multiple applications and components.'
      },
      {
        label: 'Environments',
        value: dashboard.environments,
        icon: Globe,
        path: '/environments',
        bgColor: 'bg-indigo-50',
        iconColor: 'text-indigo-600',
        borderColor: 'border-indigo-100',
        description: 'Logical environments (production, staging, development) that organize your applications and instances.'
      },
    ] : []),
    {
      label: 'Applications',
      value: dashboard.applications,
      icon: AppWindow,
      path: '/applications',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
      borderColor: 'border-purple-100',
      description: 'Your deployed applications. Each application can have multiple instances across different environments.'
    },
    {
      label: 'Instances',
      value: dashboard.instances,
      icon: Server,
      path: '/applications',
      bgColor: 'bg-green-50',
      iconColor: 'text-green-600',
      borderColor: 'border-green-100',
      description: 'Application instances running in specific environments. Each instance contains one or more components.'
    },
    {
      label: 'Components',
      value: dashboard.components.total,
      icon: Box,
      path: '/applications',
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600',
      borderColor: 'border-orange-100',
      description: 'Total components deployed across all instances. Includes webapps, workers, and cron jobs.'
    },
  ]

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Home', path: '/' },
        ]}
      />

      <PageHeader title="Dashboard" description="Tron platform overview" />

      <WelcomeSection />

      <StatsGrid stats={stats} />

      <ComponentsOverview components={dashboard.components} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ComponentsByEnvironment componentsByEnvironment={dashboard.components_by_environment} />
        {isAdmin && (
          <ComponentsByCluster componentsByCluster={dashboard.components_by_cluster} />
        )}
      </div>
    </div>
  )
}

export default Home

