import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Groups from './pages/Groups'
import Projects from './pages/Projects'
import Stages from './pages/Stages'
import { Submissions, Reviews, Documents } from './pages/Other'
import CreateGroup from './pages/CreateGroup'
import LevelFill from './pages/LevelFill'
import CoverPage from './pages/CoverPage'
import StudentInfo from './pages/StudentInfo'
import HODGroups from './pages/HODGroups'
import HODAllocate from './pages/HODAllocate'
import FacultyEvaluate from './pages/FacultyEvaluate'

const qc = new QueryClient()
function Guard({children}:{children:React.ReactNode}){
  const t = localStorage.getItem('access')
  if(!t) return <Navigate to="/login"/>
  return <>{children}</>
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={qc}>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login/>}/>
        <Route path="/register" element={<Register/>}/>
        <Route path="/" element={<Guard><Layout/></Guard>}>
          <Route index element={<Dashboard/>}/>
          <Route path="groups" element={<Groups/>}/>
          <Route path="create-group" element={<CreateGroup/>}/>
          <Route path="cover" element={<CoverPage/>}/>
          <Route path="student-info" element={<StudentInfo/>}/>
          <Route path="level/:stageId" element={<LevelFill/>}/>
          <Route path="hod/groups" element={<HODGroups/>}/>
          <Route path="hod/allocate" element={<HODAllocate/>}/>
          <Route path="faculty/evaluate" element={<FacultyEvaluate/>}/>
          <Route path="projects" element={<Projects/>}/>
          <Route path="stages" element={<Stages/>}/>
          <Route path="submissions" element={<Submissions/>}/>
          <Route path="reviews" element={<Reviews/>}/>
          <Route path="documents" element={<Documents/>}/>
        </Route>
      </Routes>
    </BrowserRouter>
  </QueryClientProvider>
)
