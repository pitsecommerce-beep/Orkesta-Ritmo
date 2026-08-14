import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";
  const verify = searchParams.get("verify") === "true";

  if (code) {
    const supabase = await createServerSupabaseClient();
    if (supabase) {
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      if (!error) {
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
          if (verify) {
            await supabase
              .from("user_profiles")
              .update({ email_verificado: true })
              .eq("id", user.id);
          }

          await supabase
            .from("user_profiles")
            .select("id")
            .eq("id", user.id)
            .maybeSingle()
            .then(({ data }) => {
              if (!data) {
                return supabase.from("user_profiles").insert({
                  id: user.id,
                  email: user.email,
                  email_verificado: false,
                  onboarding_completado: false,
                });
              }
            });
        }
        return NextResponse.redirect(`${origin}${next}`);
      }
    }
  }

  return NextResponse.redirect(`${origin}/auth/login?error=auth`);
}
