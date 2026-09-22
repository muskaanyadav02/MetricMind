import {
  ArrowRight,
  Bot,
  Sparkles,
  User,
} from "lucide-react";

import { useState } from "react";

import ChartRenderer from "../components/ChartRenderer";

import "./AskAI.css";

function AskAI() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async (text = question) => {
    const clean = text.trim();

    if (!clean || loading) return;

    // Add user's question immediately
    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: clean,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/v1/chat/query",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: clean,
          }),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail ||
            "The backend could not process the question."
        );
      }

      // Add AI response with data and evidence
      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text:
            result.answer ||
            result.message ||
            "I could not find an answer for this question.",
          data: result.data || [],
          evidence: result.evidence || null,
        },
      ]);
    } catch (error) {
      console.error("MetricMind API error:", error);

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text:
            "I couldn't connect to the MetricMind backend. Please make sure the backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Which category has the highest profit?",
    "Which region has the highest sales?",
    "Show the monthly sales trend",
    "Which products have low profit?",
  ];

  return (
    <div className="ask-page">

      <div className="ask-layout">

        {/* ================= CHAT CARD ================= */}
        <div className="chat-card">

          {/* Chat header */}
          <div className="chat-header">
            <div className="ai-avatar">
              <Sparkles size={20} />
            </div>

            <div>
              <strong>MetricMind AI</strong>

              <span>
                <i></i>
                Online
              </span>
            </div>
          </div>

          {/* Chat messages */}
          <div className="chat-messages">

            {/* Empty state */}
            {messages.length === 0 && (
              <div className="empty-chat">
                <div className="empty-ai-icon">
                  <Bot size={28} />
                </div>

                <h3>Start exploring your data</h3>

                <p>
                  Ask questions about sales, profit, products,
                  regions and more.
                </p>
              </div>
            )}

            {/* Messages */}
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message ${
                  message.type === "user"
                    ? "user"
                    : "ai"
                }`}
              >
                <div className="message-icon">
                  {message.type === "user" ? (
                    <User size={17} />
                  ) : (
                    <Bot size={17} />
                  )}
                </div>

                <div className="message-content">

                  <strong>
                    {message.type === "user"
                      ? "You"
                      : "MetricMind AI"}
                  </strong>

                  <p>{message.text}</p>

                  {/* Dynamic chart */}
                  {message.type === "ai" &&
                    message.data?.length > 1 &&
                    message.evidence?.dimensions?.length > 0 && (
                      <div className="chart-wrapper">

                        <div className="chart-title">
                          {message.evidence.governed_metric} by{" "}
                          {message.evidence.dimensions[0]}
                        </div>

                        <ChartRenderer
                          data={message.data.slice(0, 10)}
                          metric={
                            message.evidence.governed_metric
                          }
                          dimension={
                            message.evidence.dimensions[0]
                          }
                        />

                        {message.data.length > 10 && (
                          <div className="chart-note">
                            Showing top 10 of{" "}
                            {message.data.length} results
                          </div>
                        )}

                      </div>
                    )}

                </div>
              </div>
            ))}

            {/* Loading state */}
            {loading && (
              <div className="message ai">

                <div className="message-icon">
                  <Bot size={17} />
                </div>

                <div className="message-content">
                  <strong>MetricMind AI</strong>

                  <p className="thinking-text">
                    Thinking...
                  </p>
                </div>

              </div>
            )}

          </div>

          {/* Input */}
          <div className="chat-input-area">

            <input
              type="text"
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  askQuestion();
                }
              }}
              placeholder="Ask a question about your business..."
              disabled={loading}
            />

            <button
              type="button"
              onClick={() => askQuestion()}
              disabled={!question.trim() || loading}
            >
              Ask
              <ArrowRight size={17} />
            </button>

          </div>

        </div>


        {/* ================= SUGGESTIONS CARD ================= */}
        <div className="suggestions-card">

          <h3>QUICK QUESTIONS</h3>

          <p>
            Try one of these questions to begin.
          </p>

          <div className="suggestion-list">

            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                type="button"
                onClick={() => askQuestion(suggestion)}
                disabled={loading}
              >
                <span>{suggestion}</span>

                <ArrowRight size={15} />
              </button>
            ))}

          </div>

        </div>

      </div>

    </div>
  );
}

export default AskAI;