"use client";

import { useState } from "react";
import Link from "next/link";

const API_URL = "http://127.0.0.1:8000";

export default function Demo() {
  const [message, setMessage] = useState("");
  const [conversationId] = useState("demo-001");
  const [messages, setMessages] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function sendMessage(e) {
    e.preventDefault();

    const text = message.trim();

    if (!text || loading) return;

    setMessages((prev) => [
      ...prev,
      { role: "customer", content: text }
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: text
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || `Request failed with ${response.status}`
        );
      }

      setResult(data);

      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: data.reply?.reply || "No reply was returned."
        }
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: `Unable to connect to Thunai: ${error.message}`
        }
      ]);

      setResult({
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  }

  const intent = result?.intent;
  const reply = result?.reply;
  const escalation = result?.escalation;
  const matches = result?.historical_matches || [];

  return (
    <main className="inner-page">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="navbar">
        <Link href="/" className="brand">
          <span className="brand-mark">t</span>
          <span>thunai</span>
        </Link>

        <nav>
          <Link href="/">Home</Link>
          <Link href="/platform">Platform</Link>
          <Link href="/intelligence">Intelligence</Link>
          <Link href="/demo" className="active">Demo</Link>
          <Link href="/results">Results</Link>
        </nav>

        <Link href="/demo" className="nav-button">
          Try Demo →
        </Link>
      </header>

      <section className="demo-page">
        <div className="page-hero compact">
          <div className="eyebrow">
            <span />
            LIVE AGENT
          </div>

          <h1>
            Talk to <strong>thunai.</strong>
          </h1>

          <p>
            Send a real support request through the Thunai intelligence
            pipeline and inspect how the agent reaches its decision.
          </p>
        </div>

        <div className="demo-layout">
          <section className="demo-chat">
            <div className="demo-head">
              <div>
                <div className="demo-title">Customer Support</div>

                <div className="demo-status">
                  <i />
                  Thunai agent online
                </div>
              </div>

              <div className="conversation-id">
                {conversationId}
              </div>
            </div>

            <div className="demo-messages">
              {messages.length === 0 && (
                <div className="demo-empty">
                  <div className="demo-empty-mark">t</div>

                  <h3>Start a conversation</h3>

                  <p>
                    Try a real customer-support message such as:
                  </p>

                  <div className="suggestion">
                    “My order says delivered but I never received it.”
                  </div>
                </div>
              )}

              {messages.map((item, index) => (
                <div
                  key={index}
                  className={
                    item.role === "customer"
                      ? "message-row customer-row"
                      : "message-row agent-row"
                  }
                >
                  <div
                    className={
                      item.role === "customer"
                        ? "message-label customer-label"
                        : "message-label agent-label"
                    }
                  >
                    {item.role === "customer" ? "YOU" : "THUNAI"}
                  </div>

                  <div
                    className={
                      item.role === "customer"
                        ? "message-bubble customer-bubble"
                        : "message-bubble agent-bubble"
                    }
                  >
                    {item.content}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-row agent-row">
                  <div className="message-label agent-label">
                    THUNAI
                  </div>

                  <div className="message-bubble agent-bubble thinking">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              )}
            </div>

            <form className="demo-input" onSubmit={sendMessage}>
              <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Describe the customer's issue..."
                disabled={loading}
              />

              <button
                type="submit"
                disabled={loading || !message.trim()}
              >
                {loading ? "Analyzing..." : "Send"}
              </button>
            </form>
          </section>

          <aside className="demo-analysis">
            <div className="analysis-header">
              <div className="analysis-title">
                <span>✦</span>
                AI Analysis
              </div>

              {result && !result.error && (
                <div className="analysis-live">
                  LIVE
                </div>
              )}
            </div>

            {result?.error ? (
              <div className="analysis-error">
                <strong>Request failed</strong>
                <p>{result.error}</p>
              </div>
            ) : (
              <>
                <div className="analysis-block">
                  <div className="analysis-label">
                    DETECTED INTENT
                  </div>

                  <div className="intent-value">
                    {intent?.intent || "waiting"}
                  </div>

                  {intent?.reason && (
                    <p className="analysis-description">
                      {intent.reason}
                    </p>
                  )}
                </div>

                <div className="analysis-metrics">
                  <div className="analysis-metric">
                    <span>Confidence</span>
                    <b>
                      {intent
                        ? `${Math.round(intent.confidence * 100)}%`
                        : "—"}
                    </b>
                  </div>

                  <div className="analysis-metric">
                    <span>Historical matches</span>
                    <b>
                      {result ? matches.length : "—"}
                    </b>
                  </div>

                  <div className="analysis-metric">
                    <span>Evidence status</span>
                    <b>
                      {reply
                        ? reply.evidence_sufficient
                          ? "Sufficient"
                          : "Insufficient"
                        : "—"}
                    </b>
                  </div>
                </div>

                <div
                  className={`decision large ${
                    escalation?.decision === "ESCALATE"
                      ? "escalate"
                      : ""
                  }`}
                >
                  {escalation?.decision || "WAITING"}
                </div>

                <div className="analysis-block">
                  <div className="analysis-label">
                    DECISION REASON
                  </div>

                  <p className="analysis-description">
                    {escalation?.reason ||
                      "Thunai will explain why the request can be handled automatically or needs escalation."}
                  </p>
                </div>

                <div className="analysis-block">
                  <div className="analysis-label">
                    REPLY EVIDENCE
                  </div>

                  {reply?.evidence?.length ? (
                    reply.evidence.map((item, index) => (
                      <div className="evidence-item" key={index}>
                        <span>
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        {item}
                      </div>
                    ))
                  ) : (
                    <p className="analysis-description">
                      No evidence has been retrieved yet.
                    </p>
                  )}
                </div>

                <div className="analysis-block">
                  <div className="analysis-label">
                    HISTORICAL RETRIEVAL
                  </div>

                  {matches.length ? (
                    matches.map((match, index) => (
                      <div className="retrieved-card" key={index}>
                        <div className="retrieved-top">
                          <span>
                            MATCH {String(index + 1).padStart(2, "0")}
                          </span>

                          <b>
                            {Math.round(match.similarity * 100)}%
                          </b>
                        </div>

                        <p>
                          {match.customer_message}
                        </p>

                        <div className="retrieved-response">
                          {match.historical_response}
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="analysis-description">
                      No historical matches yet.
                    </p>
                  )}
                </div>
              </>
            )}
          </aside>
        </div>
      </section>

      <style jsx global>{`
        .demo-page {
          width: min(1500px, calc(100% - 64px));
          margin: 0 auto;
          font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .page-hero.compact {
          margin-bottom: 30px;
        }

        .page-hero.compact h1 {
          letter-spacing: -0.045em;
        }

        .demo-layout {
          display: grid;
          grid-template-columns: minmax(0, 3.8fr) minmax(250px, 0.9fr);
          gap: 16px;
          align-items: stretch;
        }

        .demo-chat {
          min-width: 0;
          min-height: 650px;
          height: 650px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          border-radius: 20px;
        }

        .demo-head {
          flex: 0 0 auto;
        }

        .demo-messages {
          flex: 1 1 auto;
          min-height: 0;
          overflow-y: auto;
          padding: 28px 30px;
          scroll-behavior: smooth;
        }

        .demo-messages::-webkit-scrollbar,
        .demo-analysis::-webkit-scrollbar {
          width: 5px;
        }

        .demo-messages::-webkit-scrollbar-thumb,
        .demo-analysis::-webkit-scrollbar-thumb {
          border-radius: 99px;
          background: rgba(255, 255, 255, 0.12);
        }

        .demo-input {
          flex: 0 0 auto;
          margin: 0;
          padding: 16px;
        }

        .demo-input input,
        .demo-input button {
          font-family: inherit;
        }

        .demo-input input {
          font-size: 15px;
        }

        .demo-analysis {
          min-width: 0;
          max-height: 650px;
          overflow-y: auto;
          padding: 17px;
          border-radius: 20px;
        }

        .analysis-header {
          margin-bottom: 17px;
        }

        .analysis-block {
          margin-bottom: 17px;
        }

        .analysis-label {
          font-size: 10px;
          letter-spacing: 0.13em;
          line-height: 1.4;
        }

        .intent-value {
          font-size: 17px;
          line-height: 1.35;
          margin-top: 5px;
        }

        .analysis-description {
          font-size: 12px;
          line-height: 1.5;
          margin-top: 7px;
        }

        .analysis-metrics {
          gap: 7px;
          margin-bottom: 15px;
        }

        .analysis-metric {
          padding: 9px 10px;
        }

        .analysis-metric span {
          font-size: 10px;
        }

        .analysis-metric b {
          font-size: 12px;
        }

        .decision.large {
          margin-bottom: 17px;
          padding: 9px 11px;
          font-size: 10px;
          letter-spacing: 0.12em;
        }

        .evidence-item {
          font-size: 11px;
          line-height: 1.45;
          padding: 8px 0;
        }

        .retrieved-card {
          padding: 10px;
          margin-bottom: 7px;
        }

        .retrieved-card p,
        .retrieved-response {
          font-size: 11px;
          line-height: 1.4;
        }

        .message-bubble.thinking {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          min-width: 48px;
          min-height: 34px;
          padding: 9px 13px;
        }

        .message-bubble.thinking span {
          display: block;
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: currentColor;
          opacity: 0.35;
          animation: thunaiThinking 1.15s infinite ease-in-out;
        }

        .message-bubble.thinking span:nth-child(2) {
          animation-delay: 0.15s;
        }

        .message-bubble.thinking span:nth-child(3) {
          animation-delay: 0.3s;
        }

        @keyframes thunaiThinking {
          0%,
          60%,
          100% {
            transform: translateY(0);
            opacity: 0.35;
          }

          30% {
            transform: translateY(-4px);
            opacity: 1;
          }
        }

        @media (max-width: 1000px) {
          .demo-page {
            width: min(calc(100% - 32px), 900px);
          }

          .demo-layout {
            grid-template-columns: 1fr;
          }

          .demo-chat {
            height: 620px;
          }

          .demo-analysis {
            max-height: none;
          }
        }

        @media (max-width: 640px) {
          .demo-page {
            width: calc(100% - 20px);
          }

          .demo-chat {
            min-height: 560px;
            height: 560px;
            border-radius: 16px;
          }

          .demo-analysis {
            border-radius: 16px;
          }

          .demo-messages {
            padding: 20px 16px;
          }

          .demo-input {
            padding: 10px;
          }
        }
      `}</style>
    </main>
  );
}