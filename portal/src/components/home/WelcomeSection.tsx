import { Rocket, Zap, Shield, BarChart3 } from 'lucide-react'

export function WelcomeSection() {
  return (
    <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-xl p-8 border border-blue-100/50 shadow-soft">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 mb-3">
            Welcome to Tron Platform
          </h2>
          <p className="text-slate-700 leading-relaxed mb-4">
            Tron is a comprehensive Kubernetes management platform that simplifies the deployment,
            monitoring, and management of your containerized applications. Manage your applications,
            instances, and components all in one place with an intuitive interface.
          </p>
          <p className="text-slate-600 text-sm">
            Get started by creating your first application or explore the dashboard to see your
            current infrastructure overview.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-white/50">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Rocket className="text-blue-600" size={20} />
              </div>
              <h3 className="text-sm font-semibold text-slate-800">Fast Deployment</h3>
            </div>
            <p className="text-xs text-slate-600">
              Deploy applications to Kubernetes clusters in seconds
            </p>
          </div>
          <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-white/50">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Zap className="text-purple-600" size={20} />
              </div>
              <h3 className="text-sm font-semibold text-slate-800">Auto Scaling</h3>
            </div>
            <p className="text-xs text-slate-600">
              Automatic scaling based on CPU and memory usage
            </p>
          </div>
          <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-white/50">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-green-100 rounded-lg">
                <Shield className="text-green-600" size={20} />
              </div>
              <h3 className="text-sm font-semibold text-slate-800">Secure</h3>
            </div>
            <p className="text-xs text-slate-600">
              Role-based access control and secure token management
            </p>
          </div>
          <div className="bg-white/60 backdrop-blur-sm rounded-lg p-4 border border-white/50">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-orange-100 rounded-lg">
                <BarChart3 className="text-orange-600" size={20} />
              </div>
              <h3 className="text-sm font-semibold text-slate-800">Monitoring</h3>
            </div>
            <p className="text-xs text-slate-600">
              Real-time monitoring of pods, jobs, and application health
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

