import {
  ArrowRight,
  Bot,
  Sparkles,
  User,
} from "lucide-react";

import { useState } from "react";

import "./AskAI.css";
import ChartRenderer from "../components/ChartRenderer";


/* =========================================================
   TIME GRANULARITY DETECTION
   ========================================================= */

function getTimeGranularity(question = "") {
  const q = question.toLowerCase();

  if (/\b(month|monthly)\b/.test(q)) {
    return "Monthly";
  }

  if (/\b(quarter|quarterly)\b/.test(q)) {
    return "Quarterly";
  }

  if (
    /\b(year|yearly|annual|annually)\b/.test(q)
  ) {
    return "Yearly";
  }

  return null;
}


/* =========================================================
   AI INTERPRETATION
   ========================================================= */

function getInterpretation(message) {
  const evidence = message?.result?.evidence;

  if (!evidence) {
    return null;
  }

  /*
   * For ambiguous questions, the backend may still return
   * an interpreted metric from the initial LLM response.
   * Since no governed query was actually executed, do not
   * display that metric as if it were selected.
   */

  const isAmbiguous =
    message?.result?.status === "ambiguous";

  const metric =
    isAmbiguous
      ? "Not specified"
      : evidence.interpreted_metric || "—";

  const dimension =
    evidence.interpreted_dimension || null;

  const timeGranularity =
    evidence.time_granularity ||
    getTimeGranularity(message?.question || "");

  return {
    metric,
    dimension,
    timeGranularity,
    rows: evidence.row_count ?? "—",
  };
}


/* =========================================================
   ASK AI
   ========================================================= */

