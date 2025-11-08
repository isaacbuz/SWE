import { faker } from '@faker-js/faker';

export interface TaskFixture {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignedAgent: string | null;
  createdAt: string;
  updatedAt: string;
  estimatedDuration: number;
  tags: string[];
}

export const createTaskFixture = (overrides?: Partial<TaskFixture>): TaskFixture => {
  return {
    id: faker.string.uuid(),
    title: faker.lorem.sentence(),
    description: faker.lorem.paragraph(),
    status: faker.helpers.arrayElement(['pending', 'in_progress', 'completed', 'failed']),
    priority: faker.helpers.arrayElement(['low', 'medium', 'high', 'critical']),
    assignedAgent: faker.datatype.boolean() ? faker.string.uuid() : null,
    createdAt: faker.date.past().toISOString(),
    updatedAt: faker.date.recent().toISOString(),
    estimatedDuration: faker.number.int({ min: 300, max: 14400 }),
    tags: faker.helpers.arrayElements(['bug', 'feature', 'refactor', 'test', 'docs'], { min: 1, max: 3 }),
    ...overrides,
  };
};

export const taskFixtures = {
  pending: createTaskFixture({ status: 'pending', assignedAgent: null }),
  inProgress: createTaskFixture({ status: 'in_progress', assignedAgent: 'agent-123' }),
  completed: createTaskFixture({ status: 'completed', assignedAgent: 'agent-123' }),
  failed: createTaskFixture({ status: 'failed', assignedAgent: 'agent-123' }),
  highPriority: createTaskFixture({ priority: 'critical', status: 'pending' }),
};
