"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Send, Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const INITIAL_MESSAGES: Message[] = [
  {
    id: "1",
    role: "assistant",
    content: "¡Hola! Soy el asistente fiscal de Ritmo. Puedo ayudarte con:\n\n• Dudas sobre tu declaración mensual\n• Explicación del desglose fiscal\n• Clasificación de CFDIs\n• Preguntas sobre regímenes fiscales\n\n¿En qué te puedo ayudar?",
  },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState("");

  function send() {
    if (!input.trim()) return;
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Esta funcionalidad estará disponible cuando se configure la conexión al API. Por ahora, puedo mostrarte información de ejemplo sobre cómo funciona el asistente fiscal.",
        },
      ]);
    }, 500);
  }

  return (
    <div className="flex h-full flex-col p-6 lg:p-8">
      <h1 className="font-heading text-2xl font-bold">Asistente fiscal</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Consulta dudas sobre tu declaración. La IA nunca produce números que entren al cálculo sin validación.
      </p>

      <Card className="mt-6 flex flex-1 flex-col overflow-hidden">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((m) => (
              <div key={m.id} className={cn("flex gap-3", m.role === "user" ? "justify-end" : "")}>
                {m.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--color-azul)]/10">
                    <Bot className="h-4 w-4 text-[var(--color-azul)]" />
                  </div>
                )}
                <div
                  className={cn(
                    "max-w-[70%] rounded-lg px-4 py-3 text-sm whitespace-pre-line",
                    m.role === "user"
                      ? "bg-[var(--color-azul)] text-white"
                      : "bg-muted",
                  )}
                >
                  {m.content}
                </div>
                {m.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="border-t p-4">
          <form
            onSubmit={(e) => { e.preventDefault(); send(); }}
            className="flex gap-3"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe tu pregunta..."
              className="flex-1"
            />
            <Button type="submit" disabled={!input.trim()} className="gap-2">
              <Send className="h-4 w-4" /> Enviar
            </Button>
          </form>
          <p className="mt-2 text-xs text-muted-foreground">
            Tu RFC y datos personales se enmascaran antes de enviarse al proveedor de IA.
          </p>
        </div>
      </Card>
    </div>
  );
}
