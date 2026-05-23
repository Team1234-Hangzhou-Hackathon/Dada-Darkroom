"use client"

import { motion } from "framer-motion"
import { useState, useEffect, type ReactNode } from "react"

interface IPhoneContainerProps {
  children: ReactNode
  className?: string
}

export function IPhoneContainer({ children, className = "" }: IPhoneContainerProps) {
  // iPhone 16 Pro Max: 6.9" display, 2868 x 1320 pixels
  // Aspect ratio: ~19.5:9 = 2.17:1
  // Scaled dimensions: 393px width x 852px height (maintains ratio)
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`relative mx-auto ${className}`}
      style={{
        width: "393px",
        height: "852px",
        maxHeight: "calc(100vh - 40px)",
        maxWidth: "calc((100vh - 40px) * 0.461)",
      }}
    >
      {/* Phone Frame - iPhone 16 Pro Max style */}
      <div className="absolute inset-0 rounded-[50px] bg-gradient-to-b from-zinc-700 via-zinc-800 to-zinc-900 p-[3px] shadow-2xl">
        {/* Inner bezel */}
        <div className="absolute inset-[3px] rounded-[47px] bg-gradient-to-b from-zinc-600 via-zinc-700 to-zinc-800 p-[2px]">
          {/* Screen bezel */}
          <div className="absolute inset-[2px] rounded-[45px] bg-black p-[10px] overflow-hidden">
            {/* Dynamic Island */}
            <div className="dynamic-island flex items-center justify-center">
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-900 border border-zinc-800" />
            </div>
            
            {/* Screen Content Area */}
            <div className="relative w-full h-full rounded-[35px] overflow-hidden bg-background">
              {/* Status Bar */}
              <StatusBar />
              
              {/* Main Content */}
              <div className="absolute inset-0 pt-12 overflow-hidden">
                {children}
              </div>
              
              {/* Home Indicator */}
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-32 h-1 bg-foreground/30 rounded-full" />
            </div>
          </div>
        </div>
      </div>
      
      {/* Side Buttons */}
      <div className="absolute left-[-3px] top-[120px] w-[3px] h-[35px] bg-zinc-700 rounded-l-sm" />
      <div className="absolute left-[-3px] top-[170px] w-[3px] h-[60px] bg-zinc-700 rounded-l-sm" />
      <div className="absolute left-[-3px] top-[240px] w-[3px] h-[60px] bg-zinc-700 rounded-l-sm" />
      <div className="absolute right-[-3px] top-[180px] w-[3px] h-[90px] bg-zinc-700 rounded-r-sm" />
    </motion.div>
  )
}

function StatusBar() {
  const [time, setTime] = useState<string | null>(null)
  
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      const hours = now.getHours().toString().padStart(2, '0')
      const minutes = now.getMinutes().toString().padStart(2, '0')
      setTime(`${hours}:${minutes}`)
    }
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])
  
  return (
    <div className="absolute top-0 left-0 right-0 h-11 flex items-center z-[100]">
      {/* Left side - Time */}
      <div className="flex-1 flex items-center pl-6">
        <span className="text-[15px] font-semibold text-foreground tabular-nums tracking-tight" suppressHydrationWarning>
          {time ?? "9:41"}
        </span>
      </div>
      
      {/* Center - Dynamic Island Space */}
      <div className="w-[105px] shrink-0" />
      
      {/* Right side - Status Icons */}
      <div className="flex-1 flex items-center justify-end pr-5 gap-[5px]">
        <svg className="w-[17px] h-[12px]" viewBox="0 0 17 12" fill="currentColor">
          <path d="M8.5 0C5.35 0 2.53 1.35 0.65 3.52c-.27.3-.27.76 0 1.06l7.14 6.89c.4.38 1.03.38 1.42 0l7.14-6.89c.27-.3.27-.76 0-1.06C14.47 1.35 11.65 0 8.5 0z"/>
        </svg>
        <svg className="w-[17px] h-[12px]" viewBox="0 0 17 12" fill="currentColor">
          <path d="M15 0H2C.9 0 0 .9 0 2v8c0 1.1.9 2 2 2h13c1.1 0 2-.9 2-2V2c0-1.1-.9-2-2-2zm0 10H2V2h13v8z"/>
          <path d="M4 4h2v4H4zM7 5h2v3H7zM10 3h2v5h-2zM13 4h2v4h-2z"/>
        </svg>
        <div className="flex items-center">
          <div className="w-[22px] h-[11px] rounded-[3px] border-[1.5px] border-current flex items-center p-[2px]">
            <div className="h-full w-full bg-current rounded-[1px]" />
          </div>
          <div className="w-[2px] h-[4px] bg-current rounded-r-[1px] ml-[1px]" />
        </div>
      </div>
    </div>
  )
}
