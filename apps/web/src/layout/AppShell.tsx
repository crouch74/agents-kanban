import type { ReactNode } from "react";

type AppShellProps = {
  sidebar: ReactNode;
  header: ReactNode;
  main: ReactNode;
  drawer: ReactNode;
};

export function AppShell({ sidebar, header, main, drawer }: AppShellProps) {
  return (
    <div className="grid-shell">
      <aside className="border-r border-white/8 px-6 py-6">{sidebar}</aside>
      <main className="px-6 py-6">
        {header}
        <div className="mt-6">{main}</div>
      </main>
      <aside className="border-l border-white/8 px-6 py-6">{drawer}</aside>
    </div>
  );
}
