"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase";
import { OnboardingTour } from "./OnboardingTour";
import { IntroQuestionnaire } from "./IntroQuestionnaire";

type Phase = "loading" | "tour" | "questionnaire" | "done";

export function DashboardOnboarding() {
  const [phase, setPhase] = useState<Phase>("loading");

  useEffect(() => {
    async function check() {
      const supabase = createClient();
      if (!supabase) {
        setPhase("done");
        return;
      }

      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) {
        setPhase("done");
        return;
      }

      const { data: profile } = await supabase
        .from("user_profiles")
        .select("onboarding_completado")
        .eq("id", user.id)
        .maybeSingle();

      if (profile && !profile.onboarding_completado) {
        setPhase("tour");
        return;
      }

      const { data: memberships } = await supabase
        .from("memberships")
        .select("id")
        .eq("user_id", user.id)
        .limit(1);

      if (!memberships || memberships.length === 0) {
        setPhase("questionnaire");
        return;
      }

      setPhase("done");
    }
    check();
  }, []);

  if (phase === "loading" || phase === "done") return null;

  if (phase === "tour") {
    return (
      <OnboardingTour
        onComplete={() => {
          checkMemberships().then((has) => {
            setPhase(has ? "done" : "questionnaire");
          });
        }}
      />
    );
  }

  if (phase === "questionnaire") {
    return <IntroQuestionnaire onComplete={() => setPhase("done")} />;
  }

  return null;
}

async function checkMemberships(): Promise<boolean> {
  const supabase = createClient();
  if (!supabase) return true;

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return true;

  const { data } = await supabase
    .from("memberships")
    .select("id")
    .eq("user_id", user.id)
    .limit(1);

  return !!data && data.length > 0;
}
