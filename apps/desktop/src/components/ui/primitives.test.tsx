import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button, Card, Badge, Input, Modal, ConfirmDialog, Progress, EmptyState } from "./primitives";

describe("Button", () => {
  it("renders children and fires onClick", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    const btn = screen.getByRole("button", { name: /click me/i });
    fireEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled while loading", () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("does not fire when disabled", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick} disabled>Save</Button>);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Hello card</Card>);
    expect(screen.getByText("Hello card")).toBeInTheDocument();
  });
});

describe("Badge", () => {
  it("renders a label", () => {
    render(<Badge>Strong</Badge>);
    expect(screen.getByText("Strong")).toBeInTheDocument();
  });
});

describe("Input", () => {
  it("shows label and hint", () => {
    render(<Input label="Name" hint="Your full name" />);
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(screen.getByText("Your full name")).toBeInTheDocument();
  });

  it("reports an error", () => {
    render(<Input label="Email" error="Required" />);
    expect(screen.getByText("Required")).toBeInTheDocument();
  });
});

describe("Modal", () => {
  it("renders when open and closes on Escape", () => {
    const onClose = vi.fn();
    const { rerender } = render(
      <Modal open onClose={onClose} title="Test modal">
        <p>Body</p>
      </Modal>
    );
    expect(screen.getByText("Body")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
    rerender(
      <Modal open={false} onClose={onClose} title="Test modal">
        <p>Body</p>
      </Modal>
    );
    expect(screen.queryByText("Body")).not.toBeInTheDocument();
  });
});

describe("ConfirmDialog", () => {
  it("requires explicit confirmation", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="Delete?"
        message="Are you sure?"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });
});

describe("Progress", () => {
  it("renders with a width", () => {
    const { container } = render(<Progress value={60} />);
    const bar = container.querySelector(".bg-accent") as HTMLElement;
    expect(bar).toHaveStyle({ width: "60%" });
  });
});

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(<EmptyState icon={<span>🚀</span>} title="Nothing here" description="Add something" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Add something")).toBeInTheDocument();
  });
});
