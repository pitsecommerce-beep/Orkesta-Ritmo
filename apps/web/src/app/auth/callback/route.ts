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
        if (verify) {
          const { data: { user } } = await supabase.auth.getUser();
          if (user) {
            await supabase
              .from("user_profiles")
              .update({ email_verificado: true })
              .eq("id", user.id);
          }
        }
        return NextResponse.redirect(`${origin}${next}`);
      }
    }
  }

  return NextResponse.redirect(`${origin}/auth/login?error=auth`);
}
