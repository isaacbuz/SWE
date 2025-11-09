import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import CreateSkillPage from '@/app/(dashboard)/skills/create/page'

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    back: vi.fn(),
  }),
}))

vi.mock('@/lib/hooks/use-skills', () => ({
  useCreateSkill: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}))

describe('CreateSkillPage', () => {
  it('renders required fields', () => {
    render(<CreateSkillPage />)

    expect(screen.getByLabelText(/Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Slug/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Prompt Template/i)).toBeInTheDocument()
  })

  it('disables submit button until required fields filled', () => {
    render(<CreateSkillPage />)
    const button = screen.getByRole('button', { name: /Create Skill/i })
    expect(button).toBeDisabled()
  })
})
