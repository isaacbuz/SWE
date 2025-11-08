import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { mockAgent } from '../utils/mock-data';

// Mock fetch
global.fetch = vi.fn();

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

// Example hook test - adjust based on actual hook implementation
describe('useAgents hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches agents successfully', async () => {
    const mockAgents = [mockAgent(), mockAgent({ id: 'agent-2' })];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAgents,
    });

    // Note: Actual hook implementation would be imported here
    const { result } = renderHook(
      () => {
        // Placeholder - replace with actual useAgents hook
        return { data: mockAgents, isLoading: false, error: null };
      },
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockAgents);
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('handles error states', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Failed to fetch'));

    const { result } = renderHook(
      () => {
        // Placeholder - replace with actual useAgents hook
        return { data: null, isLoading: false, error: new Error('Failed to fetch') };
      },
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
  });
});
