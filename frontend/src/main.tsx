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
import Profile from './pages/Profile'
import GroupProfile from './pages/GroupProfile'
import StudentLayout from './layouts/StudentLayout'
import StudentDashboard from './pages/student/Dashboard'
import StudentProfile from './pages/student/Profile'
import StudentGroup from './pages/student/Group'
import Logbook from './pages/student/Logbook'
import LogbookNew from './pages/student/LogbookNew'
import LogbookDetail from './pages/student/LogbookDetail'
import Progress from './pages/student/Progress'
import StudentDocuments from './pages/student/Documents'
import StudentReviews from './pages/student/Reviews'
import StudentNotifications from './pages/student/Notifications'
import FinalLogbook from './pages/student/FinalLogbook'
import FacultyLayout from './layouts/FacultyLayout'
import FacultyDashboard from './pages/faculty/Dashboard'
import FacultyGroups from './pages/faculty/Groups'
import FacultyGroupDetail from './pages/faculty/GroupDetail'
import FacultyLogbook from './pages/faculty/Logbook'
import FacultyLogbookReview from './pages/faculty/LogbookReview'
import FacultyDocuments from './pages/faculty/Documents'
import FacultyEvaluation from './pages/faculty/Evaluation'
import FacultyHistory from './pages/faculty/History'
import FacultyNotifications from './pages/faculty/Notifications'
import FacultyProgress from './pages/faculty/Progress'
import FacultyDeadlines from './pages/faculty/Deadlines'
import FacultyAudit from './pages/faculty/Audit'

const qc = new QueryClient({defaultOptions:{queries:{refetchOnWindowFocus:true, staleTime:0, gcTime:1000*60*5}}})
import { RealtimeProvider } from './contexts/RealtimeContext'
function Guard({children}:{children:React.ReactNode}){
  const t = localStorage.getItem('access')
  if(!t) return <Navigate to="/login"/>
  return <RealtimeProvider>{children}</RealtimeProvider>
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
          <Route path="profile" element={<Profile/>}/>
          <Route path="group-profile" element={<GroupProfile/>}/>
          <Route path="projects" element={<Projects/>}/>
          <Route path="stages" element={<Stages/>}/>
          <Route path="submissions" element={<Submissions/>}/>
          <Route path="reviews" element={<Reviews/>}/>
          <Route path="documents" element={<Documents/>}/>
        </Route>
        <Route path="/student" element={<Guard><StudentLayout/></Guard>}>
          <Route path="dashboard" element={<StudentDashboard/>}/>
          <Route path="profile" element={<StudentProfile/>}/>
          <Route path="group" element={<StudentGroup/>}/>
          <Route path="logbook" element={<Logbook/>}/>
          <Route path="logbook/new" element={<LogbookNew/>}/>
          <Route path="logbook/:id" element={<LogbookDetail/>}/>
          <Route path="progress" element={<Progress/>}/>
          <Route path="documents" element={<StudentDocuments/>}/>
          <Route path="reviews" element={<StudentReviews/>}/>
          <Route path="notifications" element={<StudentNotifications/>}/>
          <Route path="final-logbook" element={<FinalLogbook/>}/>
        </Route>
        <Route path="/faculty" element={<Guard><FacultyLayout role="faculty"/></Guard>}>
          <Route path="dashboard" element={<FacultyDashboard role="faculty"/>}/>
          <Route path="groups" element={<FacultyGroups role="faculty"/>}/>
          <Route path="groups/:id" element={<FacultyGroupDetail role="faculty"/>}/>
          <Route path="logbook" element={<FacultyLogbook role="faculty"/>}/>
          <Route path="logbook/:id" element={<FacultyLogbookReview role="faculty"/>}/>
          <Route path="submissions" element={<FacultyLogbook role="faculty"/>}/>
          <Route path="documents" element={<FacultyDocuments role="faculty"/>}/>
          <Route path="evaluations" element={<FacultyEvaluation role="faculty"/>}/>
          <Route path="progress" element={<FacultyProgress role="faculty"/>}/>
          <Route path="deadlines" element={<FacultyDeadlines role="faculty"/>}/>
          <Route path="notifications" element={<FacultyNotifications role="faculty"/>}/>
          <Route path="history" element={<FacultyHistory role="faculty"/>}/>
          <Route path="audit" element={<FacultyAudit role="faculty"/>}/>
        </Route>
        <Route path="/reviewer" element={<Guard><FacultyLayout role="reviewer"/></Guard>}>
          <Route path="dashboard" element={<FacultyDashboard role="reviewer"/>}/>
          <Route path="groups" element={<FacultyGroups role="reviewer"/>}/>
          <Route path="groups/:id" element={<FacultyGroupDetail role="reviewer"/>}/>
          <Route path="logbook" element={<FacultyLogbook role="reviewer"/>}/>
          <Route path="logbook/:id" element={<FacultyLogbookReview role="reviewer"/>}/>
          <Route path="submissions" element={<FacultyLogbook role="reviewer"/>}/>
          <Route path="documents" element={<FacultyDocuments role="reviewer"/>}/>
          <Route path="evaluations" element={<FacultyEvaluation role="reviewer"/>}/>
          <Route path="progress" element={<FacultyProgress role="reviewer"/>}/>
          <Route path="deadlines" element={<FacultyDeadlines role="reviewer"/>}/>
          <Route path="notifications" element={<FacultyNotifications role="reviewer"/>}/>
          <Route path="history" element={<FacultyHistory role="reviewer"/>}/>
          <Route path="audit" element={<FacultyAudit role="reviewer"/>}/>
        </Route>
      </Routes>
    </BrowserRouter>
  </QueryClientProvider>
)
