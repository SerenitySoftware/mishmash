"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface Notification {
  id: string;
  type: string;
  title: string;
  body: string | null;
  is_read: boolean;
  target_type: string | null;
  target_id: string | null;
  created_at: string;
}

export function NotificationBell() {
  const { user } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    if (!user) return;
    const fetchCount = () => {
      apiFetch<{ unread_count: number }>("/api/notifications/unread-count")
        .then((d) => setUnreadCount(d.unread_count))
        .catch(() => {});
    };
    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, [user]);

  const handleOpen = async () => {
    if (!open) {
      const resp = await apiFetch<{ items: Notification[] }>("/api/notifications?page_size=10");
      setNotifications(resp.items);
    }
    setOpen(!open);
  };

  const markAllRead = async () => {
    await apiFetch("/api/notifications/read-all", { method: "POST" });
    setUnreadCount(0);
    setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
  };

  if (!user) return null;

  const getLink = (n: Notification) => {
    if (!n.target_type || !n.target_id) return null;
    if (n.target_type === "dataset") return `/datasets/${n.target_id}`;
    if (n.target_type === "analysis") return `/analyses/${n.target_id}`;
    if (n.target_type === "publication") return `/publications/${n.target_id}`;
    return null;
  };

  return (
    <div className="relative">
      <button onClick={handleOpen} className="relative p-1 text-gray-500 hover:text-gray-700">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <span className="font-semibold text-sm">Notifications</span>
            {unreadCount > 0 && (
              <button onClick={markAllRead} className="text-xs text-brand-600 hover:text-brand-800">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
            {notifications.length === 0 && (
              <p className="text-center py-6 text-sm text-gray-500">No notifications</p>
            )}
            {notifications.map((n) => {
              const link = getLink(n);
              const content = (
                <div className={`px-4 py-3 ${n.is_read ? "" : "bg-blue-50"}`}>
                  <p className="text-sm font-medium">{n.title}</p>
                  {n.body && <p className="text-xs text-gray-500 mt-0.5">{n.body}</p>}
                  <p className="text-xs text-gray-400 mt-1">{new Date(n.created_at).toLocaleDateString()}</p>
                </div>
              );
              return link ? (
                <Link key={n.id} href={link} onClick={() => setOpen(false)} className="block hover:bg-gray-50">
                  {content}
                </Link>
              ) : (
                <div key={n.id}>{content}</div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
