import { Table } from "@heroui/react";
import { render, screen } from "@testing-library/react";
import { IconSearch as Search } from "@tabler/icons-react";
import { describe, expect, it } from "vitest";

import {
  CompactSwitch,
  ConfirmModal,
  DataTableFrame,
  FormCheckbox,
  FormField,
  FormModal,
  FormSurface,
  FormSwitchField,
} from "./ui";

describe("DataTableFrame", () => {
  it("uses one bordered scroll container without a wrapping surface", () => {
    const { container } = render(
      <DataTableFrame>
        <Table.Content aria-label="Example table">
          <Table.Header>
            <Table.Column isRowHeader>Name</Table.Column>
          </Table.Header>
          <Table.Body>
            <Table.Row id="row-1">
              <Table.Cell>Example</Table.Cell>
            </Table.Row>
          </Table.Body>
        </Table.Content>
      </DataTableFrame>,
    );

    const frame = container.querySelector(".app-table-frame");
    expect(frame).toBeInTheDocument();
    expect(frame?.parentElement).toHaveClass("table-root--secondary");
    expect(frame?.parentElement).not.toHaveClass("rounded-lg", "border", "border-border");
  });
});

describe("form selection controls", () => {
  it("nests the switch control and label inside the clickable content", () => {
    const { container } = render(
      <FormSwitchField description="Used during synchronization" isSelected label="Save index" onChange={() => undefined} />,
    );

    const root = container.querySelector('[data-slot="switch"]');
    const content = container.querySelector<HTMLElement>('[data-slot="switch-content"]');
    const control = container.querySelector<HTMLElement>('[data-slot="switch-control"]');
    const description = container.querySelector('[data-slot="description"]');
    expect(content).toContainElement(control);
    expect(content).toHaveTextContent("Save index");
    expect(description?.parentElement).toBe(root);
    expect(container.querySelector('[data-slot="switch-icon"]')).not.toBeInTheDocument();
  });

  it("only renders a checkbox indicator for selected or indeterminate states", () => {
    const { container, rerender } = render(
      <FormCheckbox description="Optional setting" isSelected={false} label="Apply start date" onChange={() => undefined} />,
    );

    const root = container.querySelector('[data-slot="checkbox"]');
    const content = container.querySelector<HTMLElement>('[data-slot="checkbox-content"]');
    const control = container.querySelector<HTMLElement>('[data-slot="checkbox-control"]');
    const description = container.querySelector('[data-slot="description"]');
    expect(content).toContainElement(control);
    expect(content).toHaveTextContent("Apply start date");
    expect(description?.parentElement).toBe(root);
    expect(container.querySelector('[data-slot="checkbox-indicator"]')).not.toBeInTheDocument();

    rerender(<FormCheckbox isSelected label="Apply start date" onChange={() => undefined} />);
    expect(container.querySelector('[data-slot="checkbox-indicator"]')).toBeInTheDocument();

    rerender(<FormCheckbox isIndeterminate isSelected={false} label="Apply start date" onChange={() => undefined} />);
    expect(container.querySelector('[data-slot="checkbox"]')).toHaveAttribute("data-indeterminate", "true");
    expect(container.querySelector('[data-slot="checkbox-indicator"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="checkbox-indicator"] svg')).toHaveAttribute("aria-hidden", "true");
  });

  it("provides a compact, accessible list switch without visible label content", () => {
    const { container } = render(
      <CompactSwitch isSelected={false} label="Enable creator" onChange={() => undefined} />,
    );

    const root = container.querySelector('[data-slot="switch"]');
    expect(screen.getByRole("switch", { name: "Enable creator" })).toBeInTheDocument();
    expect(root).toHaveClass("compact-switch");
    expect(root).not.toHaveTextContent("Enable creator");
  });
});

describe("form surfaces", () => {
  it("groups fields on a semantic secondary surface and hides decorative icons", () => {
    const { container } = render(
      <FormSurface>
        <FormField icon={Search} label="Search settings" value="" onChange={() => undefined} />
      </FormSurface>,
    );

    const surface = container.querySelector(".form-surface");
    const icon = surface?.querySelector("svg");
    expect(surface).toHaveClass("surface--secondary");
    expect(surface).toContainElement(container.querySelector("input"));
    expect(icon).toHaveAttribute("aria-hidden", "true");
  });

  it("keeps the scroll body and fixed footer in one secondary surface", () => {
    render(
      <FormModal
        actions={<span>Save action</span>}
        open
        title="Edit task"
        onOpenChange={() => undefined}
      >
        <FormField label="Output" value="downloads" onChange={() => undefined} />
      </FormModal>,
    );

    const surface = document.querySelector<HTMLElement>(".app-form-modal-surface");
    const body = document.querySelector<HTMLElement>(".app-form-modal-body");
    const actions = document.querySelector<HTMLElement>(".app-form-modal-actions");
    expect(surface?.querySelector("input")).toBeInTheDocument();
    expect(surface).toHaveClass("rounded-none", "border-0");
    expect(surface).toContainElement(body);
    expect(surface).toContainElement(actions);
    expect(actions).toHaveTextContent("Save action");
    expect(actions).toHaveAttribute("data-slot", "modal-footer");
  });

  it("uses the dialog itself as the only surface for confirmations", () => {
    render(
      <ConfirmModal
        actions={<span>Delete action</span>}
        open
        title="Delete task"
        onOpenChange={() => undefined}
      >
        <p>Deletion warning</p>
      </ConfirmModal>,
    );

    const body = document.querySelector<HTMLElement>(".app-confirm-modal-body");
    const actions = document.querySelector<HTMLElement>(".app-confirm-modal-actions");
    expect(body).toHaveTextContent("Deletion warning");
    expect(body).not.toContainElement(actions);
    expect(actions).toHaveAttribute("data-slot", "modal-footer");
    expect(body?.querySelector(".form-surface")).not.toBeInTheDocument();
  });
});
