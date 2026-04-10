import type { ReactNode } from "react";

type DashboardScreenProps = {
  children: ReactNode;
};

export function DashboardScreen({ children }: DashboardScreenProps) {
  return children;
}
