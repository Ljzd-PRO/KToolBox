import { Table } from "@heroui/react";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataTableFrame } from "./ui";

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
