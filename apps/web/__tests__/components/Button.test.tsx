import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../utils/test-utils";
import userEvent from "@testing-library/user-event";

// Example component test - adjust based on actual component
describe("Button Component", () => {
  it("renders button with text", () => {
    render(<button>Click me</button>);
    expect(
      screen.getByRole("button", { name: /click me/i }),
    ).toBeInTheDocument();
  });

  it("handles click events", async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<button onClick={handleClick}>Click me</button>);

    const button = screen.getByRole("button", { name: /click me/i });
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("can be disabled", () => {
    render(<button disabled>Click me</button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeDisabled();
  });

  it("has correct aria attributes", () => {
    render(<button aria-label="Submit form">Submit</button>);
    expect(screen.getByRole("button")).toHaveAccessibleName("Submit form");
  });
});
