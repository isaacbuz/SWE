/**
 * Tests for SkillCard component
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SkillCard } from "@/components/skills/skill-card";
import { Skill } from "@/lib/api/skills";

const mockSkill: Skill = {
  id: "skill-1",
  name: "Test Skill",
  slug: "test-skill",
  version: "1.0.0",
  description: "A test skill for testing",
  category: "CODE_GENERATION",
  tags: ["test", "code"],
  download_count: 10,
  installation_count: 5,
  execution_count: 20,
  avg_rating: 4.5,
  review_count: 8,
  status: "active",
  visibility: "public",
  license: "MIT",
  pricing_model: "free",
};

describe("SkillCard", () => {
  it("renders skill information correctly", () => {
    render(<SkillCard skill={mockSkill} />);

    expect(screen.getByText("Test Skill")).toBeInTheDocument();
    expect(screen.getByText("A test skill for testing")).toBeInTheDocument();
    expect(screen.getByText("4.5")).toBeInTheDocument();
  });

  it("displays install button when not installed", () => {
    render(<SkillCard skill={mockSkill} installed={false} />);

    expect(screen.getByText("Install")).toBeInTheDocument();
  });

  it("displays installed badge when installed", () => {
    render(<SkillCard skill={mockSkill} installed={true} />);

    expect(screen.getByText("Installed")).toBeInTheDocument();
  });

  it("calls onInstall when install button is clicked", () => {
    const onInstall = vi.fn();
    render(<SkillCard skill={mockSkill} onInstall={onInstall} />);

    const installButton = screen.getByText("Install");
    installButton.click();

    expect(onInstall).toHaveBeenCalledWith("skill-1");
  });

  it("calls onUninstall when uninstall button is clicked", () => {
    const onUninstall = vi.fn();
    render(
      <SkillCard
        skill={mockSkill}
        installed={true}
        onUninstall={onUninstall}
      />,
    );

    const uninstallButton = screen.getByText("Installed");
    uninstallButton.click();

    expect(onUninstall).toHaveBeenCalledWith("skill-1");
  });

  it("displays tags correctly", () => {
    render(<SkillCard skill={mockSkill} />);

    expect(screen.getByText("test")).toBeInTheDocument();
    expect(screen.getByText("code")).toBeInTheDocument();
  });

  it("displays stats correctly", () => {
    render(<SkillCard skill={mockSkill} />);

    expect(screen.getByText("5")).toBeInTheDocument(); // installation_count
    expect(screen.getByText("20")).toBeInTheDocument(); // execution_count
  });

  it("displays free badge for free skills", () => {
    render(<SkillCard skill={mockSkill} />);

    expect(screen.getByText("Free")).toBeInTheDocument();
  });
});
