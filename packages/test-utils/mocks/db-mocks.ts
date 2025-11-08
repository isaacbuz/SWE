export class MockDatabase {
  private data: Map<string, Map<string, any>> = new Map();

  constructor() {
    // Initialize tables
    this.data.set('agents', new Map());
    this.data.set('tasks', new Map());
    this.data.set('users', new Map());
    this.data.set('projects', new Map());
  }

  public async insert(table: string, id: string, data: any) {
    const tableData = this.data.get(table);
    if (!tableData) {
      throw new Error(`Table ${table} does not exist`);
    }
    tableData.set(id, { ...data, id, createdAt: new Date(), updatedAt: new Date() });
    return data;
  }

  public async findById(table: string, id: string) {
    const tableData = this.data.get(table);
    if (!tableData) {
      throw new Error(`Table ${table} does not exist`);
    }
    return tableData.get(id) || null;
  }

  public async findAll(table: string) {
    const tableData = this.data.get(table);
    if (!tableData) {
      throw new Error(`Table ${table} does not exist`);
    }
    return Array.from(tableData.values());
  }

  public async update(table: string, id: string, data: any) {
    const tableData = this.data.get(table);
    if (!tableData) {
      throw new Error(`Table ${table} does not exist`);
    }
    const existing = tableData.get(id);
    if (!existing) {
      throw new Error(`Record ${id} not found in ${table}`);
    }
    const updated = { ...existing, ...data, updatedAt: new Date() };
    tableData.set(id, updated);
    return updated;
  }

  public async delete(table: string, id: string) {
    const tableData = this.data.get(table);
    if (!tableData) {
      throw new Error(`Table ${table} does not exist`);
    }
    return tableData.delete(id);
  }

  public async clear(table?: string) {
    if (table) {
      const tableData = this.data.get(table);
      if (tableData) {
        tableData.clear();
      }
    } else {
      this.data.forEach((tableData) => tableData.clear());
    }
  }

  public async seed(table: string, data: any[]) {
    const tableData = this.data.get(table);
    if (!tableData) {
      throw new Error(`Table ${table} does not exist`);
    }
    data.forEach((item) => {
      tableData.set(item.id, item);
    });
  }
}

export const createMockDatabase = () => new MockDatabase();
