
import {
  ArrowRight,
  Bot,
  Sparkles,
  User,
} from "lucide-react";

import { useState } from "react";

import ChartCard from "../components/ChartCard";
import "./AskAI.css";

// Check whether a value can safely be plotted as a number.
function isNumericValue(value) {
  if (typeof value === "number") {
    return Number.isFinite(value);
  }

  return (
    typeof value === "string" &&
    value.trim() !== "" &&
    Number.isFinite(Number(value))
  );
}

// Build chart configuration from the actual backend response.
function buildChartConfig(result) {
  const rows = Array.isArray(result?.data)
    ? result.data.filter(
        (row) =>
          row &&
          typeof row === "object" &&
          !Array.isArray(row)
      )
    : [];

  if (rows.length === 0) return null;

  const evidence = result.evidence || {};
  const query = evidence.governed_query || {};
  const firstRow = rows[0];
  const rowKeys = Object.keys(firstRow);

  const dimensionCandidates = [
    ...(Array.isArray(evidence.dimensions)
      ? evidence.dimensions
      : []),
    ...(Array.isArray(query.dimensions)
      ? query.dimensions
      : []),
    ...(Array.isArray(query.time_dimensions)
      ? query.time_dimensions.map((item) =>
          typeof item === "string"
            ? item
            : item?.dimension
        )
      : []),
  ].filter((key) => typeof key === "string");

  const xKey =
    dimensionCandidates.find((key) =>
      Object.prototype.hasOwnProperty.call(firstRow, key)
    ) ||
    rowKeys.find(
      (key) => !isNumericValue(firstRow[key])
    );

  const metricCandidates = [
    ...(Array.isArray(query.measures)
      ? query.measures
      : []),
    evidence.governed_metric,
  ].filter((key) => typeof key === "string");

  const dataKey =
    metricCandidates.find(
      (key) =>
        Object.prototype.hasOwnProperty.call(firstRow, key) &&
        isNumericValue(firstRow[key])
    ) ||
    rowKeys.find(
      (key) =>
        key !== xKey &&
        isNumericValue(firstRow[key])
    );

  if (!xKey || !dataKey) return null;

  const chartData = rows
    .filter(
      (row) =>
        row[xKey] != null &&
        isNumericValue(row[dataKey])
    )
    .map((row) => ({
      ...row,
      [dataKey]: Number(row[dataKey]),
    }));

  if (chartData.length === 0) return null;

  const timeDimensions = Array.isArray(query.time_dimensions)
    ? query.time_dimensions
    : [];

  const isTimeSeries =
    timeDimensions.length > 0 ||
    /month|year|date|day|quarter/i.test(xKey);

  return {
    title: `${dataKey} by ${xKey}`,
    subtitle: `${chartData.length} result row(s)`,
    data: chartData,
    dataKey,
    xKey,
    type: isTimeSeries ? "area" : "bar",
  };
}

