import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AdminRoute } from './components/AdminRoute'
import Layout from './components/Layout'
import Home from './pages/home'
import Login from './pages/Login'
import Clusters from './pages/clusters/Clusters'
import Environments from './pages/environments/Environments'
import Applications from './pages/applications/Applications'
import CreateApplication from './pages/applications/CreateApplication'
import CreateInstance from './pages/applications/CreateInstance'
import InstanceDetail from './pages/applications/InstanceDetail'
import InstanceEvents from './pages/applications/InstanceEvents'
import WebappDetail from './pages/applications/WebappDetail'
import CronDetail from './pages/applications/CronDetail'
import Templates from './pages/templates/Templates'
import Profile from './pages/Profile'
import Users from './pages/users/Users'
import Tokens from './pages/tokens/Tokens'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="clusters" element={<ProtectedRoute><AdminRoute><Clusters /></AdminRoute></ProtectedRoute>} />
          <Route path="environments" element={<ProtectedRoute><AdminRoute><Environments /></AdminRoute></ProtectedRoute>} />
          <Route path="applications" element={<ProtectedRoute><Applications /></ProtectedRoute>} />
          <Route path="applications/new" element={<ProtectedRoute><CreateApplication /></ProtectedRoute>} />
          <Route path="applications/:uuid/instances/new" element={<ProtectedRoute><CreateInstance /></ProtectedRoute>} />
          <Route path="applications/:uuid/instances/:instanceUuid/components" element={<ProtectedRoute><InstanceDetail /></ProtectedRoute>} />
          <Route path="applications/:uuid/instances/:instanceUuid/events" element={<ProtectedRoute><InstanceEvents /></ProtectedRoute>} />
          <Route path="applications/:uuid/instances/:instanceUuid/components/:componentUuid" element={<ProtectedRoute><WebappDetail /></ProtectedRoute>} />
          <Route path="applications/:uuid/instances/:instanceUuid/components/:componentUuid/executions" element={<ProtectedRoute><CronDetail /></ProtectedRoute>} />
          <Route path="templates" element={<ProtectedRoute><AdminRoute><Templates /></AdminRoute></ProtectedRoute>} />
          <Route path="users" element={<ProtectedRoute><AdminRoute><Users /></AdminRoute></ProtectedRoute>} />
          <Route path="tokens" element={<ProtectedRoute><AdminRoute><Tokens /></AdminRoute></ProtectedRoute>} />
          <Route path="profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App

