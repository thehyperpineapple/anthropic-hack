"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { motion } from "framer-motion"
import { Bell, Heart, Upload, LayoutDashboard, Settings, FileText } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/files", label: "Files", icon: FileText },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
]

export function Navbar() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-50 glass border-b border-border/50">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <Link href="/dashboard" className="flex items-center gap-2 group">
          <div className="relative flex items-center">
            <span className="text-xl font-bold tracking-tight text-foreground">
              {"Order"}
            </span>
            <span className="relative mx-0.5">
              <Heart
                className="h-5 w-5 text-coral-400 fill-coral-400 group-hover:animate-heartbeat transition-transform"
                aria-hidden="true"
              />
            </span>
            <span className="text-xl font-bold tracking-tight text-foreground">
              {"Flow"}
            </span>
            <span className="ml-1 text-xs font-semibold text-coral-400 uppercase tracking-widest">
              AI
            </span>
          </div>
        </Link>

        <div className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/")
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "text-coral-400"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="nav-active"
                    className="absolute inset-0 rounded-lg bg-coral-400/10"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <item.icon className="h-4 w-4 relative z-10" />
                <span className="relative z-10 hidden sm:inline">{item.label}</span>
              </Link>
            )
          })}
        </div>

        <div className="flex items-center gap-3">
          <button
            className="relative rounded-lg p-2 text-muted-foreground transition-colors hover:text-foreground hover:bg-muted"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-coral-400" />
          </button>
          <button
            className="relative rounded-lg p-2 text-muted-foreground transition-colors hover:text-foreground hover:bg-muted"
            aria-label="Settings"
          >
            <Settings className="h-5 w-5" />
          </button>
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-coral-400 to-rose-600 flex items-center justify-center text-xs font-bold text-card">
            JD
          </div>
        </div>
      </nav>
    </header>
  )
}