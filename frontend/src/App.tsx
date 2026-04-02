import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AppLayout } from '@/components/AppLayout'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { CatalogPage } from '@/pages/CatalogPage'
import { CategoryDetailPage } from '@/pages/CategoryDetailPage'
import { CategoryFormPage } from '@/pages/CategoryFormPage'
import { VarietyDetailPage } from '@/pages/VarietyDetailPage'
import { VarietyFormPage } from '@/pages/VarietyFormPage'
import { ContainersPage } from '@/pages/ContainersPage'
import { ContainerDetailPage } from '@/pages/ContainerDetailPage'
import { ContainerFormPage } from '@/pages/ContainerFormPage'
import { PlantingDetailPage } from '@/pages/PlantingDetailPage'
import { GardenOverviewPage } from '@/pages/GardenOverviewPage'
import { TimelinePage } from '@/pages/TimelinePage'
import { TasksPage } from '@/pages/TasksPage'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/overview" element={<GardenOverviewPage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/catalog" element={<CatalogPage />} />
            <Route path="/catalog/categories/new" element={<CategoryFormPage />} />
            <Route path="/catalog/categories/:id" element={<CategoryDetailPage />} />
            <Route path="/catalog/categories/:id/edit" element={<CategoryFormPage />} />
            <Route path="/catalog/varieties/new" element={<VarietyFormPage />} />
            <Route path="/catalog/varieties/:id" element={<VarietyDetailPage />} />
            <Route path="/catalog/varieties/:id/edit" element={<VarietyFormPage />} />
            <Route path="/containers" element={<ContainersPage />} />
            <Route path="/containers/new" element={<ContainerFormPage />} />
            <Route path="/containers/:id" element={<ContainerDetailPage />} />
            <Route path="/containers/:id/edit" element={<ContainerFormPage />} />
            <Route path="/plantings/:id" element={<PlantingDetailPage />} />
            <Route path="/tasks" element={<TasksPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
