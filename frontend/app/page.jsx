"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const nav = [
  ["Home", "/"],
  ["Platform", "/platform"],
  ["Intelligence", "/intelligence"],
  ["Demo", "/demo"],
  ["Results", "/results"]
];

const particles = [
  [7, 13], [14, 35], [21, 72], [29, 23], [36, 58],
  [44, 17], [51, 76], [59, 31], [66, 64], [73, 21],
  [81, 47], [88, 12], [93, 69], [97, 32]
];

export default function Home() {
  return (
    <main className="site-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <div className="particle-field">
        {particles.map(([left, top], index) => (
          <span
            key={index}
            className="particle"
            style={{
              left: `${left}%`,
              top: `${top}%`,
              animationDelay: `${index * -0.6}s`
            }}
          />
        ))}
      </div>

      <svg
        className="wave-field"
        viewBox="0 0 1600 850"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="goldWave" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#5b4300" />
            <stop offset="25%" stopColor="#ffd21a" />
            <stop offset="50%" stopColor="#fff0a0" />
            <stop offset="75%" stopColor="#ffc400" />
            <stop offset="100%" stopColor="#5b4300" />
          </linearGradient>
        </defs>

        <path
          className="wave-main"
          d="M-100 650 C140 520 260 820 530 640 S850 430 1100 615 S1390 800 1720 530"
        />
        <path
          className="wave-secondary"
          d="M-100 680 C140 550 260 850 530 670 S850 460 1100 645 S1390 830 1720 555"
        />
      </svg>

      <header className="navbar">
        <Link href="/" className="brand">
          <span className="brand-mark">t</span>
          <span>thunai</span>
        </Link>

        <nav>
          {nav.map(([name, href], index) => (
            <Link
              key={name}
              href={href}
              className={index === 0 ? "active" : ""}
            >
              {name}
            </Link>
          ))}
        </nav>

        <Link href="/demo" className="nav-button">
          Try Demo <span>→</span>
        </Link>
      </header>

      <section className="hero">
        <motion.div
          className="hero-copy"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.7,
            ease: [0.22, 1, 0.36, 1]
          }}
        >
          <div className="eyebrow">
            <span />
            AI SUPPORT AGENT
          </div>

          <h1>
            AI Support That
            <br />
            Knows <strong>When to Act.</strong>
          </h1>

          <p>
            Thunai understands customer intent, retrieves relevant historical
            evidence, and decides whether to respond or escalate — automatically.
          </p>

          <div className="actions">
            <Link href="/demo" className="primary-button">
              Explore Agent <span>→</span>
            </Link>

            <Link href="/demo" className="secondary-button">
              <span className="play">▶</span>
              Watch Demo
            </Link>
          </div>
        </motion.div>

        <motion.div
          className="product-wrap"
          initial={{ opacity: 0, x: 45 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{
            duration: 0.8,
            delay: 0.1,
            ease: [0.22, 1, 0.36, 1]
          }}
        >
          <div className="product-card">
            <div className="chat-panel">
              <div className="panel-head">
                <div className="mini-brand">
                  <span>t</span>
                  thunai
                </div>

                <div className="online">
                  <i />
                  Online
                </div>
              </div>

              <div className="chat-body">
                <div className="customer-msg">
                  Where is my order? It’s been more than a week now.
                </div>

                <div className="agent-msg">
                  <span className="agent-icon">t</span>
                  I’m sorry for the delay. Let me check the relevant information
                  and help you with the next step.
                </div>
              </div>

              <div className="input-bar">
                <span>Type a message...</span>
                <b>➤</b>
              </div>
            </div>

            <div className="analysis-panel">
              <div className="analysis-title">
                <span>✦</span>
                AI Analysis
              </div>

              <div className="metric">
                <span>Intent</span>
                <b>delivery_delay</b>
              </div>

              <div className="metric">
                <span>Confidence</span>
                <div className="confidence">
                  <b>94%</b>
                  <i>
                    <em />
                  </i>
                </div>
              </div>

              <div className="metric">
                <span>Evidence</span>
                <b>
                  3 matches <small>›</small>
                </b>
              </div>

              <div className="decision">
                ✓ &nbsp; AUTO_HANDLE
              </div>

              <div className="evidence">
                <div>Relevant Evidence</div>

                <p>
                  Order marked delayed...
                  <b>92%</b>
                </p>

                <p>
                  Similar cases (2)
                  <b>87%</b>
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <div className="scroll-cue">
        <span>SCROLL TO EXPLORE</span>
        <i />
      </div>

      <footer className="footer">
        <div>
          <span className="footer-mark">t</span>
          thunai
          <b />
          Smarter support. Happier customers.
        </div>

        <div>
          ✦ &nbsp; Powered by AI &nbsp; / &nbsp; Built for real support
        </div>
      </footer>
    </main>
  );
}