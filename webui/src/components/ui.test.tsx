import { Table } from "@heroui/react";
import { parseDate, type DateValue } from "@internationalized/date";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { IconCalendar as Calendar, IconSearch as Search, IconTags as Tags } from "@tabler/icons-react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import {
  ChipListField,
  CompactSwitch,
  ConfirmModal,
  DataTableFrame,
  FormCheckbox,
  FormField,
  FormModal,
  FormSurface,
  FormSwitchField,
  OptionalDateRangeField,
  PawchivePathField,
} from "./ui";

function ChipListHarness({ commitOnComma = true }: { commitOnComma?: boolean }) {
  const [values, setValues] = useState<string[]>([]);
  return (
    <ChipListField
      commitOnComma={commitOnComma}
      icon={Tags}
      label="Keywords"
      placeholder="Add keyword"
      values={values}
      onChange={setValues}
    />
  );
}

function OptionalDateHarness() {
  const [start, setStart] = useState<DateValue | null>(parseDate("2026-07-10"));
  const [end, setEnd] = useState<DateValue | null>(null);
  const [startUnlimited, setStartUnlimited] = useState(false);
  const [endUnlimited, setEndUnlimited] = useState(true);
  return (
    <>
      <OptionalDateRangeField
        description="Choose optional publication boundaries."
        endLabel="End date"
        endUnlimited={endUnlimited}
        endUnlimitedLabel="No end date"
        endValue={end}
        icon={Calendar}
        label="Publication range"
        startLabel="Start date"
        startUnlimited={startUnlimited}
        startUnlimitedLabel="No start date"
        startValue={start}
        onEndChange={setEnd}
        onEndUnlimitedChange={setEndUnlimited}
        onStartChange={setStart}
        onStartUnlimitedChange={setStartUnlimited}
      />
      <output data-testid="date-state">
        {start?.toString() ?? "none"}|{end?.toString() ?? "none"}|{String(startUnlimited)}|{String(endUnlimited)}
      </output>
    </>
  );
}

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

describe("ChipListField", () => {
  it("commits comma and Enter delimited values, ignores duplicates, and supports removal", async () => {
    const user = userEvent.setup();
    render(<ChipListHarness />);
    const input = screen.getByRole("textbox", { name: "Keywords" });

    await user.type(input, "alpha,");
    await user.type(input, "beta，");
    await user.type(input, "gamma{Enter}");
    await user.type(input, "alpha{Enter}");

    expect(screen.getByText("alpha")).toBeInTheDocument();
    expect(screen.getByText("beta")).toBeInTheDocument();
    expect(screen.getByText("gamma")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Remove/ })).toHaveLength(3);

    await user.click(screen.getByRole("button", { name: "Remove beta" }));
    expect(screen.queryByText("beta")).not.toBeInTheDocument();
    await user.click(input);
    await user.keyboard("{Backspace}");
    expect(screen.queryByText("gamma")).not.toBeInTheDocument();
  });

  it("splits pasted lists and does not commit Enter during IME composition", () => {
    render(<ChipListHarness />);
    const input = screen.getByRole("textbox", { name: "Keywords" });

    fireEvent.paste(input, { clipboardData: { getData: () => "one,two，three\nfour" } });
    expect(screen.getByText("one")).toBeInTheDocument();
    expect(screen.getByText("four")).toBeInTheDocument();

    fireEvent.change(input, { target: { value: "composing" } });
    fireEvent.keyDown(input, { key: "Enter", isComposing: true });
    expect(screen.queryByText("composing")).not.toBeInTheDocument();
    expect(input).toHaveValue("composing");
  });

  it("preserves commas when the field uses Enter-only commits", async () => {
    const user = userEvent.setup();
    render(<ChipListHarness commitOnComma={false} />);
    const input = screen.getByRole("textbox", { name: "Keywords" });

    await user.type(input, "^foo,bar${Enter}");
    expect(screen.getByText("^foo,bar$")).toBeInTheDocument();
  });
});

describe("OptionalDateRangeField", () => {
  it("keeps boundaries independent and clears a date when unlimited is selected", async () => {
    const user = userEvent.setup();
    render(<OptionalDateHarness />);

    expect(screen.getByRole("group", { name: "Start date" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "End date" })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "No start date" })).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: "No end date" })).toBeChecked();

    await user.click(screen.getByRole("checkbox", { name: "No start date" }));
    expect(screen.getByTestId("date-state")).toHaveTextContent("none|none|true|true");

    await user.click(screen.getByRole("checkbox", { name: "No end date" }));
    expect(screen.getByTestId("date-state")).toHaveTextContent("none|none|true|false");
  });
});

describe("PawchivePathField", () => {
  it("composes accessible inputs into the real Pawchive path shape", async () => {
    const user = userEvent.setup();
    function Harness() {
      const [service, setService] = useState("");
      const [creatorId, setCreatorId] = useState("");
      const [postId, setPostId] = useState("");
      return (
        <PawchivePathField
          creatorId={creatorId}
          creatorIdLabel="Creator ID"
          label="Pawchive post path"
          postId={postId}
          postIdLabel="Post ID"
          service={service}
          serviceLabel="Service"
          onCreatorIdChange={setCreatorId}
          onPostIdChange={setPostId}
          onServiceChange={setService}
        />
      );
    }
    render(<Harness />);

    await user.type(screen.getByRole("textbox", { name: "Service" }), "fanbox");
    await user.type(screen.getByRole("textbox", { name: "Creator ID" }), "42");
    await user.type(screen.getByRole("textbox", { name: "Post ID" }), "99");

    expect(screen.getByRole("group", { name: "Pawchive post path" })).toHaveTextContent("//user//post/");
    expect(screen.getByRole("textbox", { name: "Service" })).toHaveValue("fanbox");
    expect(screen.getByRole("textbox", { name: "Creator ID" })).toHaveValue("42");
    expect(screen.getByRole("textbox", { name: "Post ID" })).toHaveValue("99");
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
        isWide
        open
        title="Edit task"
        onOpenChange={() => undefined}
      >
        <FormField label="Output" value="downloads" onChange={() => undefined} />
      </FormModal>,
    );

    const surface = document.querySelector<HTMLElement>(".app-form-modal-surface");
    const container = document.querySelector<HTMLElement>(".app-form-modal-container-wide");
    const body = document.querySelector<HTMLElement>(".app-form-modal-body");
    const actions = document.querySelector<HTMLElement>(".app-form-modal-actions");
    expect(surface?.querySelector("input")).toBeInTheDocument();
    expect(container).toHaveAttribute("data-slot", "modal-container");
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
