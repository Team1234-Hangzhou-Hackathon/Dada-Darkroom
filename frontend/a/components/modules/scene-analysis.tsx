"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import {
  faCamera,
  faLightbulb,
  faPalette,
  faBolt,
  faCheck,
  faXmark,
  faRotate,
  faSpinner,
  faFilm,
  faFire,
  faSnowflake,
  faLeaf,
  faSun,
  faChevronLeft,
} from "@fortawesome/free-solid-svg-icons"

interface SceneAnalysisProps {
  onAnalysisComplete?: (result: AnalysisResult) => void
  onFilterApply?: (filter: string) => void
  currentImage?: string | null
  onBack?: () => void
}

interface AnalysisResult {
  lighting: string
  colors: string[]
  objects: string[]
  mood: string
  suggestedStyles: StyleSuggestion[]
}

interface StyleSuggestion {
  name: string
  icon: typeof faFilm
  filter: string
  description: string
}

const STYLE_PRESETS: StyleSuggestion[] = [
  { name: "电影感", icon: faFilm, filter: "filter-cinematic", description: "高对比度，电影色调" },
  { name: "暖阳", icon: faFire, filter: "filter-warm", description: "温暖舒适的氛围" },
  { name: "清冷", icon: faSnowflake, filter: "filter-cool", description: "清新冷调效果" },
  { name: "复古", icon: faLeaf, filter: "filter-vintage", description: "怀旧胶片质感" },
  { name: "鲜艳", icon: faSun, filter: "filter-vibrant", description: "高饱和度色彩" },
]

