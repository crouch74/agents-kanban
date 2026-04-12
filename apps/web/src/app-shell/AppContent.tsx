import type { ReactNode } from "react";
import { AppShell } from "@/layout/AppShell";

type AppContentProps = {
  sidebar: ReactNode;
  header: ReactNode;
  main: ReactNode;
  drawer?: ReactNode;
};

export function AppContent({ sidebar, header, main, drawer }: AppContentProps) {
  return <AppShell sidebar={sidebar} header={header} main={main} drawer={drawer} />;
}
