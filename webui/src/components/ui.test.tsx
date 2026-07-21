import { Table } from "@heroui/react";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataTableFrame, FormCheckbox, Toggle } from "./ui";

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
      <Toggle description="Used during synchronization" isSelected label="Save index" onChange={() => undefined} />,
    );

    const root = container.querySelector('[data-slot="switch"]');
    const content = container.querySelector<HTMLElement>('[data-slot="switch-content"]');
    const control = container.querySelector<HTMLElement>('[data-slot="switch-control"]');
    const description = container.querySelector('[data-slot="description"]');
    expect(content).toContainElement(control);
    expect(content).toHaveTextContent("Save index");
    expect(description?.parentElement).toBe(root);
  });

  it("nests the checkbox control and label inside the clickable content", () => {
    const { container } = render(
      <FormCheckbox description="Optional setting" isSelected={false} label="Apply start date" onChange={() => undefined} />,
    );

    const root = container.querySelector('[data-slot="checkbox"]');
    const content = container.querySelector<HTMLElement>('[data-slot="checkbox-content"]');
    const control = container.querySelector<HTMLElement>('[data-slot="checkbox-control"]');
    const description = container.querySelector('[data-slot="description"]');
    expect(content).toContainElement(control);
    expect(content).toHaveTextContent("Apply start date");
    expect(description?.parentElement).toBe(root);
  });
});
