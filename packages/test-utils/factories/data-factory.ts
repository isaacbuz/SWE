import { createMockAgent } from '../mocks/agent-mocks';
import { createTaskFixture } from '../fixtures/task-fixtures';
import { createUserFixture } from '../fixtures/user-fixtures';
import { createProjectFixture } from '../fixtures/project-fixtures';

export class DataFactory {
  public static agents(count: number = 5) {
    return Array.from({ length: count }, () => createMockAgent());
  }

  public static tasks(count: number = 10) {
    return Array.from({ length: count }, () => createTaskFixture());
  }

  public static users(count: number = 3) {
    return Array.from({ length: count }, () => createUserFixture());
  }

  public static projects(count: number = 2) {
    return Array.from({ length: count }, () => createProjectFixture());
  }

  public static completeWorkflow() {
    const users = this.users(1);
    const agents = this.agents(3);
    const project = createProjectFixture({
      ownerId: users[0].id,
      agentCount: agents.length,
    });
    const tasks = this.tasks(5).map((task) => ({
      ...task,
      assignedAgent: agents[Math.floor(Math.random() * agents.length)].id,
    }));

    return {
      users,
      agents,
      project: {
        ...project,
        taskCount: tasks.length,
      },
      tasks,
    };
  }
}
