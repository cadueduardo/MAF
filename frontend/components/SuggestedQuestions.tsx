"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "./theme-toggle";

interface SuggestedQuestionsProps {
    onQuestionSelect: (question: string) => void;
    isLoading: boolean;
}

export function SuggestedQuestions({ onQuestionSelect, isLoading }: SuggestedQuestionsProps) {
    const [suggestions, setSuggestions] = useState<string[]>([]);

    useEffect(() => {
        const fetchSuggestions = async () => {
            try {
                const response = await fetch("/cpe/api/suggest-questions");
                if (!response.ok) {
                    throw new Error("A resposta da rede não foi 'ok'.");
                }
                const data = await response.json();
                setSuggestions(data.suggestions || []);
            } catch (error) {
                console.error("Erro ao buscar perguntas sugeridas:", error);
            }
        };

        fetchSuggestions();
    }, []);

    if (isLoading || suggestions.length === 0) return null;

    return (
        <div className="flex flex-col h-full">
            <div className="flex-grow">
                <h3 className="text-md font-semibold mb-4">Sugestões de Perguntas</h3>
                <div className="flex flex-col gap-2">
                    {suggestions.map((q, i) => (
                        <Button key={i} variant="outline" size="sm" className="h-auto whitespace-normal text-left" onClick={() => onQuestionSelect(q)}>
                            {q}
                        </Button>
                    ))}
                </div>
            </div>
            <div className="mt-auto flex justify-end">
                <ModeToggle />
            </div>
        </div>
    );
} 