function AskAI() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);


  /* =======================================================
     ASK QUESTION
     ======================================================= */

  const askQuestion = async (text = question) => {
    const clean = text.trim();

    if (!clean || loading) {
      return;
    }


    /* =====================================================
       SHOW USER QUESTION IMMEDIATELY
       ===================================================== */

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

      /* ===================================================
         CALL BACKEND
         =================================================== */

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


      /* ===================================================
         HANDLE BACKEND ERROR
         =================================================== */

      if (!response.ok) {
        throw new Error(
          result.detail ||
            "The backend could not process the question."
        );
      }


      /* ===================================================
         STORE AI RESPONSE

         Store the original question as well.
         This allows the frontend to detect:
         Monthly / Quarterly / Yearly
         =================================================== */

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",

          text:
            result.answer ||
            result.message ||
            "I could not find an answer for this question.",

          question: clean,

          result: result,
        },
      ]);


    } catch (error) {

      /* ===================================================
         ERROR MESSAGE
         =================================================== */

      setMessages((prev) => [
        ...prev,
        {
          type: "ai",

          text:
            "I couldn't connect to the MetricMind backend. Please make sure the backend is running.",
        },
      ]);


      console.error(
        "MetricMind API error:",
        error
      );


    } finally {

      setLoading(false);

    }
  };


  /* =======================================================
     QUICK QUESTIONS
     ======================================================= */

  const suggestions = [
    "Which category has the highest profit?",
    "Which region has the highest sales?",
    "Show the monthly sales trend",
    "Which products have low profit?",
  ];


  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="ask-page">


      {/* ===================================================
          PAGE HEADING
          =================================================== */}

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


        {/* =================================================
            CHAT CARD
            ================================================= */}

        <div className="chat-card">


          {/* =================================================
              CHAT HEADER
              ================================================= */}

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

                {loading
                  ? "Thinking..."
                  : "Online"}

              </span>

            </div>

          </div>



          {/* =================================================
              CHAT MESSAGES
              ================================================= */}

          <div className="chat-messages">


            {/* =================================================
                EMPTY STATE
                ================================================= */}

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

              /* =================================================
                 MESSAGE LIST
                 ================================================= */

              messages.map((message, index) => {

                const interpretation =
                  message.type === "ai"
                    ? getInterpretation(message)
                    : null;


                return (

                  <div
                    key={index}
                    className={`message ${message.type}`}
                  >


                    {/* =========================================
                        MESSAGE ICON
                        ========================================= */}

                    <div className="message-icon">

                      {message.type === "user" ? (
                        <User size={14} />
                      ) : (
                        <Bot size={14} />
                      )}

                    </div>



                    <div className="message-content">


                      {/* =======================================
                          MESSAGE NAME
                          ======================================= */}

                      <strong>

                        {message.type === "user"
                          ? "You"
                          : "MetricMind AI"}

                      </strong>



                      {/* =======================================
                          ANSWER
                          ======================================= */}

                      <p>
                        {message.text}
                      </p>



                      {/* =======================================
                          AI INTERPRETATION
                          ======================================= */}

                      {message.type === "ai" &&
                        interpretation && (

                          <>


                            <div className="ai-interpretation">


                              <div className="interpretation-title">

                                <Sparkles size={14} />

                                AI Interpretation

                              </div>



                              <div className="interpretation-grid">


                                {/* =================================
                                    METRIC
                                    ================================= */}

                                <div className="interpretation-item">

                                  <span className="interpretation-label">
                                    Metric
                                  </span>


                                  <strong className="interpretation-value">

                                    {interpretation.metric}

                                  </strong>

                                </div>



                                {/* =================================
                                    DIMENSION / TIME
                                    ================================= */}

                                <div className="interpretation-item">

                                  <span className="interpretation-label">

                                    {interpretation.dimension
                                      ? "Dimension"
                                      : interpretation.timeGranularity
                                        ? "Time"
                                        : "Dimension"}

                                  </span>


                                  <strong className="interpretation-value">

                                    {interpretation.dimension ||
                                      interpretation.timeGranularity ||
                                      "—"}

                                  </strong>

                                </div>



                                {/* =================================
                                    ROW COUNT
                                    ================================= */}

                                <div className="interpretation-item">

                                  <span className="interpretation-label">
                                    Rows
                                  </span>


                                  <strong className="interpretation-value">

                                    {interpretation.rows}

                                  </strong>

                                </div>


                              </div>

                            </div>



                            {/* =====================================
                                AI CHART
                                ===================================== */}

                            {message.result?.data &&
                              Array.isArray(
                                message.result.data
                              ) &&
                              message.result.data.length > 0 && (

                                <div className="ai-chart">

                                  <ChartRenderer
                                    data={
                                      message.result.data
                                    }

                                    metric={
                                      message.result
                                        ?.evidence
                                        ?.interpreted_metric
                                    }

                                    dimension={
                                      message.result
                                        ?.evidence
                                        ?.interpreted_dimension
                                    }

                                  />

                                </div>

                              )}



                            {/* =====================================
                                GOVERNED QUERY BADGE
                                ===================================== */}

                            <div className="governed-badge">

                              <span>
                                ✓
                              </span>

                              Governed semantic query

                            </div>


                          </>

                        )}

                    </div>

                  </div>

                );

              })

            )}



            {/* =================================================
                LOADING STATE
                ================================================= */}

            {loading && (

              <div className="message ai">


                <div className="message-icon">

                  <Bot size={14} />

                </div>



                <div className="message-content">


                  <strong>
                    MetricMind AI
                  </strong>


                  <p className="loading-text">

                    Analyzing your business question

                    <span className="loading-dots">

                      <span>.</span>
                      <span>.</span>
                      <span>.</span>

                    </span>

                  </p>


                </div>

              </div>

            )}

          </div>



          {/* =================================================
              CHAT INPUT
              ================================================= */}

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
                loading ||
                !question.trim()
              }
            >

              {loading
                ? "Thinking..."
                : "Ask"}


              <ArrowRight size={14} />

            </button>


          </div>

        </div>



        {/* =================================================
            QUICK QUESTIONS
            ================================================= */}

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


                <span>
                  {suggestion}
                </span>


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