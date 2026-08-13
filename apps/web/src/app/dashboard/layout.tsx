import { Sidebar } from "@/components/dashboard/Sidebar";
import { ChatPanel } from "@/components/dashboard/ChatPanel";
import { TarifaAlertBanner, PrivacyReviewBanner, EmailVerificationBanner } from "@/components/dashboard/AlertBanners";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto scroll-smooth bg-[#f8fafc]">
        <div className="space-y-3 p-4 pb-0">
          <EmailVerificationBanner />
          <TarifaAlertBanner />
          <PrivacyReviewBanner />
        </div>
        <div className="page-enter">
          {children}
        </div>
      </main>
      <ChatPanel />
    </div>
  );
}
