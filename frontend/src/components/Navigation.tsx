"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { useAuth } from "@/lib/auth";

const links = [
  { href: "/datasets", label: "Datasets" },
  { href: "/analyses", label: "Analyses" },
  { href: "/publications", label: "Publications" },
];

export function Navigation() {
  const pathname = usePathname();
  const { user, logout, loading } = useAuth();

  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-brand-700">
              Mishmash
            </Link>
            <div className="flex gap-1">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={clsx(
                    "rounded-md px-3 py-2 text-sm font-medium transition",
                    pathname?.startsWith(link.href)
                      ? "bg-brand-50 text-brand-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {!loading && (
              user ? (
                <>
                  <Link
                    href={`/u/${user.username}`}
                    className="text-sm font-medium text-gray-700 hover:text-gray-900"
                  >
                    {user.name}
                  </Link>
                  <button
                    onClick={logout}
                    className="rounded-md px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 transition"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="rounded-md px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 transition"
                  >
                    Log in
                  </Link>
                  <Link
                    href="/register"
                    className="rounded-lg bg-brand-600 px-4 py-1.5 text-sm text-white font-medium hover:bg-brand-700 transition"
                  >
                    Sign up
                  </Link>
                </>
              )
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
