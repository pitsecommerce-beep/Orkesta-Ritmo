"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageSquare, Send, X, Smartphone } from "lucide-react";
import { cn } from "@/lib/utils";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: Date;
};

export function ChatPanel() {
  const [open, setOpen] = useState(false);
  const [channel, setChannel] = useState<"web" | "whatsapp">("web");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "¡Hola! Soy el asistente de Ritmo. Puedo ayudarte con dudas sobre tu declaración fiscal. ¿En qué te puedo ayudar?",
      ts: new Date(),
    },
  ]);
  const [input, setInput] = useState("");

  function send() {
    if (!input.trim()) return;
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
      ts: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    setTimeout(() => {
      const botMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Estoy procesando tu consulta. Esta funcionalidad estará disponible pronto con conexión al API.",
        ts: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    }, 500);
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-azul)] text-white shadow-lg hover:bg-[var(--color-azul-profundo)] transition-colors"
      >
        <MessageSquare className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex h-[500px] w-[380px] flex-col rounded-xl border bg-background shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="font-heading text-sm font-semibold">Asistente Ritmo</h3>
        <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Channel Tabs */}
      <Tabs value={channel} onValueChange={(v) => setChannel(v as "web" | "whatsapp")}>
        <TabsList className="mx-3 mt-2 w-auto">
          <TabsTrigger value="web" className="gap-1 text-xs">
            <MessageSquare className="h-3 w-3" /> Web
          </TabsTrigger>
          <TabsTrigger value="whatsapp" className="gap-1 text-xs">
            <Smartphone className="h-3 w-3" /> WhatsApp
          </TabsTrigger>
        </TabsList>

        <TabsContent value="web" className="flex flex-1 flex-col mt-0">
          <ScrollArea className="flex-1 px-4 py-3">
            <div className="space-y-3">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                    m.role === "user"
                      ? "ml-auto bg-[var(--color-azul)] text-white"
                      : "bg-muted text-foreground",
                  )}
                >
                  {m.content}
                </div>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="whatsapp" className="flex flex-1 flex-col mt-0">
          <div className="flex flex-1 flex-col items-center justify-center px-4 text-center">
            <Smartphone className="h-10 w-10 text-muted-foreground" />
            <p className="mt-3 text-sm text-muted-foreground">
              El canal de WhatsApp estará disponible próximamente.
              Por ahora, usa el chat web.
            </p>
          </div>
        </TabsContent>
      </Tabs>

      {/* Input */}
      <div className="border-t p-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="flex gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe tu mensaje..."
            className="flex-1 text-sm"
          />
          <Button type="submit" size="sm" disabled={!input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