export function SceneAnalysis({ onAnalysisComplete, onFilterApply, currentImage, onBack }: SceneAnalysisProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const startCamera = useCallback(async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setIsStreaming(true)
      }
    } catch {
      setError("无法访问摄像头，请检查权限设置")
    }
  }, [])

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
      tracks.forEach((track) => track.stop())
      videoRef.current.srcObject = null
      setIsStreaming(false)
    }
  }, [])

  const captureAndAnalyze = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return

    setIsAnalyzing(true)
    const canvas = canvasRef.current
    const video = videoRef.current
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext("2d")
    if (ctx) {
      ctx.drawImage(video, 0, 0)
      const imageData = canvas.toDataURL("image/jpeg")
      setCapturedImage(imageData)

      // Simulate AI analysis
      await new Promise((resolve) => setTimeout(resolve, 1500))

      const mockResult: AnalysisResult = {
        lighting: "自然光，偏暖色调",
        colors: ["#4A90A4", "#D4A574", "#6B8E6B", "#E8D5B7"],
        objects: ["建筑", "植物", "天空"],
        mood: "宁静",
        suggestedStyles: STYLE_PRESETS.slice(0, 3),
      }
      setAnalysisResult(mockResult)
      onAnalysisComplete?.(mockResult)
    }
    setIsAnalyzing(false)
  }, [onAnalysisComplete])

  const applyFilter = useCallback(
    (filter: string) => {
      setSelectedFilter(filter)
      onFilterApply?.(filter)
    },
    [onFilterApply]
  )

  const resetAnalysis = useCallback(() => {
    setAnalysisResult(null)
    setCapturedImage(null)
    setSelectedFilter(null)
  }, [])

  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [stopCamera])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="px-4 py-3 glass-strong rounded-2xl mx-3 mt-3"
      >
        <div className="flex items-center gap-3">
          {onBack && (
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={onBack}
              className="w-8 h-8 rounded-xl bg-secondary/50 flex items-center justify-center"
            >
              <FontAwesomeIcon icon={faChevronLeft} className="text-foreground text-sm" />
            </motion.button>
          )}
          <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
            <FontAwesomeIcon icon={faCamera} className="text-primary text-lg" />
          </div>
          <div className="flex-1">
            <h2 className="text-base font-semibold text-foreground">实时场景分析</h2>
            <p className="text-xs text-muted-foreground">AI 智能识别环境与推荐风格</p>
          </div>
        </div>
      </motion.div>

      {/* Main View */}
      <div className="flex-1 px-3 py-3 overflow-hidden">
        <div className="relative w-full h-full rounded-2xl overflow-hidden bg-card">
          {/* Camera / Image Preview */}
          <AnimatePresence mode="wait">
            {!isStreaming && !capturedImage && !currentImage ? (
              <motion.div
                key="start"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6"
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={startCamera}
                  className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center cursor-pointer glow-sm"
                >
                  <FontAwesomeIcon icon={faCamera} className="text-primary text-3xl" />
                </motion.div>
                <p className="text-sm text-muted-foreground text-center">
                  点击启动后置摄像头
                  <br />
                  <span className="text-xs">进行实时环境识别</span>
                </p>
                {error && <p className="text-xs text-destructive mt-2">{error}</p>}
              </motion.div>
            ) : (
              <motion.div
                key="camera"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0"
              >
                {/* Video Stream */}
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className={`absolute inset-0 w-full h-full object-cover ${
                    capturedImage ? "hidden" : ""
                  } ${selectedFilter || ""}`}
                />

                {/* Captured Image */}
                {capturedImage && (
                  <img
                    src={capturedImage}
                    alt="Captured"
                    className={`absolute inset-0 w-full h-full object-cover ${selectedFilter || ""}`}
                  />
                )}

                {/* Current Background Image (from other modules) */}
                {currentImage && !capturedImage && !isStreaming && (
                  <img
                    src={currentImage}
                    alt="Current"
                    className={`absolute inset-0 w-full h-full object-cover ${selectedFilter || ""}`}
                  />
                )}

                {/* Hidden Canvas */}
                <canvas ref={canvasRef} className="hidden" />

                {/* Analyzing Overlay */}
                <AnimatePresence>
                  {isAnalyzing && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute inset-0 bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center gap-3"
                    >
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <FontAwesomeIcon icon={faSpinner} className="text-primary text-3xl" />
                      </motion.div>
                      <p className="text-sm text-foreground">AI 正在分析场景...</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Analysis Result Overlay */}
                <AnimatePresence>
                  {analysisResult && !isAnalyzing && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className="absolute inset-x-0 bottom-0 p-3"
                    >
                      {/* Analysis Info */}
                      <div className="glass-strong rounded-xl p-3 mb-3">
                        <div className="flex items-center gap-2 mb-2">
                          <FontAwesomeIcon icon={faLightbulb} className="text-accent text-sm" />
                          <span className="text-xs font-medium text-foreground">场景分析结果</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-muted-foreground">光线：</span>
                            <span className="text-foreground">{analysisResult.lighting}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">氛围：</span>
                            <span className="text-foreground">{analysisResult.mood}</span>
                          </div>
                        </div>
                        <div className="flex gap-1.5 mt-2">
                          {analysisResult.colors.map((color, i) => (
                            <div
                              key={i}
                              className="w-6 h-6 rounded-lg border border-border/50"
                              style={{ backgroundColor: color }}
                            />
                          ))}
                        </div>
                      </div>

                      {/* Style Suggestions */}
                      <div className="glass-strong rounded-xl p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <FontAwesomeIcon icon={faPalette} className="text-primary text-sm" />
                          <span className="text-xs font-medium text-foreground">推荐风格</span>
                        </div>
                        <div className="flex gap-2 overflow-x-auto pb-1">
                          {STYLE_PRESETS.map((style) => (
                            <motion.button
                              key={style.name}
                              whileTap={{ scale: 0.95 }}
                              onClick={() => applyFilter(style.filter)}
                              className={`flex-shrink-0 px-3 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                                selectedFilter === style.filter
                                  ? "bg-primary text-primary-foreground"
                                  : "bg-secondary/50 text-foreground hover:bg-secondary"
                              }`}
                            >
                              <FontAwesomeIcon icon={style.icon} className="text-xs" />
                              <span className="text-xs font-medium whitespace-nowrap">{style.name}</span>
                              {selectedFilter === style.filter && (
                                <FontAwesomeIcon icon={faCheck} className="text-xs" />
                              )}
                            </motion.button>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Bottom Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="px-3 pb-8 pt-2"
      >
        <div className="flex items-center justify-center gap-4">
          {isStreaming && !capturedImage && (
            <>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={stopCamera}
                className="w-12 h-12 rounded-full bg-destructive/20 flex items-center justify-center"
              >
                <FontAwesomeIcon icon={faXmark} className="text-destructive text-lg" />
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={captureAndAnalyze}
                className="w-16 h-16 rounded-full bg-primary flex items-center justify-center glow"
              >
                <FontAwesomeIcon icon={faBolt} className="text-primary-foreground text-2xl" />
              </motion.button>
              <div className="w-12" />
            </>
          )}
          {capturedImage && (
            <>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={resetAnalysis}
                className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center"
              >
                <FontAwesomeIcon icon={faRotate} className="text-foreground text-lg" />
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={() => {
                  resetAnalysis()
                  startCamera()
                }}
                className="w-16 h-16 rounded-full bg-primary flex items-center justify-center glow"
              >
                <FontAwesomeIcon icon={faCamera} className="text-primary-foreground text-2xl" />
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.9 }}
                onClick={() => onFilterApply?.(selectedFilter || "")}
                className="w-12 h-12 rounded-full bg-accent flex items-center justify-center"
              >
                <FontAwesomeIcon icon={faCheck} className="text-accent-foreground text-lg" />
              </motion.button>
            </>
          )}
        </div>
      </motion.div>
    </div>
  )
}
