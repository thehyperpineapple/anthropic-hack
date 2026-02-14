"use client"

import { motion } from "framer-motion"
import {
  X,
  Download,
  Send,
  CheckCircle,
  Copy,
  Check,
  AlertTriangle,
  Shield,
  Mail,
  Phone,
  Flame,
  Heart,
  FileText,
  Volume2,
  Play,
  Pause,
} from "lucide-react"
import { useState } from "react"
import type { Order } from "@/lib/data"
import { formatCurrency } from "@/lib/data"
import { updateOrderStatus } from "@/lib/api"
import { StatusBadge } from "@/components/status-badge"
import { Button } from "@/components/ui/button"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

interface OrderDetailPanelProps {
  order: Order
  onClose: () => void
  onOrderUpdate?: () => void
}

export function OrderDetailPanel({ order, onClose, onOrderUpdate }: OrderDetailPanelProps) {
  const [copied, setCopied] = useState(false)
  const [quoteView, setQuoteView] = useState<"text" | "voice">("text")
  const [isPlaying, setIsPlaying] = useState(false)
  const [actionLoading, setActionLoading] = useState<"approve" | "reject" | null>(null)

  const canReview = order.status === "processing" || order.status === "review"

  const handleStatusAction = async (action: "approve" | "reject") => {
    if (!order.orderId) return
    setActionLoading(action)
    try {
      const newStatus = action === "approve" ? "completed" : "cancelled"
      await updateOrderStatus(order.orderId, newStatus, "Employee")
      onOrderUpdate?.()
      onClose()
    } catch (err) {
      alert(`Failed to ${action} order: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleCopy = () => {
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const generatedQuote = `Dear ${order.customer},

Thank you for your order request. Please find the details below:

Order Reference: ${order.id}
Date: February 14, 2026

${
  order.parsedItems
    ?.map(
      (item) =>
        `${item.sku}  ${item.product.padEnd(20)} x${String(item.qty).padStart(5)}  @${formatCurrency(item.price)}  = ${formatCurrency(item.total)}`
    )
    .join("\n") || "No items parsed"
}

${"─".repeat(50)}
Total: ${formatCurrency(order.amount)}

Payment terms: Net 30
Expected delivery: 5-7 business days

Best regards,
OrderFlow AI`

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-foreground/10 backdrop-blur-sm"
      />

      {/* Panel */}
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 30, stiffness: 300 }}
        className="fixed right-0 top-0 z-50 flex h-full w-full flex-col bg-card shadow-2xl sm:max-w-lg"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gradient-to-r from-coral-400 to-rose-500 px-3 py-1">
              <span className="font-mono text-sm font-bold text-card">
                {order.id}
              </span>
            </div>
            <StatusBadge status={order.status} />
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Close panel"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 border-b border-border px-6 py-3">
          <Button variant="outline" size="sm" className="text-xs border-border text-foreground hover:bg-muted">
            <Download className="mr-1.5 h-3.5 w-3.5" />
            Download PDF
          </Button>
          <Button variant="outline" size="sm" className="text-xs border-border text-foreground hover:bg-muted">
            <Send className="mr-1.5 h-3.5 w-3.5" />
            Send Quote
          </Button>
          {!canReview && (
            <Button variant="outline" size="sm" className="text-xs border-border text-foreground hover:bg-muted">
              <CheckCircle className="mr-1.5 h-3.5 w-3.5" />
              Mark Complete
            </Button>
          )}
        </div>

        {/* Approve / Reject Banner */}
        {canReview && (
          <div className="flex items-center gap-3 border-b border-border bg-amber-50/70 dark:bg-amber-950/20 px-6 py-3">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500" />
            <span className="flex-1 text-xs font-medium text-amber-700 dark:text-amber-400">
              This order requires review
            </span>
            <Button
              size="sm"
              onClick={() => handleStatusAction("approve")}
              disabled={actionLoading !== null}
              className="h-8 bg-emerald-600 text-white hover:bg-emerald-700 border-0 text-xs px-4"
            >
              {actionLoading === "approve" ? (
                <span className="flex items-center gap-1.5">
                  <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }} className="inline-block h-3 w-3 rounded-full border-2 border-white border-t-transparent" />
                  Approving...
                </span>
              ) : (
                <>
                  <CheckCircle className="mr-1.5 h-3.5 w-3.5" />
                  Approve
                </>
              )}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleStatusAction("reject")}
              disabled={actionLoading !== null}
              className="h-8 border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 text-xs px-4"
            >
              {actionLoading === "reject" ? (
                <span className="flex items-center gap-1.5">
                  <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }} className="inline-block h-3 w-3 rounded-full border-2 border-red-500 border-t-transparent" />
                  Rejecting...
                </span>
              ) : (
                <>
                  <X className="mr-1.5 h-3.5 w-3.5" />
                  Reject
                </>
              )}
            </Button>
          </div>
        )}

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Customer Info */}
          <div className="border-b border-border px-6 py-5">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-coral-400 to-rose-600 text-lg font-bold text-card">
                {order.customer.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-lg font-semibold text-foreground">
                  {order.customer}
                </h3>
                <div className="mt-2 space-y-1.5">
                  {order.email && (
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors group"
                    >
                      <Mail className="h-3.5 w-3.5" />
                      <span>{order.email}</span>
                      {copied ? (
                        <Check className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <Copy className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      )}
                    </button>
                  )}
                  {order.phone && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Phone className="h-3.5 w-3.5" />
                      <span>{order.phone}</span>
                    </div>
                  )}
                </div>
                {order.orderHistory && (
                  <div className="mt-3 flex items-center gap-1.5 text-xs font-medium text-coral-400">
                    <Flame className="h-3.5 w-3.5" />
                    {order.orderHistory}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Parsed Order */}
          <div className="border-b border-border px-6 py-5">
            <div className="mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                AI extracted this from the message
              </span>
            </div>

            {/* Original message */}
            {order.originalText && (
              <div className="mb-4 rounded-lg border-l-2 border-coral-400 bg-secondary/50 px-4 py-3">
                <p className="text-sm italic text-muted-foreground leading-relaxed">
                  {`"${order.originalText}"`}
                </p>
              </div>
            )}

            {/* Arrow */}
            <div className="my-3 flex justify-center">
              <motion.div
                animate={{ y: [0, 4, 0] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="flex h-6 w-6 items-center justify-center rounded-full bg-coral-400/10"
              >
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 12 12"
                  fill="none"
                  className="text-coral-400"
                >
                  <path
                    d="M6 2v8m0 0l3-3m-3 3L3 7"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </motion.div>
            </div>

            {/* Items table */}
            {order.parsedItems && order.parsedItems.length > 0 ? (
              <div className="overflow-hidden rounded-lg border border-border">
                <div className="grid grid-cols-12 gap-2 bg-muted/30 px-4 py-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  <div className="col-span-2">SKU</div>
                  <div className="col-span-4">Product</div>
                  <div className="col-span-1 text-right">Qty</div>
                  <div className="col-span-2 text-right">Price</div>
                  <div className="col-span-3 text-right">Total</div>
                </div>
                {order.parsedItems.map((item, i) => (
                  <motion.div
                    key={item.sku}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="grid grid-cols-12 gap-2 border-t border-border px-4 py-2.5 text-sm"
                  >
                    <div className="col-span-2 font-mono text-xs text-muted-foreground">
                      {item.sku}
                    </div>
                    <div className="col-span-4 font-medium text-foreground">
                      {item.product}
                    </div>
                    <div className="col-span-1 text-right text-foreground">
                      {item.qty}
                    </div>
                    <div className="col-span-2 text-right text-muted-foreground">
                      {formatCurrency(item.price)}
                    </div>
                    <div className="col-span-3 text-right font-medium text-foreground">
                      {formatCurrency(item.total)}
                    </div>
                  </motion.div>
                ))}
                <div className="grid grid-cols-12 gap-2 border-t-2 border-border bg-muted/20 px-4 py-2.5">
                  <div className="col-span-9 text-right text-sm font-semibold text-foreground">
                    TOTAL:
                  </div>
                  <div className="col-span-3 text-right text-sm font-bold text-coral-400">
                    {formatCurrency(order.amount)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center rounded-lg border border-border py-8">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Heart className="h-4 w-4 text-red-300" />
                  {order.error || "No items parsed"}
                </div>
              </div>
            )}
          </div>

          {/* Generated Quote */}
          <div className="border-b border-border px-6 py-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Generated Quote
              </span>
              <div className="flex rounded-lg border border-border bg-muted/30 p-0.5">
                <button
                  onClick={() => setQuoteView("text")}
                  className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                    quoteView === "text"
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Text
                </button>
                <button
                  onClick={() => setQuoteView("voice")}
                  className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                    quoteView === "voice"
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Voice
                </button>
              </div>
            </div>

            {quoteView === "text" ? (
              <div className="relative">
                <pre className="overflow-x-auto rounded-lg bg-foreground/[0.03] p-4 font-mono text-xs leading-relaxed text-foreground">
                  {generatedQuote}
                </pre>
                <button
                  onClick={handleCopy}
                  className="absolute right-3 top-3 rounded-md border border-border bg-card p-1.5 text-muted-foreground transition-colors hover:text-foreground"
                  aria-label="Copy quote"
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-emerald-500" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>
            ) : (
              <div className="rounded-lg border border-border bg-foreground/[0.03] p-4">
                <div className="mb-3 flex items-center gap-2 text-xs text-muted-foreground">
                  <Volume2 className="h-3.5 w-3.5" />
                  Listen to AI-generated quote
                </div>
                {/* Waveform */}
                <div className="mb-3 flex h-12 items-end gap-0.5">
                  {Array.from({ length: 50 }).map((_, i) => (
                    <motion.div
                      key={i}
                      animate={
                        isPlaying
                          ? {
                              height: [
                                `${20 + Math.random() * 80}%`,
                                `${20 + Math.random() * 80}%`,
                              ],
                            }
                          : { height: `${30 + Math.sin(i * 0.3) * 25}%` }
                      }
                      transition={
                        isPlaying
                          ? {
                              repeat: Infinity,
                              duration: 0.3 + Math.random() * 0.3,
                              repeatType: "reverse",
                            }
                          : {}
                      }
                      className="flex-1 rounded-full bg-gradient-to-t from-coral-400 to-rose-300"
                      style={{
                        height: `${30 + Math.sin(i * 0.3) * 25}%`,
                      }}
                    />
                  ))}
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-coral-400 to-rose-500 text-card transition-transform hover:scale-105"
                    aria-label={isPlaying ? "Pause" : "Play"}
                  >
                    {isPlaying ? (
                      <Pause className="h-3.5 w-3.5" />
                    ) : (
                      <Play className="h-3.5 w-3.5 ml-0.5" />
                    )}
                  </button>
                  <span className="text-xs font-mono text-muted-foreground">
                    0:00 / 0:32
                  </span>
                  <button className="ml-auto rounded border border-border px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
                    1x
                  </button>
                  <button className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Download audio">
                    <Download className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Safety Checks */}
          <div className="px-6 py-5">
            <span className="mb-3 block text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Safety Checks
            </span>
            <Accordion type="single" collapsible className="space-y-2">
              <AccordionItem
                value="qty"
                className="rounded-lg border border-border px-4"
              >
                <AccordionTrigger className="py-3 text-sm hover:no-underline">
                  <span className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-emerald-500" />
                    <span className="text-foreground">Quantity validation passed</span>
                  </span>
                </AccordionTrigger>
                <AccordionContent className="pb-3 text-xs text-muted-foreground">
                  All item quantities are within acceptable ranges.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem
                value="sku"
                className="rounded-lg border border-border px-4"
              >
                <AccordionTrigger className="py-3 text-sm hover:no-underline">
                  <span className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-emerald-500" />
                    <span className="text-foreground">SKU verification passed</span>
                  </span>
                </AccordionTrigger>
                <AccordionContent className="pb-3 text-xs text-muted-foreground">
                  All SKUs match items in the product catalog.
                </AccordionContent>
              </AccordionItem>
              {order.warning && (
                <AccordionItem
                  value="warning"
                  className="rounded-lg border border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/30 px-4"
                >
                  <AccordionTrigger className="py-3 text-sm hover:no-underline">
                    <span className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      <span className="text-amber-700 dark:text-amber-400">
                        Unusually large order ({order.warning})
                      </span>
                      <span className="rounded-full bg-amber-100 dark:bg-amber-900/50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 dark:text-amber-400">
                        Needs Review
                      </span>
                    </span>
                  </AccordionTrigger>
                  <AccordionContent className="pb-3 text-xs text-amber-600 dark:text-amber-400">
                    This order is significantly larger than the customer average.
                    Please verify with the customer before processing.
                  </AccordionContent>
                </AccordionItem>
              )}
              <AccordionItem
                value="pricing"
                className="rounded-lg border border-border px-4"
              >
                <AccordionTrigger className="py-3 text-sm hover:no-underline">
                  <span className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-emerald-500" />
                    <span className="text-foreground">Pricing calculation verified</span>
                  </span>
                </AccordionTrigger>
                <AccordionContent className="pb-3 text-xs text-muted-foreground">
                  All line items and totals have been verified against the
                  current price list.
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        </div>
      </motion.div>
    </>
  )
}
