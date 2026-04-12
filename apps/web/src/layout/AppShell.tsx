import { useState, type ReactNode } from "react";
import { Menu } from "lucide-react";

type AppShellProps = {
  sidebar: ReactNode;
  header: ReactNode;
  main: ReactNode;
  drawer?: ReactNode;
};

export function AppShell({ sidebar, header, main, drawer }: AppShellProps) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <div className="app-topbar">
        <button
          type="button"
          className="btn-ghost md:hidden"
          aria-label="Toggle sidebar"
          onClick={() => setMobileSidebarOpen((value) => !value)}
        >
          <Menu className="h-4 w-4" />
        </button>
        <div className="min-w-0 flex-1">{header}</div>
      </div>
      <div className="app-body">
        <aside className={mobileSidebarOpen ? "app-sidebar" : "app-sidebar max-md:hidden"}>
          {sidebar}
        </aside>
        <main className="app-main">
          {main}
          {drawer}
        </main>
      </div>
    </div>
  );
}
