import { expect, test } from "vitest";
import { toDisplay } from "@/utils/display";

test("formats snake case and uppercase enum values for display", () => {
  expect(toDisplay("in_progress")).toBe("In Progress");
  expect(toDisplay("HIGH_PRIORITY")).toBe("High Priority");
});
