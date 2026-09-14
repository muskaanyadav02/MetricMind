import {
  ArrowRight,
  Bot,
  Sparkles,
  User,
} from "lucide-react";

import { useState } from "react";

import "./AskAI.css";

function AskAI() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);

  const askQuestion = (text = question) => {
    const clean = text.trim();

    if (!clean) return;

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: clean,
      },
      {
        type: "ai",
        text:
          "Based on the current business dataset, I can analyze sales, profit, quantity, categories, products, regions and trends. Connect the backend AI agent to return live analytical results.",
      },
    ]);

    setQuestion("");
  };

  const suggestions = [
    "Which category has the highest profit?",
    "Which region has the highest sales?",
    "Show the monthly sales trend",
    "Which products have low profit?",
  ];

  return (
    <div className="ask-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">AI ASSISTANT</span>
          <h1>Ask MetricMind</h1>
          <p>
            Ask questions about your sales, profit, products and regions.
          </p>
        </div>
      </div>

      <div className="ask-layout">

        <div className="chat-card">
          <div className="chat-header">
            <div className="ai-avatar">
              <Sparkles size={19} />
            </div>

            <div>
              <strong>MetricMind AI</strong>
              <span>
                <i />
                Online
              </span>
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="empty-chat">
                <div className="empty-ai-icon">
                  <Bot size={27} />
                </div>

                <h3>What would you like to know?</h3>

                <p>
                  Ask a business question and MetricMind will analyze
                  your data.
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`message ${message.type}`}
                >
                  <div className="message-icon">
                    {message.type === "user" ? (
                      <User size={14} />
                    ) : (
                      <Bot size={14} />
                    )}
                  </div>

                  <div className="message-content">
                    <strong>
                      {message.type === "user"
                        ? "You"
                        : "MetricMind AI"}
                    </strong>

                    <p>{message.text}</p>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="chat-input-area">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  askQuestion();
                }
              }}
              placeholder="Ask a question about your business..."
            />

            <button onClick={() => askQuestion()}>
              Ask
              <ArrowRight size={14} />
            </button>
          </div>
        </div>

        <div className="suggestions-card">
          <span className="eyebrow">QUICK QUESTIONS</span>

          <h3>Start exploring your data</h3>

          <p>
            Try one of these questions to begin.
          </p>

          <div className="suggestion-list">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => askQuestion(suggestion)}
              >
                <Sparkles size={14} />
                {suggestion}
                <ArrowRight size={13} />
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

export default AskAI;