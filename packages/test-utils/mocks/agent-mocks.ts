import { faker } from "@faker-js/faker";

export interface MockAgent {
  id: string;
  name: string;
  type: "developer" | "qa" | "devops" | "architect" | "pm";
  status: "available" | "busy" | "offline" | "error";
  capabilities: string[];
  currentTask: string | null;
  metrics: {
    tasksCompleted: number;
    successRate: number;
    averageTime: number;
  };
}

export const createMockAgent = (overrides?: Partial<MockAgent>): MockAgent => {
  return {
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    type: faker.helpers.arrayElement([
      "developer",
      "qa",
      "devops",
      "architect",
      "pm",
    ]),
    status: faker.helpers.arrayElement(["available", "busy", "offline"]),
    capabilities: faker.helpers.arrayElements(
      ["code_generation", "code_review", "testing", "deployment", "monitoring"],
      { min: 1, max: 3 },
    ),
    currentTask: faker.datatype.boolean() ? faker.string.uuid() : null,
    metrics: {
      tasksCompleted: faker.number.int({ min: 0, max: 100 }),
      successRate: faker.number.float({ min: 0.5, max: 1, fractionDigits: 2 }),
      averageTime: faker.number.int({ min: 300, max: 7200 }),
    },
    ...overrides,
  };
};

export const createMockAgentList = (count: number = 5): MockAgent[] => {
  return Array.from({ length: count }, () => createMockAgent());
};
