import { Project, Issue, Agent, PullRequest, Specification } from './types'

export const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Orion Platform',
    description: 'Next-gen AI platform',
    status: 'active',
    tags: ['Production', 'High Priority'],
    issueCount: 28,
    prCount: 12,
    specCount: 15,
  },
  {
    id: '2',
    name: 'Analytics Dashboard',
    description: 'Real-time metrics and insights',
    status: 'active',
    tags: ['Analytics', 'Frontend'],
    issueCount: 15,
    prCount: 8,
    specCount: 10,
  },
  {
    id: '3',
    name: 'Mobile App',
    description: 'iOS and Android apps',
    status: 'active',
    tags: ['Mobile', 'Cross-platform'],
    issueCount: 22,
    prCount: 6,
    specCount: 12,
  },
]

export const mockIssues: Issue[] = [
  {
    id: '1',
    number: 54,
    title: 'Implement authentication flow',
    status: 'in_progress',
    priority: 'high',
    assignee: 'Codegen Agent',
    labels: ['backend', 'auth'],
    projectId: '1',
  },
  {
    id: '2',
    number: 55,
    title: 'Design user dashboard',
    status: 'todo',
    priority: 'medium',
    assignee: 'Design Agent',
    labels: ['frontend', 'ui'],
    projectId: '1',
  },
  {
    id: '3',
    number: 56,
    title: 'Write API documentation',
    status: 'review',
    priority: 'low',
    assignee: 'Doc Agent',
    labels: ['docs'],
    projectId: '1',
  },
  {
    id: '4',
    number: 57,
    title: 'Fix payment integration bug',
    status: 'done',
    priority: 'high',
    assignee: 'Debug Agent',
    labels: ['bug', 'payment'],
    projectId: '1',
  },
]

export const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'Chief Architect',
    role: 'System Design',
    skills: ['Architecture', 'Planning', 'Database Design'],
    status: 'active',
    tasksCompleted: 42,
    successRate: 94,
  },
  {
    id: '2',
    name: 'Codegen Agent',
    role: 'Code Generation',
    skills: ['TypeScript', 'React', 'Node.js'],
    status: 'busy',
    tasksCompleted: 156,
    successRate: 89,
  },
  {
    id: '3',
    name: 'Test Engineer',
    role: 'Quality Assurance',
    skills: ['Testing', 'Automation', 'E2E'],
    status: 'idle',
    tasksCompleted: 78,
    successRate: 96,
  },
  {
    id: '4',
    name: 'Doc Agent',
    role: 'Documentation',
    skills: ['Writing', 'API Docs', 'Tutorials'],
    status: 'active',
    tasksCompleted: 34,
    successRate: 92,
  },
]

export const mockPRs: PullRequest[] = [
  {
    id: '1',
    number: 104,
    title: 'Add user authentication',
    status: 'open',
    author: 'Codegen Agent',
    createdAt: '2024-01-15T10:30:00Z',
    projectId: '1',
  },
  {
    id: '2',
    number: 103,
    title: 'Update dependencies',
    status: 'merged',
    author: 'Maintenance Agent',
    createdAt: '2024-01-14T14:20:00Z',
    projectId: '1',
  },
]

export const mockSpecs: Specification[] = [
  {
    id: '1',
    title: 'Authentication System Spec',
    status: 'approved',
    author: 'Chief Architect',
    createdAt: '2024-01-10T09:00:00Z',
    projectId: '1',
  },
  {
    id: '2',
    title: 'Dashboard UI Specification',
    status: 'draft',
    author: 'Design Agent',
    createdAt: '2024-01-12T11:30:00Z',
    projectId: '1',
  },
]
