"use client";

import { Message } from "./Chat"; // Importar a interface Message
import { ModeToggle } from "./theme-toggle";

// Definir a estrutura de uma conversa
export interface Conversation {
  id: string; // Um ID único para cada conversa
  title: string; // O título será a primeira pergunta do usuário
  messages: Message[];
}

interface SidebarProps {
  conversations: Conversation[];
  onSelectConversation: (conversation: Conversation) => void;
  currentConversationId: string | null;
}

export function Sidebar({ conversations, onSelectConversation, currentConversationId }: SidebarProps) {
    return (
        <div className="flex flex-col h-full p-4 bg-slate-100 dark:bg-slate-900 border-r">
            <h2 className="text-lg font-semibold mb-4">Histórico</h2>
            <div className="flex-grow overflow-y-auto">
                {conversations.length === 0 ? (
                    <p className="text-sm text-slate-500">Nenhuma conversa ainda.</p>
                ) : (
                    <ul className="space-y-2">
                        {conversations.map((convo) => (
                            <li key={convo.id}>
                                <button
                                    onClick={() => onSelectConversation(convo)}
                                    className={`w-full text-left text-sm p-2 rounded-md truncate ${
                                        convo.id === currentConversationId
                                            ? "bg-blue-600 text-white"
                                            : "hover:bg-slate-200 dark:hover:bg-slate-800"
                                    }`}
                                >
                                    {convo.title}
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            <div className="mt-auto">
                <ModeToggle />
            </div>
        </div>
    );
} 