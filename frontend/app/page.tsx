"use client";

import { useState, useEffect } from "react";
import { Chat, Message } from "@/components/Chat";
import { Sidebar, Conversation } from "@/components/Sidebar";
import { SuggestedQuestions } from "@/components/SuggestedQuestions";
import { v4 as uuidv4 } from 'uuid'; // Para gerar IDs únicos

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  
  // Efeito para carregar o histórico do localStorage na inicialização
  useEffect(() => {
    const storedHistory = localStorage.getItem("maf-chat-history");
    if (storedHistory) {
      setConversations(JSON.parse(storedHistory));
    }
  }, []); // Roda apenas uma vez quando o componente é montado

  // Efeito para salvar o histórico no localStorage sempre que ele for alterado
  useEffect(() => {
    // A verificação evita salvar um array vazio antes do histórico ser carregado
    if (conversations.length > 0 || localStorage.getItem("maf-chat-history")) {
        localStorage.setItem("maf-chat-history", JSON.stringify(conversations));
    }
  }, [conversations]);

  // Efeito para salvar/atualizar a conversa no histórico
  useEffect(() => {
    // Só atualiza o histórico se houver uma conversa ativa e mensagens nela
    if (currentConversationId && messages.length > 0) {
      const updatedConversations = conversations.map(convo => 
        convo.id === currentConversationId ? { ...convo, messages: messages } : convo
      );
      // Se a conversa não estiver no histórico ainda (é uma nova), adicione-a
      if (!updatedConversations.some(c => c.id === currentConversationId)) {
        const newConversation: Conversation = {
            id: currentConversationId,
            title: messages.find(m => m.sender === 'user')?.text || "Novo Chat",
            messages: messages
        };
        setConversations(prev => [...prev, newConversation]);
      } else {
        setConversations(updatedConversations);
      }
    }
  }, [messages, currentConversationId]); // Roda sempre que as mensagens ou o ID da conversa mudam


  const sendMessageToServer = async (question: string) => {
    setIsLoading(true);
    // Adiciona a mensagem do bot vazia para mostrar o indicador de "digitando"
    setMessages((prev) => [...prev, { sender: "bot", text: "" }]);

    try {
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question }),
      });

      if (!response.ok) throw new Error("A resposta da rede não foi 'ok'.");
      if (!response.body) throw new Error("A resposta não contém um corpo.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        setMessages((prev) => {
            const newMessages = [...prev];
            const lastMessageIndex = newMessages.length - 1;
            if (lastMessageIndex >= 0 && newMessages[lastMessageIndex].sender === "bot") {
                const updatedLastMessage = { 
                    ...newMessages[lastMessageIndex],
                    text: newMessages[lastMessageIndex].text + chunk 
                };
                newMessages[lastMessageIndex] = updatedLastMessage;
            }
            return newMessages;
        });
      }

    } catch (error) {
      console.error("Houve um problema com a sua requisição:", error);
      setMessages((prev) => {
          const newMessages = [...prev];
          const lastMessageIndex = newMessages.length - 1;
          if (lastMessageIndex >= 0 && newMessages[lastMessageIndex].sender === "bot") {
            const updatedLastMessage = {
                ...newMessages[lastMessageIndex],
                text: "Desculpe, não consegui me conectar ao meu cérebro. Tente novamente mais tarde."
            };
            newMessages[lastMessageIndex] = updatedLastMessage;
          }
          return newMessages;
        });
    } finally {
      setIsLoading(false);
    }
  };
  
  const startNewOrContinueChat = async (question: string) => {
    const userMessage: Message = { sender: "user", text: question };
    let conversationId = currentConversationId;
    const newMessages = [...messages, userMessage];

    // Se não há conversa ativa, inicie uma nova
    if (!conversationId) {
        conversationId = uuidv4();
        setCurrentConversationId(conversationId);
    }
    
    setMessages(newMessages);
    await sendMessageToServer(question);
  };

  const handleSendMessage = (input: string) => {
    if (!input.trim()) return;
    startNewOrContinueChat(input);
  };
  
  const handleQuestionSelect = (question: string) => {
    startNewOrContinueChat(question);
  };

  const handleSelectConversation = (conversation: Conversation) => {
    setCurrentConversationId(conversation.id);
    setMessages(conversation.messages);
  };

  return (
    <main className="flex h-screen w-screen bg-white dark:bg-slate-950">
      {/* Coluna da Esquerda (Histórico) */}
      <div className="w-1/4 max-w-xs border-r hidden md:block">
        <Sidebar 
          conversations={conversations}
          onSelectConversation={handleSelectConversation}
          currentConversationId={currentConversationId}
        />
      </div>

      {/* Coluna Central (Chat) */}
      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <Chat 
          messages={messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
        />
      </div>

      {/* Coluna da Direita (Sugestões) */}
      <div className="w-1/4 max-w-xs border-l hidden lg:block bg-slate-50 dark:bg-slate-900/50 p-6">
        <SuggestedQuestions onQuestionSelect={handleQuestionSelect} isLoading={isLoading || messages.length > 0} />
      </div>

    </main>
  );
}
