import { useState, useEffect, useRef } from "react";
import { api } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Send, Loader2, Trash2, FileText } from "lucide-react";
import { cn } from "../lib/utils";

// Render message text with clickable citations
const renderMessageWithCitations = (text) => {
    // Match patterns like [documento.pdf] or [1] filename.pdf
    const citationRegex = /\[([^\]]+\.(pdf|docx|txt|md|html))\]|\[(\d+)\]\s*([^\s,\.\n]+\.(pdf|docx|txt|md|html))/gi;

    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
        // Add text before citation
        if (match.index > lastIndex) {
            parts.push(<span key={`text-${lastIndex}`}>{text.slice(lastIndex, match.index)}</span>);
        }

        // Extract filename from match
        const filename = match[1] || match[4];

        // Add citation badge
        parts.push(
            <span
                key={`cite-${match.index}`}
                className="inline-flex items-center gap-1 px-2 py-0.5 mx-0.5 text-xs bg-primary/20 text-primary rounded-full cursor-pointer hover:bg-primary/30 transition-colors"
                title={`Fuente: ${filename}`}
            >
                <FileText className="h-3 w-3" />
                {filename.length > 20 ? filename.slice(0, 20) + "..." : filename}
            </span>
        );

        lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
        parts.push(<span key={`text-${lastIndex}`}>{text.slice(lastIndex)}</span>);
    }

    return parts.length > 0 ? parts : text;
};


export default function ChatPage() {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load chat history on mount
    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const data = await api.chatHistory.getHistory();
            const historyMessages = (data.messages || []).map(msg => ({
                role: msg.role,
                text: msg.message
            }));
            setMessages(historyMessages);
        } catch (err) {
            console.error("Error loading history:", err);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userText = input;
        setInput("");
        setLoading(true);

        // Optimistic update
        setMessages((prev) => [...prev, { role: "user", text: userText }]);

        try {
            const data = await api.chatHistory.sendMessage(userText);
            // Replace optimistic message with server response
            setMessages((prev) => [
                ...prev.slice(0, -1),
                { role: "user", text: data.user_message.message },
                { role: "bot", text: data.bot_message.message }
            ]);
        } catch (err) {
            console.error(err);
            setMessages((prev) => [...prev, { role: "bot", text: "Error sending message" }]);
        } finally {
            setLoading(false);
        }
    };

    const handleClearHistory = async () => {
        if (!confirm("Are you sure you want to clear chat history?")) return;

        try {
            await api.chatHistory.clearHistory();
            setMessages([]);
        } catch (err) {
            console.error("Error clearing history:", err);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-6rem)] gap-4">
            <Card className="flex-1 flex flex-col overflow-hidden border-0 shadow-none bg-transparent">
                <CardHeader className="px-0 pt-0 flex flex-row items-center justify-between">
                    <CardTitle>Chat Assistant</CardTitle>
                    {messages.length > 0 && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleClearHistory}
                            className="text-destructive hover:text-destructive"
                        >
                            <Trash2 className="h-3 w-3 mr-1" />
                            Clear History
                        </Button>
                    )}
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 bg-card/50 rounded-lg border backdrop-blur-sm">
                    {messages.length === 0 && (
                        <div className="text-center text-muted-foreground mt-10">
                            Start a conversation...
                        </div>
                    )}
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={cn(
                                "flex w-full",
                                msg.role === "user" ? "justify-end" : "justify-start"
                            )}
                        >
                            <div
                                className={cn(
                                    "max-w-[80%] rounded-lg px-4 py-2 text-sm",
                                    msg.role === "user"
                                        ? "bg-gradient-to-r from-primary to-secondary text-primary-foreground"
                                        : "bg-muted text-foreground"
                                )}
                            >
                                {msg.role === "bot" ? renderMessageWithCitations(msg.text) : msg.text}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-muted rounded-lg px-4 py-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </CardContent>
            </Card>

            <form onSubmit={handleSend} className="flex gap-2">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 bg-input text-foreground placeholder:text-muted-foreground border-border focus:ring-primary"
                    disabled={loading}
                />
                <Button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="bg-gradient-to-r from-primary to-secondary hover:opacity-90 transition-opacity"
                >
                    <Send className="h-4 w-4" />
                </Button>
            </form>
        </div>
    );
}
