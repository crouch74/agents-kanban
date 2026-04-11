import type { ComponentProps } from "react";
import { WaitingInboxScreen } from "@/screens/WaitingInboxScreen";

export function WaitingSectionContainer(props: ComponentProps<typeof WaitingInboxScreen>) {
  return <WaitingInboxScreen {...props} />;
}
