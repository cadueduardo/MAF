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
    try {
      const storedHistory = localStorage.getItem("maf-chat-history");
      if (storedHistory) {
        const loadedConversations: Conversation[] = JSON.parse(storedHistory);
        setConversations(loadedConversations);

        // MODIFICADO: Carrega a última conversa ao iniciar
        if (loadedConversations.length > 0) {
          const lastConversation = loadedConversations[loadedConversations.length - 1];
          setCurrentConversationId(lastConversation.id);
          setMessages(lastConversation.messages);
        }
      }
    } catch (error) {
      console.error("Falha ao ler o histórico do chat:", error);
      // Limpa o histórico corrompido para evitar erros futuros.
      localStorage.removeItem("maf-chat-history");
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
    // Só roda se houver uma conversa ativa e mensagens para salvar.
    if (currentConversationId && messages.length > 0) {
      setConversations(prevConversations => {
        const conversationExists = prevConversations.some(c => c.id === currentConversationId);
  
        if (conversationExists) {
          // A conversa já existe, então apenas atualiza as mensagens dela.
          return prevConversations.map(convo =>
            convo.id === currentConversationId ? { ...convo, messages: messages } : convo
          );
        } else {
          // É uma nova conversa, então a adiciona ao histórico.
          const newConversation: Conversation = {
            id: currentConversationId,
            // Pega o texto da primeira mensagem do usuário como título.
            title: messages.find(m => m.sender === 'user')?.text.substring(0, 30) || "Novo Chat",
            messages: messages,
          };
          return [...prevConversations, newConversation];
        }
      });
    }
  }, [messages, currentConversationId]); // Roda sempre que as mensagens ou o ID da conversa mudam


  const handleSendMessage = async (question: string) => {
    if (!question.trim() || isLoading) return;
    setIsLoading(true);

    const userMessage: Message = { sender: "user", text: question };
    const historyForAPI = [...messages]; // Histórico ANTES de adicionar a nova pergunta do usuário

    // Garante que temos um ID para a conversa
    let convId = currentConversationId;
    if (!convId) {
      convId = uuidv4();
      setCurrentConversationId(convId);
    }
    
    // Atualiza a interface com a mensagem do usuário e o indicador de "digitando..." do bot
    setMessages(prev => [...prev, userMessage, { sender: "bot", text: "" }]);

    try {
      const response = await fetch("/cpe/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question, history: historyForAPI }),
      });

      if (!response.ok) throw new Error("A resposta da rede não foi 'ok'.");
      if (!response.body) throw new Error("A resposta não contém um corpo.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let firstChunk = true; // Flag para lidar com o primeiro pedaço da resposta

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMessageIndex = newMessages.length - 1;
          
          if (lastMessageIndex >= 0 && newMessages[lastMessageIndex].sender === "bot") {
            // No primeiro chunk, substitui o "digitando...". Nos seguintes, anexa.
            const newText = firstChunk ? chunk : newMessages[lastMessageIndex].text + chunk;
            firstChunk = false;
            
            newMessages[lastMessageIndex] = { ...newMessages[lastMessageIndex], text: newText };
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
          newMessages[lastMessageIndex] = {
            ...newMessages[lastMessageIndex],
            text: "Desculpe, não consegui me conectar ao meu cérebro. Tente novamente mais tarde."
          };
        }
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleQuestionSelect = (question: string) => {
    handleSendMessage(question);
  };

  const handleSelectConversation = (conversation: Conversation) => {
    setCurrentConversationId(conversation.id);
    setMessages(conversation.messages);
  };

  // NOVO: Handler para iniciar uma nova conversa
  const handleNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
  };

  // NOVO: Handler para deletar uma conversa
  const handleDeleteConversation = (id: string) => {
    setConversations(prev => prev.filter(convo => convo.id !== id));
    
    // Se a conversa deletada era a ativa, limpa a tela de chat
    if (currentConversationId === id) {
      handleNewConversation();
    }
  };

  return (
    <main className="flex h-screen w-screen bg-white dark:bg-slate-950">
      {/* Coluna da Esquerda (Histórico) */}
      <div className="w-1/4 max-w-xs border-r hidden md:block">
        <Sidebar 
          conversations={conversations}
          onSelectConversation={handleSelectConversation}
          currentConversationId={currentConversationId}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
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