// Generate deterministic follow-up questions locally.
// No additional backend or LLM request is made here.
function buildFollowUpSuggestions(result, question) {
  const normalizedQuestion = question.toLowerCase();

  const evidence = result?.evidence || {};
  const query = evidence.governed_query || {};

  const context = [
    normalizedQuestion,
    ...(Array.isArray(query.measures) ? query.measures : []),
    ...(Array.isArray(query.dimensions) ? query.dimensions : []),
    ...(Array.isArray(evidence.dimensions)
      ? evidence.dimensions
      : []),
  ]
    .filter((value) => typeof value === "string")
    .join(" ")
    .toLowerCase();

  let candidates;

  if (/profit|margin|loss/.test(context)) {
    candidates = [
      "Which category has the highest profit?",
      "Which region has the lowest profit?",
      "Show the yearly profit trend",
      "Which products have low profit?",
      "Which region has the highest sales?",
    ];
  } else if (/sales|revenue|turnover/.test(context)) {
    candidates = [
      "Which category has the highest sales?",
      "Which region has the highest sales?",
      "Show the monthly sales trend",
      "Which products generate the most profit?",
      "Compare sales across countries",
    ];
  } else if (/product|sub.?categor|category/.test(context)) {
    candidates = [
      "Which products have the highest profit?",
      "Which category has the highest sales?",
      "Which products have low profit?",
      "Which region has the highest sales?",
      "Show the yearly profit trend",
    ];
  } else if (/region|country|market/.test(context)) {
    candidates = [
      "Which region has the highest sales?",
      "Which category has the highest profit?",
      "Compare sales across countries",
      "Show the monthly sales trend",
      "Which products have low profit?",
    ];
  } else if (/month|year|date|trend|time/.test(context)) {
    candidates = [
      "Show the monthly sales trend",
      "Show the yearly profit trend",
      "Which category has the highest profit?",
      "Which region has the highest sales?",
      "Which products have low profit?",
    ];
  } else {
    candidates = [
      "Which category has the highest profit?",
      "Which region has the highest sales?",
      "Show the monthly sales trend",
      "Which products have low profit?",
      "Compare sales across countries",
    ];
  }

  // Do not suggest the exact question the user just asked.
  const normalizedCurrentQuestion = question
    .trim()
    .toLowerCase()
    .replace(/[?!.\s]+$/, "");

  const uniqueSuggestions = [
    ...new Set(candidates),
  ].filter(
    (suggestion) =>
      suggestion
        .trim()
        .toLowerCase()
        .replace(/[?!.\s]+$/, "") !== normalizedCurrentQuestion
  );

  return uniqueSuggestions.slice(0, 3);
}

function AskAI() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const askQuestion = async (text = question) => {
    const clean = text.trim();

    if (!clean || loading) return;

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
        const detail =
          typeof result.detail === "string"
            ? result.detail
            : "The backend could not process the question.";

        throw new Error(detail);
      }

      const isAnswered = result.status === "answered";

      const chart = isAnswered
        ? buildChartConfig(result)
        : null;

      const followUps = isAnswered
        ? buildFollowUpSuggestions(result, clean)
        : [];

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text:
            result.answer ||
            result.message ||
            "I could not find an answer for this question.",
          chart,
          followUps,
        },
      ]);
    } catch (error) {
      console.error("MetricMind API error:", error);

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text:
            error instanceof TypeError
              ? "I couldn't connect to the MetricMind backend. Please make sure the backend is running."
              : error.message ||
                "Something went wrong while processing your question.",
          chart: null,
          followUps: [],
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
                {loading ? "Thinking..." : "Online"}
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

                    {message.type === "ai" &&
                      message.chart && (
                        <div className="message-chart">
                          <ChartCard {...message.chart} />
                        </div>
                      )}

                    {message.type === "ai" &&
                      message.followUps?.length > 0 && (
                        <div className="follow-up-suggestions">
                          <div className="follow-up-title">
                            <Sparkles size={13} />
                            Explore further
                          </div>

                          <div className="follow-up-list">
                            {message.followUps.map(
                              (followUp) => (
                                <button
                                  key={followUp}
                                  type="button"
                                  onClick={() =>
                                    askQuestion(followUp)
                                  }
                                  disabled={loading}
                                  title={followUp}
                                >
                                  <span>{followUp}</span>
                                  <ArrowRight size={13} />
                                </button>
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              ))
            )}

            {loading && (
              <div className="message ai">
                <div className="message-icon">
                  <Bot size={14} />
                </div>

                <div className="message-content">
                  <strong>MetricMind AI</strong>
                  <p>Analyzing your business question...</p>
                </div>
              </div>
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
              disabled={loading}
            />

            <button
              type="button"
              onClick={() => askQuestion()}
              disabled={loading || !question.trim()}
            >
              {loading ? "Thinking..." : "Ask"}
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
                type="button"
                onClick={() => askQuestion(suggestion)}
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