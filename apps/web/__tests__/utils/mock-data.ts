// Mock data generators for testing

export const mockAgent = (overrides = {}) => ({
  id: "agent-1",
  name: "Test Agent",
  type: "developer",
  status: "available",
  capabilities: ["code_generation", "code_review"],
  currentTask: null,
  metrics: {
    tasksCompleted: 10,
    successRate: 0.95,
    averageTime: 1200,
  },
  ...overrides,
});

export const mockTask = (overrides = {}) => ({
  id: "task-1",
  title: "Test Task",
  description: "This is a test task",
  status: "pending",
  priority: "medium",
  assignedAgent: null,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  estimatedDuration: 3600,
  tags: ["test", "development"],
  ...overrides,
});

export const mockProject = (overrides = {}) => ({
  id: "project-1",
  name: "Test Project",
  description: "This is a test project",
  status: "active",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  tasks: [],
  agents: [],
  ...overrides,
});

export const mockUser = (overrides = {}) => ({
  id: "user-1",
  email: "test@example.com",
  name: "Test User",
  role: "admin",
  createdAt: new Date().toISOString(),
  ...overrides,
});

export const mockWorkflowExecution = (overrides = {}) => ({
  id: "exec-1",
  workflowId: "workflow-1",
  status: "running",
  startedAt: new Date().toISOString(),
  steps: [],
  context: {},
  ...overrides,
});
