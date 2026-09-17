"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const features = [
  ["Intent Intelligence", "Nine focused support intents with confidence-aware classification."],
  ["Historical Memory", "Retrieves similar real customer conversations and their resolutions."],
  ["Conversation Memory", "Maintains context across multiple customer follow-up messages."],
  ["Evidence Grounding", "Replies are constrained by retrieved historical support evidence."],
  ["Multilingual Support", "Supports English, Tamil, Tanglish, Kannada, Hindi, Malayalam and mixed-language messages."],
  ["Escalation Logic", "Low confidence, weak evidence and unclear requests can be escalated."]
];

export default function Intelligence() {
  return (
    <main className="inner-page">
      <header className="navbar">
        <Link className="brand" href="/"><span className="brand-mark">t</span><span>thunai</span></Link>
        <nav>
          <Link href="/">Home</Link>
          <Link href="/platform">Platform</Link>
          <Link className="active" href="/intelligence">Intelligence</Link>
          <Link href="/demo">Demo</Link>
          <Link href="/results">Results</Link>
        </nav>
        <Link className="nav-button" href="/demo">Try Demo →</Link>
      </header>

      <section className="page-hero">
        <div className="eyebrow"><span />INTELLIGENCE LAYER</div>
        <h1>
          Support that
          <strong> remembers.</strong>
        </h1>
        <p>
          Thunai combines intent classification, retrieval memory,
          conversational context and evidence-aware generation.
        </p>
      </section>

      <section className="feature-grid">
        {features.map(([title, text], i) => (
          <motion.div
            className="feature-card"
            key={title}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08 }}
          >
            <div className="feature-index">0{i + 1}</div>
            <h2>{title}</h2>
            <p>{text}</p>
          </motion.div>
        ))}
      </section>
    </main>
  );
}