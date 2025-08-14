"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"

const rotatingWords = ["lazy", "busy", "overwhelmed", "ambitious", "procrastinating", "cracked"]

export default function HomePage() {
  const [currentWordIndex, setCurrentWordIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentWordIndex((prev) => (prev + 1) % rotatingWords.length)
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center px-4 transition-colors">
      {/* Theme toggle */}
      <ThemeToggle />

      {/* Logo in top left */}
      <div className="absolute top-6 left-6">
        <img src="/angel-logo-new.png" alt="Angel A114 Logo" className="w-16 h-12" />
      </div>

      {/* Main content */}
      <div className="text-center mb-8">
        <h1 className="text-6xl md:text-7xl font-bold text-black dark:text-white mb-4 font-jetbrains transition-colors">
          10X your productivity
        </h1>

        <p className="text-xl md:text-2xl text-gray-700 dark:text-gray-300 mb-8 font-jetbrains transition-colors">
          AI agent for{" "}
          <span className="inline-block min-w-[140px] text-left">
            <span key={currentWordIndex} className="animate-[fadeInUp_0.5s_ease-out]">
              {rotatingWords[currentWordIndex]}
            </span>
          </span>{" "}
          students
        </p>

        <Button
          size="lg"
          className="bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200 px-8 py-3 text-lg rounded-full mb-12 transition-colors"
        >
          Meet Angel!
        </Button>

        <div className="flex items-center justify-center gap-8 mb-16">
          <img
            src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/icons8-gmail-48-OggZ8x1v6XJiJtWBCfVmzmfZNCukPP.png"
            alt="Gmail"
            className="w-12 h-12 transition-opacity hover:opacity-80"
          />
          <img
            src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/icons8-notion-48-YixtylRiDppizaSQqKGgypbK5L3USn.png"
            alt="Notion"
            className="w-12 h-12 transition-opacity hover:opacity-80"
          />
          <img
            src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/icons8-google-calendar-48-tdPHQiBkWtj64HxZ5YP6wvt6heNv42.png"
            alt="Google Calendar"
            className="w-12 h-12 transition-opacity hover:opacity-80"
          />
          <img
            src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/icons8-microsoft-outlook-48-U3emUw4cq0HwkLRdiWBJGUZ8cmwnZP.png"
            alt="Microsoft Outlook"
            className="w-12 h-12 transition-opacity hover:opacity-80"
          />
          <img
            src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/icons8-canvas-student-48-mEPJXi01CXwiRP0QCC8KFiRaxUAzDt.png"
            alt="Canvas"
            className="w-12 h-12 transition-opacity hover:opacity-80"
          />
        </div>
      </div>

      <div className="relative w-full max-w-4xl mx-auto">
        <div className="flex justify-center mb-8">
          <img src="/angel-logo-new.png" alt="Angel A114 Logo" className="w-24 h-20" />
        </div>

        {/* Message bubbles positioned around the center with floating animations */}
        {/* Top left bubble */}
        <div className="absolute -top-8 left-8 max-w-xs animate-[float_3s_ease-in-out_infinite]">
          <div className="bg-blue-500 dark:bg-blue-600 text-white p-3 rounded-2xl rounded-tl-sm text-sm font-inter transition-colors">
            Angel, did my professors send any new emails?
          </div>
        </div>

        {/* Top right bubble */}
        <div className="absolute -top-8 right-8 max-w-xs animate-[float_4s_ease-in-out_infinite_1s]">
          <div className="bg-blue-500 dark:bg-blue-600 text-white p-3 rounded-2xl rounded-tr-sm text-sm font-inter transition-colors">
            yo angel, can you set a reminder to study at 10pm on Tuesday night before my chem exam?
          </div>
        </div>

        {/* Bottom left bubble */}
        <div className="absolute top-16 left-0 max-w-xs animate-[floatSide_3.5s_ease-in-out_infinite_0.5s]">
          <div className="bg-blue-500 dark:bg-blue-600 text-white p-3 rounded-2xl rounded-bl-sm text-sm font-inter transition-colors">
            angel, can you help me review for my DSA quiz on Dijkstra's algorithm?
          </div>
        </div>

        {/* Bottom right bubble */}
        <div className="absolute top-16 right-0 max-w-xs animate-[float_3.2s_ease-in-out_infinite_2s]">
          <div className="bg-blue-500 dark:bg-blue-600 text-white p-3 rounded-2xl rounded-br-sm text-sm font-inter transition-colors">
            thank you, angel! you're the best :)
          </div>
        </div>
      </div>
    </main>
  )
}
