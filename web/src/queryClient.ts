import { QueryClient } from '@tanstack/react-query'

/**
 * TanStack Query client.
 *
 * Defaults:
 * - staleTime 5 min  — API data changes slowly (daily predictions)
 * - gcTime    15 min — keep cache warm while user navigates between routes
 * - retry 2          — transient network errors should retry
 * - No global error handler here; each query handles its own error state
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime:  5  * 60 * 1000,
      gcTime:     15 * 60 * 1000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})
