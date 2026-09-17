"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const steps = [
  ["01", "Customer Message", "Understand what the customer is asking."],
  ["02", "Intent Detection", "Classify the request into a focused support intent."],
  ["03", "Historical Retrieval", "Find similar resolved AmazonHelp conversations."],
  ["04", "Evidence-Grounded Reply", "Generate a response using retrieved evidence."],
  ["05", "Action Decision", "Automatically handle safe cases or escalate them."]
];

export default function Platform() {
  return (
    <main className="inner-page">
      <header className="navbar">
        <Link className="brand" href="/"><span className="brand-mark">t</span><span>thunai</span></Link>
        <nav>
          <Link href="/">Home</Link>
          <Link className="active" href="/platform">Platform</Link>
          <Link href="/intelligence">Intelligence</Link>
          <Link href="/demo">Demo</Link>
          <Link href="/results">Results</Link>
        </nav>
        <Link className="nav-button" href="/demo">Try Demo →</Link>
      </header>

      <section className="page-hero">
        <div className="eyebrow"><span />HOW THUNAI WORKS</div>
        <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}>
          From message to
          <strong> action.</strong>
        </motion.h1>
        <p>
          A support pipeline designed to understand, retrieve, respond and
          make a decision with evidence at every stage.
        </p>
      </section>

      <section className="process-grid">
        {steps.map(([number, title, text], i) => (
          <motion.div
            className="process-card"
            key={number}
            initial={{ opacity: 0, y: 35 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08 }}
          >
            <span>{number}</span>
            <h2>{title}</h2>
            <p>{text}</p>
            <div className="connector" />
          </motion.div>
        ))}
      </section>
    </main>
  );
}