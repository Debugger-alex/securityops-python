import { useCallback, useEffect, useState } from "react";
import { getNotifications, markNotificationRead } from "./api";
import type { NotificationItem } from "./types";

const pageSize = 25;

function messageFrom(reason: unknown, fallback: string) {
  return reason instanceof Error ? reason.message : fallback;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("de-DE");
}

export default function NotificationManagement() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const page = await getNotifications({ limit: pageSize, offset });
      setItems(page.items);
      setTotal(page.total);
      setUnreadCount(page.unread_count);
      setError("");
    } catch (reason) {
      setError(messageFrom(reason, "Benachrichtigungen konnten nicht geladen werden."));
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  async function markAsRead(notificationId: string) {
    setBusyId(notificationId);
    try {
      await markNotificationRead(notificationId);
      await loadNotifications();
    } catch (reason) {
      setError(messageFrom(reason, "Benachrichtigung konnte nicht aktualisiert werden."));
    } finally {
      setBusyId("");
    }
  }

  return (
    <section className="notification-module">
      <section className="panel" aria-labelledby="notifications-heading">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">POSTEINGANG</p>
            <h2 id="notifications-heading">Benachrichtigungen</h2>
          </div>
          <span className="result-count">{unreadCount} ungelesen</span>
        </div>
        {error && <p className="alert" role="alert">{error}</p>}
        {loading
          ? <p className="muted" role="status">Benachrichtigungen werden geladen …</p>
          : items.length === 0
          ? <p className="empty">Keine Benachrichtigungen vorhanden.</p>
          : <ul className="notification-list">
            {items.map((item) => (
              <li key={item.id} className={item.read_at ? "notification-read" : ""}>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.body}</p>
                  <time dateTime={item.created_at}>{formatDate(item.created_at)}</time>
                </div>
                {item.read_at
                  ? <span className="notification-status">Gelesen</span>
                  : <button
                    className="secondary-button"
                    disabled={busyId === item.id}
                    onClick={() => void markAsRead(item.id)}
                  >
                    {busyId === item.id ? "Wird gespeichert …" : "Als gelesen markieren"}
                  </button>}
              </li>
            ))}
          </ul>}
        <div className="pagination">
          <span className="result-count">
            {total === 0 ? "0 Einträge" : `${offset + 1}–${Math.min(offset + pageSize, total)} von ${total}`}
          </span>
          <div>
            <button
              className="secondary-button"
              disabled={offset === 0 || loading}
              onClick={() => setOffset((current) => Math.max(0, current - pageSize))}
            >
              Zurück
            </button>
            <button
              className="secondary-button"
              disabled={offset + pageSize >= total || loading}
              onClick={() => setOffset((current) => current + pageSize)}
            >
              Weiter
            </button>
          </div>
        </div>
      </section>
    </section>
  );
}
