"use client";

import { useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface Message {
  sender: "user" | "bot";
  text: string;
}

interface ChatProps {
    messages: Message[];
    isLoading: boolean;
    onSendMessage: (input: string) => void;
}

export function Chat({ messages, isLoading, onSendMessage }: ChatProps) {
  const [input, setInput] = useState("");

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput("");
  };

  return (
    <Card className="w-full max-w-2xl h-full grid grid-rows-[auto,1fr,auto]">
      <CardHeader>
        <CardTitle>CPE - Seu agente inteligente</CardTitle>
      </CardHeader>
      <CardContent className="overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex items-end gap-2 ${
              message.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-xs md:max-w-md lg:max-w-xl rounded-lg px-4 py-2 ${
                message.sender === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-200 text-slate-900 dark:bg-slate-700 dark:text-slate-50"
              }`}
            >
              <div className="prose dark:prose-invert text-sm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.text}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {isLoading && messages[messages.length-1]?.sender === 'bot' && (
            <div className="flex items-end gap-2 justify-start">
                <div className="max-w-xs rounded-lg px-4 py-2 bg-slate-200 text-slate-900 dark:bg-slate-700 dark:text-slate-50">
                    <div className="flex items-center justify-center gap-1">
                        <span className="h-2 w-2 bg-slate-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="h-2 w-2 bg-slate-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="h-2 w-2 bg-slate-500 rounded-full animate-bounce"></span>
                    </div>
                </div>
            </div>
        )}
        {messages.length === 0 && !isLoading && (
            <div className="flex justify-center items-center h-full">
                <p className="text-slate-500">Faça uma pergunta sobre os produtos para começar!</p>
            </div>
        )}
      </CardContent>
      <CardFooter>
        <form onSubmit={handleSendMessage} className="flex w-full items-center space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite sua pergunta aqui..."
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading}>Enviar</Button>
        </form>
      </CardFooter>
    </Card>
  );
} 