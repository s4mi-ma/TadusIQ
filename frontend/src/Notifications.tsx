import { createContext, useCallback, useContext, useRef, useState } from 'react';
import type { ReactNode } from 'react';

type Tone = 'error' | 'warning';
type Notify = (title: string, description: string, tone?: Tone) => void;
type Notice = { id: number; title: string; description: string; tone: Tone; origin: HTMLElement | null };
const NotificationContext = createContext<Notify | null>(null);

export function useNotify() {
  const notify = useContext(NotificationContext);
  if (!notify) throw new Error('Notifications require their provider.');
  return notify;
}

export function Notifications({ children }: { children: ReactNode }) {
  const [notices, setNotices] = useState<Notice[]>([]);
  const nextId = useRef(0);
  const notify = useCallback<Notify>((title, description, tone = 'error') => {
    const notice = { id: ++nextId.current, title, description, tone,
      origin: document.activeElement instanceof HTMLElement ? document.activeElement : null };
    setNotices(previous => [...previous.filter(item => item.title !== title || item.description !== description), notice].slice(-3));
  }, []);
  function dismiss(notice: Notice) {
    setNotices(previous => previous.filter(item => item.id !== notice.id));
    if (notice.origin?.isConnected && notice.origin.getClientRects().length) notice.origin.focus({ preventScroll: true });
  }
  return <NotificationContext value={notify}>{children}<aside className="notifications" aria-label="Notifications">
    {notices.map(notice => <div key={notice.id} className={`toast toast-${notice.tone}`} onKeyDown={event => {
      if (event.key === 'Escape') { event.preventDefault(); dismiss(notice); }
    }}>
      <span className="toast-symbol" aria-hidden="true">!</span>
      <div role={notice.tone === 'error' ? 'alert' : 'status'} aria-atomic="true"><strong>{notice.title}</strong><p>{notice.description}</p></div>
      <button className="icon-button" type="button" aria-label={`Dismiss ${notice.title}`} onClick={() => dismiss(notice)}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg></button>
    </div>)}
  </aside></NotificationContext>;
}
