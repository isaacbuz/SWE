import { faker } from '@faker-js/faker';

export interface ProjectFixture {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'completed' | 'archived';
  createdAt: string;
  updatedAt: string;
  ownerId: string;
  taskCount: number;
  agentCount: number;
}

export const createProjectFixture = (overrides?: Partial<ProjectFixture>): ProjectFixture => {
  return {
    id: faker.string.uuid(),
    name: faker.company.buzzPhrase(),
    description: faker.lorem.paragraph(),
    status: faker.helpers.arrayElement(['active', 'paused', 'completed', 'archived']),
    createdAt: faker.date.past().toISOString(),
    updatedAt: faker.date.recent().toISOString(),
    ownerId: faker.string.uuid(),
    taskCount: faker.number.int({ min: 0, max: 50 }),
    agentCount: faker.number.int({ min: 0, max: 10 }),
    ...overrides,
  };
};

export const projectFixtures = {
  active: createProjectFixture({ status: 'active', taskCount: 10, agentCount: 3 }),
  completed: createProjectFixture({ status: 'completed', taskCount: 20, agentCount: 0 }),
  empty: createProjectFixture({ status: 'active', taskCount: 0, agentCount: 0 }),
};
