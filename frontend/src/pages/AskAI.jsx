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
  const [loading, setLoading] = useState(false);

  const askQuestion = async (text = question) => {
    const clean = text.trim();

    if (!clean || loading) return;

    // Show user's question immediately
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

      // Store the complete backend response
      // so evidence can be displayed in the UI.
      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text:
            result.answer ||
            result.message ||
            "I could not find an answer for this question.",
          result: result,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text:
            "I couldn't connect to the MetricMind backend. Please make sure the backend is running.",
        },
      ]);

      console.error("MetricMind API error:", error);
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

      {/* ================= PAGE HEADING ================= */}

      <div className="page-heading">
        <div>
          <span className="eyebrow">
            AI ASSISTANT
          </span>

          <h1>
            Ask MetricMind
          </h1>

          <p>
            Ask questions about your sales, profit, products and regions.
          </p>
        </div>
      </div>


      <div className="ask-layout">

        {/* ================= CHAT CARD ================= */}

        <div className="chat-card">

          {/* ================= CHAT HEADER ================= */}

          <div className="chat-header">

            <div className="ai-avatar">
              <Sparkles size={19} />
            </div>

            <div>
              <strong>
                MetricMind AI
              </strong>

              <span>
                <i />
                {loading ? "Thinking..." : "Online"}
              </span>
            </div>

          </div>


          {/* ================= CHAT MESSAGES ================= */}

          <div className="chat-messages">

            {messages.length === 0 ? (

              <div className="empty-chat">

                <div className="empty-ai-icon">
                  <Bot size={27} />
                </div>

                <h3>
                  What would you like to know?
                </h3>

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


                    <p>
                      {message.text}
                    </p>


                    {/* ================= AI INTERPRETATION ================= */}

                    {message.type === "ai" &&
                      message.result?.evidence && (

                        <>

                          <div className="ai-interpretation">

                            <div className="interpretation-title">
                              <Sparkles size={14} />
                              AI Interpretation
                            </div>


                            <div className="interpretation-grid">

                              <div>
                                <span>
                                  Metric
                                </span>

                                <strong>
                                  {message.result.evidence
                                    .interpreted_metric || "—"}
                                </strong>
                              </div>


                              <div>
                                <span>
                                  Dimension
                                </span>

                                <strong>
                                  {message.result.evidence
                                    .interpreted_dimension || "—"}
                                </strong>
                              </div>


                              <div>
                                <span>
                                  Rows
                                </span>

                                <strong>
                                  {message.result.evidence
                                    .row_count ?? "—"}
                                </strong>
                              </div>

                            </div>

                          </div>


                          {/* ================= GOVERNED QUERY ================= */}

                          <div className="governed-badge">
                            ✓ Governed semantic query
                          </div>

                        </>

                      )}

                  </div>

                </div>

              ))

            )}


            {/* ================= LOADING STATE ================= */}

            {loading && (

              <div className="message ai">

                <div className="message-icon">
                  <Bot size={14} />
                </div>

                <div className="message-content">

                  <strong>
                    MetricMind AI
                  </strong>

                  <p>
                    Analyzing your business question...
                  </p>

                </div>

              </div>

            )}

          </div>


          {/* ================= CHAT INPUT ================= */}

          <div className="chat-input-area">

            <input
              value={question}
              onChange={(e) =>
                setQuestion(e.target.value)
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  askQuestion();
                }
              }}
              placeholder="Ask a question about your business..."
              disabled={loading}
            />


            <button
              onClick={() => askQuestion()}
              disabled={
                loading || !question.trim()
              }
            >
              {loading ? "Thinking..." : "Ask"}

              <ArrowRight size={14} />
            </button>

          </div>

        </div>


        {/* ================= QUICK QUESTIONS ================= */}

        <div className="suggestions-card">

          <span className="eyebrow">
            QUICK QUESTIONS
          </span>


          <h3>
            Start exploring your data
          </h3>


          <p>
            Try one of these questions to begin.
          </p>


          <div className="suggestion-list">

            {suggestions.map((suggestion) => (

              <button
                key={suggestion}
                onClick={() =>
                  askQuestion(suggestion)
                }
                disabled={loading}
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