import { useEffect, useState } from "react";
import "./App.css";

const initialMessage = {
  role: "assistant",
  content:
    "Hello. Ask me about the employee handbook, or book a Performance Review.",
};

function createThreadId() {
  return globalThis.crypto?.randomUUID?.() ?? `thread-${Date.now()}`;
}

function App() {
  const [threadId] = useState(() => {
    const saved = localStorage.getItem("people-assistant-thread");
    if (saved) return saved;
    const created = createThreadId();
    localStorage.setItem("people-assistant-thread", created);
    return created;
  });
  const [messages, setMessages] = useState(() => {
    try {
      return (
        JSON.parse(
          localStorage.getItem(`people-assistant-messages-${threadId}`),
        ) || [initialMessage]
      );
    } catch {
      return [initialMessage];
    }
  });
  const [draft, setDraft] = useState("");
  const [slots, setSlots] = useState([]);
  const [bookingStatus, setBookingStatus] = useState("not_started");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    localStorage.setItem(
      `people-assistant-messages-${threadId}`,
      JSON.stringify(messages),
    );
  }, [messages, threadId]);

  useEffect(() => {
    fetch("/api/slots")
      .then((response) => {
        if (!response.ok) throw new Error("Appointment times are unavailable.");
        return response.json();
      })
      .then(setSlots)
      .catch(() =>
        setError(
          "Could not load appointment times. Check that the backend is running.",
        ),
      );
  }, []);

  async function sendMessage(event) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || loading) return;

    setMessages((current) => [...current, { role: "user", content: message }]);
    setDraft("");
    setError("");
    setLoading(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, message }),
      });
      const result = await response.json();
      if (!response.ok)
        throw new Error(result.detail || "The assistant could not respond.");
      setMessages((current) => [
        ...current,
        { role: "assistant", content: result.response },
      ]);
      setBookingStatus(result.booking_status);
    } catch (sendError) {
      setError(
        sendError.message || "Could not reach the assistant. Try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label="People Desk home">
          <span className="wordmark-icon">P</span>
          <span>people desk</span>
        </a>
        <div className="topbar-meta">
          <span className="status-dot" /> Handbook assistant
        </div>
      </header>

      <section className="workspace" id="top">
        <div className="intro">
          <p className="eyebrow">PEOPLE OPERATIONS</p>
          <h1>How can we help?</h1>
          <p className="intro-copy">
            Get a handbook answer or arrange a Performance Review.
          </p>
        </div>

        <section className="chat-panel" aria-label="Conversation">
          <div className="chat-header">
            <div>
              <h2>Assistant</h2>
              <p>Employee handbook and reviews</p>
            </div>
            <span className={`booking-pill ${bookingStatus}`}>
              {bookingStatus === "confirmed"
                ? "Booking confirmed"
                : "Ready to help"}
            </span>
          </div>

          <div className="messages" aria-live="polite">
            {messages.map((message, index) => (
              <div
                className={`message-row ${message.role}`}
                key={`${index}-${message.role}`}
              >
                {message.role === "assistant" && (
                  <span className="assistant-mark">P</span>
                )}
                <p className="message-bubble">{message.content}</p>
              </div>
            ))}
            {loading && (
              <p className="thinking">
                <span /> Thinking
              </p>
            )}
          </div>

          {slots.length > 0 && (
            <div className="slot-strip">
              <span>AVAILABLE TIMES</span>
              <div className="slot-list">
                {slots.map((slot) => (
                  <button
                    key={slot.id}
                    type="button"
                    onClick={() => setDraft(slot.id)}
                  >
                    {slot.label.replace(" UTC", "")}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form className="composer" onSubmit={sendMessage}>
            <label className="sr-only" htmlFor="message">
              Message the assistant
            </label>
            <input
              id="message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask a question or book a review..."
              disabled={loading}
            />
            <button type="submit" disabled={!draft.trim() || loading}>
              Send <span aria-hidden="true">↗</span>
            </button>
          </form>
          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}
        </section>

        <footer className="session-footer">
          <span>Conversation saved in this browser</span>
          <code>{threadId.slice(0, 8)}</code>
        </footer>
      </section>
    </main>
  );
}

export default App;
