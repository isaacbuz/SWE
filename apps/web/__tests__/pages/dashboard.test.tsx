import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../utils/test-utils';
import { mockAgent, mockTask, mockProject } from '../utils/mock-data';

// Example page test - adjust based on actual page implementation
describe('Dashboard Page', () => {
  it('renders dashboard layout', () => {
    // Placeholder component - replace with actual Dashboard page
    render(
      <div role="main">
        <h1>Dashboard</h1>
        <nav aria-label="Main navigation">
          <ul>
            <li><a href="/agents">Agents</a></li>
            <li><a href="/tasks">Tasks</a></li>
            <li><a href="/projects">Projects</a></li>
          </ul>
        </nav>
      </div>
    );

    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: /main navigation/i })).toBeInTheDocument();
  });

  it('displays agent statistics', () => {
    const agents = [
      mockAgent({ status: 'available' }),
      mockAgent({ id: 'agent-2', status: 'busy' }),
      mockAgent({ id: 'agent-3', status: 'available' }),
    ];

    render(
      <div>
        <h2>Agent Statistics</h2>
        <p>Total Agents: {agents.length}</p>
        <p>Available: {agents.filter(a => a.status === 'available').length}</p>
      </div>
    );

    expect(screen.getByText(/total agents: 3/i)).toBeInTheDocument();
    expect(screen.getByText(/available: 2/i)).toBeInTheDocument();
  });

  it('displays task statistics', () => {
    const tasks = [
      mockTask({ status: 'pending' }),
      mockTask({ id: 'task-2', status: 'in_progress' }),
      mockTask({ id: 'task-3', status: 'completed' }),
    ];

    render(
      <div>
        <h2>Task Statistics</h2>
        <p>Total Tasks: {tasks.length}</p>
        <p>Pending: {tasks.filter(t => t.status === 'pending').length}</p>
        <p>In Progress: {tasks.filter(t => t.status === 'in_progress').length}</p>
        <p>Completed: {tasks.filter(t => t.status === 'completed').length}</p>
      </div>
    );

    expect(screen.getByText(/total tasks: 3/i)).toBeInTheDocument();
    expect(screen.getByText(/pending: 1/i)).toBeInTheDocument();
  });
});
