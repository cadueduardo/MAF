"use client";

import { Button } from "@/components/ui/button";
import { Plus, Trash2, MessageSquare } from 'lucide-react'; // Importa os ícones
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
  onNewConversation: () => void;
  onDeleteConversation: (id:string) => void;
}

export function Sidebar({ 
  conversations, 
  onSelectConversation, 
  currentConversationId,
  onNewConversation,
  onDeleteConversation
}: SidebarProps) {

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation(); // Impede que o clique no lixo também selecione a conversa
    onDeleteConversation(id);
  };

  return (
    <div className="flex flex-col h-full p-4 bg-slate-100 dark:bg-slate-900 border-r">
      <h2 className="text-lg font-semibold mb-4">Histórico</h2>
      <Button 
        variant="outline" 
        className="w-full mb-4"
        onClick={onNewConversation}
      >
        <Plus className="mr-2 h-4 w-4" />
        Nova Conversa
      </Button>
      <div className="flex-grow overflow-y-auto">
        {conversations.length === 0 ? (
          <p className="text-sm text-slate-500">Nenhuma conversa ainda.</p>
        ) : (
          <div className="flex-1 overflow-y-auto space-y-2">
            {/* Inverte a lista para mostrar as conversas mais novas primeiro */}
            {conversations.slice().reverse().map((convo) => (
              <div
                key={convo.id}
                onClick={() => onSelectConversation(convo)}
                className={`flex items-center justify-between p-2 rounded-lg cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 ${
                  currentConversationId === convo.id ? "bg-slate-200 dark:bg-slate-700" : ""
                }`}
              >
                <div className="flex items-center overflow-hidden">
                  <MessageSquare className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span className="truncate text-sm">{convo.title}</span>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-7 w-7 flex-shrink-0"
                  onClick={(e) => handleDelete(e, convo.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="mt-auto">
        <ModeToggle />
      </div>
    </div>
  );
} 