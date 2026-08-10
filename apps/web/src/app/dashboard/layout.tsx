import { Sidebar } from "@/components/dashboard/Sidebar";
import { ChatPanel } from "@/components/dashboard/ChatPanel";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-muted/30">
        {children}
      </main>
      <ChatPanel />
    </div>
  );
}
