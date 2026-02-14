"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FileText,
  Mic,
  Upload,
  Check,
  Heart,
  Sparkles,
  ArrowRight,
  User,
} from "lucide-react"
import { useRouter } from "next/navigation"
import { useScribe } from "@elevenlabs/react"
import { Navbar } from "@/components/navbar"
import { HeartConfetti } from "@/components/heart-confetti"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { Client } from "@/lib/data"
import { formatCurrency } from "@/lib/data"
import { fetchCustomers, processOrder } from "@/lib/api"

type ProcessingStep = {
  label: string
  done: boolean
}

export default function UploadPage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [clients, setClients] = useState<Client[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState("")
  const [orderResult, setOrderResult] = useState<{ order_number: string; total_amount: string | number } | null>(null)

  useEffect(() => {
    fetchCustomers().then((data) => {
      setClients(data)
      if (data.length > 0) setSelectedCustomer(data[0].name)
    }).catch(console.error)
  }, [])
  const [textInput, setTextInput] = useState("")
  const [textFile, setTextFile] = useState<File | null>(null)
  const [dragOverText, setDragOverText] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([])
  const [transcribedText, setTranscribedText] = useState("")
  const [liveTranscript, setLiveTranscript] = useState("")
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [recordedAudioBlob, setRecordedAudioBlob] = useState<Blob | null>(null)

  // ElevenLabs Scribe setup
  const scribe = useScribe({
    modelId: "scribe_v2_realtime",
    onPartialTranscript: (data) => {
      setLiveTranscript(data.text)
    },
    onCommittedTranscript: (data) => {
      setTranscribedText((prev) => prev + " " + data.text)
    },
  })

  const sendToBackend = useCallback(async (message: string, sourceType: "voice_message" | "text_file") => {
    const customer = clients.find((c) => c.name === selectedCustomer)
    if (!customer) return

    setProcessing(true)
    const steps = [
      "Sending to AI...",
      "Parsing order details...",
      "Matching inventory...",
      "Creating order...",
    ]
    const stepsState = steps.map((label) => ({ label, done: false }))
    setProcessingSteps(stepsState)

    // Animate first step immediately
    setProcessingSteps((prev) =>
      prev.map((s, idx) => (idx === 0 ? { ...s, done: true } : s))
    )

    try {
      const result = await processOrder({
        customerId: customer.customerId,
        sourceType,
        originalMessage: message,
      })

      // Animate remaining steps
      for (let i = 1; i < steps.length; i++) {
        await new Promise((r) => setTimeout(r, 300))
        setProcessingSteps((prev) =>
          prev.map((s, idx) => (idx === i ? { ...s, done: true } : s))
        )
      }
      await new Promise((r) => setTimeout(r, 400))

      setOrderResult({
        order_number: result.order_number,
        total_amount: result.total_amount,
      })
      setProcessing(false)
      setShowSuccess(true)
    } catch (err) {
      setProcessing(false)
      alert(`Order processing failed: ${err instanceof Error ? err.message : "Unknown error"}`)
    }
  }, [clients, selectedCustomer])

  const handleRecordToggle = async () => {
    if (!isRecording) {
      // Start recording
      try {
        // Check if getUserMedia is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          alert("Your browser doesn't support audio recording. Please use Chrome, Edge, or Safari on localhost.")
          return
        }

        // Get microphone stream
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        
        // Create MediaRecorder to save the audio
        const recorder = new MediaRecorder(stream)
        const chunks: Blob[] = []
        
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            chunks.push(e.data)
          }
        }
        
        recorder.onstop = () => {
          const blob = new Blob(chunks, { type: 'audio/webm' })
          setRecordedAudioBlob(blob)
          
          // Stop all tracks to release microphone
          stream.getTracks().forEach(track => track.stop())
        }
        
        recorder.start()
        setMediaRecorder(recorder)

        // Fetch token from your server for transcription
        const response = await fetch("/api/scribe-token")
        const { token } = await response.json()

        // Connect to ElevenLabs with microphone for real-time transcription
        await scribe.connect({
          token,
          microphone: {
            echoCancellation: true,
            noiseSuppression: true,
          },
        })

        setIsRecording(true)
        setLiveTranscript("")
      } catch (error) {
        console.error("Failed to start recording:", error)
        alert("Failed to start recording. Please ensure:\n1. You're using localhost (not an IP address)\n2. Microphone permissions are granted\n3. You're using a modern browser (Chrome/Edge/Safari)")
      }
    } else {
      // Stop recording - save the current live transcript to transcribedText
      if (liveTranscript) {
        const finalTranscript = transcribedText + " " + liveTranscript
        setTranscribedText(finalTranscript.trim())
      }
      
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop()
      }
      scribe.disconnect()
      setIsRecording(false)
      setLiveTranscript("") // Clear live transcript after saving
    }
  }

  const handleProcessRecording = async () => {
    if (!transcribedText.trim()) return
    await sendToBackend(transcribedText.trim(), "voice_message")
  }

  const handleTextDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOverText(false)
    const file = e.dataTransfer.files[0]
    if (file) setTextFile(file)
  }, [])

  const handleProcessText = async () => {
    let content = textInput.trim()
    if (!content && textFile) {
      content = await textFile.text()
    }
    if (!content) return
    await sendToBackend(content, "text_file")
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <HeartConfetti show={showSuccess} />

      {/* Processing Overlay */}
      <AnimatePresence>
        {processing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/5 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="mx-4 w-full max-w-md rounded-2xl bg-card p-8 shadow-2xl"
            >
              <div className="mb-6 flex justify-center">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 1.2 }}
                >
                  <Heart className="h-12 w-12 text-coral-400 fill-coral-400" />
                </motion.div>
              </div>
              <h3 className="mb-6 text-center text-lg font-semibold text-foreground">
                Processing your order...
              </h3>
              <div className="space-y-3">
                {processingSteps.map((step, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center gap-3"
                  >
                    {step.done ? (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/40"
                      >
                        <Check className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                      </motion.div>
                    ) : (
                      <div className="flex h-6 w-6 items-center justify-center">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{
                            repeat: Infinity,
                            duration: 1,
                            ease: "linear",
                          }}
                          className="h-4 w-4 rounded-full border-2 border-coral-400 border-t-transparent"
                        />
                      </div>
                    )}
                    <span
                      className={`text-sm ${step.done ? "text-muted-foreground line-through" : "text-foreground font-medium"}`}
                    >
                      {step.label}
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Success Modal */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/5 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", bounce: 0.3 }}
              className="mx-4 w-full max-w-sm rounded-2xl bg-card p-8 shadow-2xl text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", bounce: 0.5 }}
                className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-coral-400 to-rose-600"
              >
                <Check className="h-8 w-8 text-card" />
              </motion.div>
              <h3 className="mb-1 text-xl font-bold text-foreground">
                Order Created!
              </h3>
              <p className="mb-6 text-sm text-muted-foreground">
                {orderResult
                  ? `Order #${orderResult.order_number} • ${formatCurrency(Number(orderResult.total_amount))}`
                  : "Order created successfully"}
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={() => router.push("/dashboard")}
                  className="flex-1 bg-gradient-to-r from-coral-400 to-rose-600 text-card hover:from-coral-500 hover:to-rose-700 border-0"
                >
                  View Details
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowSuccess(false)
                    setTextInput("")
                    setTextFile(null)
                    setTranscribedText("")
                    setLiveTranscript("")
                    setRecordedAudioBlob(null)
                    setOrderResult(null)
                  }}
                  className="flex-1 border-coral-200 dark:border-coral-800 text-coral-400 hover:bg-coral-50 dark:hover:bg-coral-950/30 hover:text-coral-500"
                >
                  Upload Another
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="mx-auto max-w-5xl px-6 py-16">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <motion.div
            animate={{ scale: [1, 1.15, 1] }}
            transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
            className="mb-4 inline-block"
          >
            <Heart className="h-10 w-10 text-coral-400 fill-coral-400" />
          </motion.div>
          <h1 className="mb-3 text-4xl font-bold tracking-tight text-foreground text-balance md:text-5xl">
            Fall in Love with Automated Orders
          </h1>
          <p className="mx-auto max-w-xl text-lg text-muted-foreground leading-relaxed">
            Turn messy texts and voice messages into perfect ERP entries in
            seconds
          </p>
        </motion.div>

        {/* Customer Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="mb-10 flex items-center justify-center gap-3"
        >
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <User className="h-4 w-4" />
            <span>Customer:</span>
          </div>
          <Select value={selectedCustomer} onValueChange={setSelectedCustomer}>
            <SelectTrigger className="w-64 border-coral-200 focus:ring-coral-400/30">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-coral-400/20 to-rose-500/20 text-xs font-bold text-coral-400">
                  {selectedCustomer.charAt(0)}
                </div>
                <SelectValue />
              </div>
            </SelectTrigger>
            <SelectContent>
              {clients.map((c) => (
                <SelectItem key={c.id} value={c.name}>
                  <div className="flex items-center gap-2">
                    <span>{c.name}</span>
                    <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                      {c.industry}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </motion.div>

        {/* Upload Cards */}
        <div className="grid gap-8 md:grid-cols-2">
          {/* Text Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="group relative overflow-hidden rounded-2xl border border-coral-200 dark:border-coral-800/50 bg-card p-1"
          >
            <div className="rounded-xl bg-card p-6">
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-coral-400/10 to-coral-400/5">
                  <FileText className="h-6 w-6 text-coral-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-foreground">
                    Text Orders
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Type, paste, or upload a file
                  </p>
                </div>
                <Sparkles className="ml-auto h-5 w-5 text-coral-300" />
              </div>

              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="e.g. I need 50 units of Organic Honey and 30 jars of Almond Butter..."
                className="mb-4 w-full resize-none rounded-xl border-2 border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-coral-400 focus:outline-none focus:ring-2 focus:ring-coral-400/20 transition-all"
                rows={4}
              />

              {/* Divider */}
              <div className="mb-4 flex items-center gap-3">
                <div className="h-px flex-1 bg-border" />
                <span className="text-xs font-medium text-muted-foreground">or attach a file</span>
                <div className="h-px flex-1 bg-border" />
              </div>

              {/* File Upload Area */}
              <div
                onDrop={handleTextDrop}
                onDragOver={(e) => {
                  e.preventDefault()
                  setDragOverText(true)
                }}
                onDragLeave={() => setDragOverText(false)}
                onClick={() => fileInputRef.current?.click()}
                className={`mb-6 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed py-6 transition-all ${
                  dragOverText
                    ? "border-coral-400 bg-coral-400/5"
                    : "border-border hover:border-coral-300 hover:bg-muted/50"
                }`}
                role="button"
                tabIndex={0}
                aria-label="Drop or click to upload text file"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.pdf,.docx,.csv"
                  className="hidden"
                  onChange={(e) =>
                    setTextFile(e.target.files?.[0] || null)
                  }
                />
                <AnimatePresence mode="wait">
                  {textFile ? (
                    <motion.div
                      key="file"
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.8, opacity: 0 }}
                      className="flex flex-col items-center"
                    >
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", bounce: 0.5 }}
                        className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/30"
                      >
                        <Check className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                      </motion.div>
                      <p className="text-sm font-medium text-foreground">
                        {textFile.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {(textFile.size / 1024).toFixed(1)} KB
                      </p>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex flex-col items-center"
                    >
                      <Upload className="mb-2 h-6 w-6 text-muted-foreground" />
                      <p className="text-xs font-medium text-foreground">
                        Drop files here or click to browse
                      </p>
                      <p className="mt-0.5 text-[10px] text-muted-foreground">
                        .txt, .pdf, .docx, .csv
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <Button
                onClick={handleProcessText}
                disabled={(!textInput.trim() && !textFile) || processing}
                className="w-full bg-gradient-to-r from-coral-400 to-coral-500 text-card hover:from-coral-500 hover:to-coral-600 border-0 shadow-lg shadow-coral-400/25 transition-all hover:shadow-xl hover:shadow-coral-400/30 hover:-translate-y-0.5 disabled:opacity-50 disabled:shadow-none disabled:translate-y-0"
              >
                Process Order
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </motion.div>

          {/* Audio Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="group relative overflow-hidden rounded-2xl border border-rose-200 dark:border-rose-800/50 bg-card p-1"
          >
            <div className="rounded-xl bg-card p-6">
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-rose-600/10 to-rose-600/5">
                  <Mic className="h-6 w-6 text-rose-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-foreground">
                    Voice Orders
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Record your order
                  </p>
                </div>
                <Sparkles className="ml-auto h-5 w-5 text-rose-300" />
              </div>

              {/* Live transcription display */}
              {(isRecording || transcribedText) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-4 rounded-xl border border-rose-200 bg-rose-50/50 dark:border-rose-800 dark:bg-rose-950/30 p-4"
                >
                  <div className="mb-2 flex items-center gap-2">
                    <div className="flex items-center gap-2">
                      {isRecording && (
                        <span className="relative flex h-2 w-2">
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75"></span>
                          <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500"></span>
                        </span>
                      )}
                      <span className="text-xs font-medium text-rose-600">
                        {isRecording ? "Listening..." : "Transcribed"}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-foreground">
                    {transcribedText}
                    {liveTranscript && (
                      <span className="text-muted-foreground italic">
                        {" "}{liveTranscript}
                      </span>
                    )}
                  </p>
                </motion.div>
              )}

              {/* Record button */}
              <button
                onClick={handleRecordToggle}
                disabled={scribe.isConnected && !isRecording}
                className={`mb-4 flex w-full items-center justify-center gap-3 rounded-xl border-2 py-4 transition-all ${
                  isRecording
                    ? "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/30"
                    : "border-border hover:border-rose-300"
                }`}
              >
                <span className="relative flex h-4 w-4 items-center justify-center">
                  <span
                    className={`absolute h-4 w-4 rounded-full ${isRecording ? "bg-red-500 animate-pulse-ring" : "bg-red-400"}`}
                  />
                  <span
                    className={`relative h-3 w-3 rounded-full ${isRecording ? "bg-red-600" : "bg-red-400"}`}
                  />
                </span>
                <span
                  className={`text-sm font-medium ${isRecording ? "text-red-600" : "text-foreground"}`}
                >
                  {isRecording ? "Stop Recording..." : "Record Now"}
                </span>
              </button>

              {/* Clear transcript button */}
              {transcribedText && !isRecording && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <Button
                    onClick={() => {
                      setTranscribedText("")
                      setLiveTranscript("")
                      setRecordedAudioBlob(null)
                    }}
                    variant="outline"
                    className="w-full mb-4 border-rose-200 dark:border-rose-800 text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:text-rose-500"
                  >
                    Clear & Record Again
                  </Button>
                </motion.div>
              )}

              <Button
                onClick={handleProcessRecording}
                disabled={!transcribedText || processing || isRecording}
                className="w-full bg-gradient-to-r from-rose-500 to-rose-600 text-card hover:from-rose-600 hover:to-rose-700 border-0 shadow-lg shadow-rose-600/25 transition-all hover:shadow-xl hover:shadow-rose-600/30 hover:-translate-y-0.5 disabled:opacity-50 disabled:shadow-none disabled:translate-y-0"
              >
                Process Recording
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center">
        <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
          Made with{" "}
          <Heart className="h-3 w-3 text-coral-400 fill-coral-400" /> in
          SF
        </p>
      </footer>
    </div>
  )
}