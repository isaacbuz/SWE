import { faker } from "@faker-js/faker";

export interface UserFixture {
  id: string;
  email: string;
  name: string;
  role: "admin" | "user" | "viewer";
  createdAt: string;
  lastLogin: string | null;
}

export const createUserFixture = (
  overrides?: Partial<UserFixture>,
): UserFixture => {
  return {
    id: faker.string.uuid(),
    email: faker.internet.email(),
    name: faker.person.fullName(),
    role: faker.helpers.arrayElement(["admin", "user", "viewer"]),
    createdAt: faker.date.past().toISOString(),
    lastLogin: faker.datatype.boolean()
      ? faker.date.recent().toISOString()
      : null,
    ...overrides,
  };
};

export const userFixtures = {
  admin: createUserFixture({ role: "admin", email: "admin@example.com" }),
  user: createUserFixture({ role: "user", email: "user@example.com" }),
  viewer: createUserFixture({ role: "viewer", email: "viewer@example.com" }),
};
