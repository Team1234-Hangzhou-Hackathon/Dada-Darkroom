"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import {
  faCrop,
  faFont,
  faDownload,
  faTrash,
  faRotate,
  faWandMagicSparkles,
  faSpinner,
  faXmark,
  faCirclePlay,
  faCirclePause,
  faImage,
  faShuffle,
  faUpDownLeftRight,
  faPaperPlane,
  faLightbulb,
} from "@fortawesome/free-solid-svg-icons"

interface CreativeCollageProps {
  backgroundImage?: string | null
  moodKeywords?: string[]
  onExport?: (data: StoryCard[]) => void
  onNavigateToModule?: (module: "scene" | "upload") => void
}

interface CollageElement {
  id: string
  type: "image" | "text" | "shape"
  x: number
  y: number
  width: number
  height: number
  rotation: number
  content: string
  style?: Record<string, string>
  zIndex: number
}

interface StoryCard {
  id: string
  title: string
  elements: CollageElement[]
  background: string
  mood: string
}

interface SelectionBox {
  x: number
  y: number
  width: number
  height: number
}

const MOOD_THEMES = [
  { keyword: "旅行回忆", gradient: "from-amber-500/20 to-orange-600/20", color: "#D4A574" },
  { keyword: "未来幻想", gradient: "from-cyan-500/20 to-blue-600/20", color: "#4A90A4" },
  { keyword: "自然宁静", gradient: "from-green-500/20 to-emerald-600/20", color: "#6B8E6B" },
  { keyword: "城市夜景", gradient: "from-purple-500/20 to-indigo-600/20", color: "#7C5CBF" },
  { keyword: "温馨时光", gradient: "from-rose-500/20 to-pink-600/20", color: "#E07B7B" },
]

const SAMPLE_IMAGES = [
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300",
  "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=300",
  "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=300",
  "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=300",
]

// Default background image for the canvas
const DEFAULT_CANVAS_IMAGE = "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=800&q=80"

export function CreativeCollage({ backgroundImage, moodKeywords = [], onExport, onNavigateToModule }: CreativeCollageProps) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [elements, setElements] = useState<CollageElement[]>([])
  const [selectedElement, setSelectedElement] = useState<string | null>(null)
  const [selectionBox, setSelectionBox] = useState<SelectionBox>({ x: 50, y: 60, width: 200, height: 260 })
  const [isResizing, setIsResizing] = useState<string | null>(null)
  const [isDraggingSelection, setIsDraggingSelection] = useState(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number; boxX: number; boxY: number } | null>(null)
  const [storyCards, setStoryCards] = useState<StoryCard[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [activeTab, setActiveTab] = useState<"edit" | "story">("edit")
  const [selectedMood, setSelectedMood] = useState<string>(moodKeywords[0] || "旅行回忆")
  const [textInput, setTextInput] = useState("")
  const [showTextInput, setShowTextInput] = useState(false)
  const [showSceneAnalysis, setShowSceneAnalysis] = useState(false)
  const [sceneAnalysisInput, setSceneAnalysisInput] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<{
    description: string
    tags: string[]
    suggestions: string[]
  } | null>(null)
  
  const canvasImage = backgroundImage || DEFAULT_CANVAS_IMAGE

  // Handle scene analysis
  const handleSceneAnalysis = useCallback(async () => {
    if (!sceneAnalysisInput.trim()) return
    setIsAnalyzing(true)
    setAnalysisResult(null)
    
    // Simulate AI analysis
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    setAnalysisResult({
      description: `基于"${sceneAnalysisInput}"的场景分析完成`,
      tags: ["自然", "宁静", "光影", "构图"],
      suggestions: [
        "建议使用暖色调滤镜",
        "可添加文字叙事元素",
        "适合拼贴创作"
      ]
    })
    setIsAnalyzing(false)
  }, [sceneAnalysisInput])

  const closeSceneAnalysis = useCallback(() => {
    setShowSceneAnalysis(false)
    setSceneAnalysisInput("")
    setAnalysisResult(null)
    setIsAnalyzing(false)
  }, [])

  // Handle selection box dragging
  const handleSelectionMouseDown = useCallback((e: React.MouseEvent) => {
    e.stopPropagation()
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    setIsDraggingSelection(true)
    setDragStart({
      x: e.clientX,
      y: e.clientY,
      boxX: selectionBox.x,
      boxY: selectionBox.y,
    })
  }, [selectionBox])

  // Handle resize from corners
  const handleResizeMouseDown = useCallback((e: React.MouseEvent, corner: string) => {
    e.stopPropagation()
    setIsResizing(corner)
    setDragStart({
      x: e.clientX,
      y: e.clientY,
      boxX: selectionBox.x,
      boxY: selectionBox.y,
    })
  }, [selectionBox])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!canvasRef.current || !dragStart) return
    const rect = canvasRef.current.getBoundingClientRect()
    const deltaX = e.clientX - dragStart.x
    const deltaY = e.clientY - dragStart.y

    if (isDraggingSelection) {
      const newX = Math.max(0, Math.min(rect.width - selectionBox.width, dragStart.boxX + deltaX))
      const newY = Math.max(0, Math.min(rect.height - selectionBox.height, dragStart.boxY + deltaY))
      setSelectionBox(prev => ({ ...prev, x: newX, y: newY }))
    } else if (isResizing) {
      let newBox = { ...selectionBox }
      const minSize = 60

      if (isResizing.includes('e')) {
        newBox.width = Math.max(minSize, selectionBox.width + deltaX)
      }
      if (isResizing.includes('w')) {
        const newWidth = Math.max(minSize, selectionBox.width - deltaX)
        newBox.x = dragStart.boxX + (selectionBox.width - newWidth)
        newBox.width = newWidth
      }
      if (isResizing.includes('s')) {
        newBox.height = Math.max(minSize, selectionBox.height + deltaY)
      }
      if (isResizing.includes('n')) {
        const newHeight = Math.max(minSize, selectionBox.height - deltaY)
        newBox.y = dragStart.boxY + (selectionBox.height - newHeight)
        newBox.height = newHeight
      }

      // Clamp to canvas bounds
      newBox.x = Math.max(0, newBox.x)
      newBox.y = Math.max(0, newBox.y)
      newBox.width = Math.min(rect.width - newBox.x, newBox.width)
      newBox.height = Math.min(rect.height - newBox.y, newBox.height)

      setSelectionBox(newBox)
    }
  }, [isDraggingSelection, isResizing, dragStart, selectionBox])

  const handleMouseUp = useCallback(() => {
    setIsDraggingSelection(false)
    setIsResizing(null)
    setDragStart(null)
  }, [])

  const addImageElement = useCallback((imageUrl?: string) => {
    const newElement: CollageElement = {
      id: `element-${Date.now()}`,
      type: "image",
      x: selectionBox.x,
      y: selectionBox.y,
      width: selectionBox.width,
      height: selectionBox.height,
      rotation: 0,
      content: imageUrl || SAMPLE_IMAGES[Math.floor(Math.random() * SAMPLE_IMAGES.length)],
      zIndex: elements.length,
    }
    setElements([...elements, newElement])
    setSelectedElement(newElement.id)
  }, [elements, selectionBox])

  const addTextElement = useCallback(() => {
    if (!textInput.trim()) return
    const newElement: CollageElement = {
      id: `element-${Date.now()}`,
      type: "text",
      x: selectionBox.x,
      y: selectionBox.y,
      width: selectionBox.width,
      height: 40,
      rotation: 0,
      content: textInput,
      style: { fontSize: "14px", color: "#ffffff", fontWeight: "600" },
      zIndex: elements.length,
    }
    setElements([...elements, newElement])
    setTextInput("")
    setShowTextInput(false)
    setSelectedElement(newElement.id)
  }, [elements, textInput, selectionBox])

  const deleteElement = useCallback((id: string) => {
    setElements(elements.filter(el => el.id !== id))
    if (selectedElement === id) setSelectedElement(null)
  }, [elements, selectedElement])

  const generateStoryCards = useCallback(async () => {
    setIsGenerating(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    const theme = MOOD_THEMES.find(t => t.keyword === selectedMood) || MOOD_THEMES[0]
    const cards: StoryCard[] = [
      {
        id: "card-1",
        title: `${selectedMood} · 开篇`,
        elements: elements.slice(0, Math.ceil(elements.length / 2)),
        background: theme.gradient,
        mood: selectedMood,
      },
      {
        id: "card-2",
        title: `${selectedMood} · 发展`,
        elements: elements.slice(Math.ceil(elements.length / 2)),
        background: theme.gradient,
        mood: selectedMood,
      },
      {
        id: "card-3",
        title: `${selectedMood} · 终章`,
        elements: elements,
        background: theme.gradient,
        mood: selectedMood,
      },
    ]
    
    setStoryCards(cards)
    setActiveTab("story")
    setIsGenerating(false)
  }, [elements, selectedMood])

  const playStoryboard = useCallback(() => {
    setIsPlaying(true)
    setCurrentCardIndex(0)
  }, [])

  const stopStoryboard = useCallback(() => {
    setIsPlaying(false)
    setCurrentCardIndex(0)
  }, [])

  // Auto-advance story cards when playing
  useEffect(() => {
    if (!isPlaying || storyCards.length === 0) return
    const timer = setInterval(() => {
      setCurrentCardIndex(prev => {
        if (prev >= storyCards.length - 1) {
          setIsPlaying(false)
          return 0
        }
        return prev + 1
      })
    }, 2000)
    return () => clearInterval(timer)
  }, [isPlaying, storyCards.length])

  const handleExport = useCallback(() => {
    onExport?.(storyCards)
    // Simulate download
    const link = document.createElement("a")
    link.download = `storyboard-${Date.now()}.json`
    link.href = `data:application/json,${encodeURIComponent(JSON.stringify(storyCards))}`
    link.click()
  }, [storyCards, onExport])

  return (
    <div className="flex flex-col h-full">
      {/* Tab Switcher - moved to top */}
      <div className="px-3 pt-3">
        <div className="flex gap-2 p-1 bg-secondary/30 rounded-xl">
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab("edit")}
            className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "edit" ? "bg-primary text-primary-foreground" : "text-muted-foreground"
            }`}
          >
            <FontAwesomeIcon icon={faCrop} className="mr-1.5" />
            编辑拼贴
          </motion.button>
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab("story")}
            className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "story" ? "bg-primary text-primary-foreground" : "text-muted-foreground"
            }`}
          >
            <FontAwesomeIcon icon={faCirclePlay} className="mr-1.5" />
            故事板
          </motion.button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 px-3 py-2 overflow-hidden">
        <AnimatePresence mode="wait">
          {activeTab === "edit" ? (
            <motion.div
              key="edit"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="h-full flex flex-col"
            >
              {/* Canvas Area with Image, Mask and Selection */}
              <div
                ref={canvasRef}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                className="relative flex-1 rounded-2xl overflow-hidden cursor-default select-none"
              >
                {/* Background Image */}
                <img
                  src={canvasImage}
                  alt="Canvas background"
                  className="absolute inset-0 w-full h-full object-cover"
                  crossOrigin="anonymous"
                  draggable={false}
                />

                {/* Dark Overlay Mask with Cutout */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  <defs>
                    <mask id="selection-mask">
                      <rect width="100%" height="100%" fill="white" />
                      <rect
                        x={selectionBox.x}
                        y={selectionBox.y}
                        width={selectionBox.width}
                        height={selectionBox.height}
                        fill="black"
                        rx="8"
                      />
                    </mask>
                  </defs>
                  <rect
                    width="100%"
                    height="100%"
                    fill="rgba(0, 0, 0, 0.6)"
                    mask="url(#selection-mask)"
                  />
                </svg>

                {/* Selection Box - Draggable Area */}
                <motion.div
                  className="absolute cursor-move border-2 border-white/80 rounded-lg shadow-lg"
                  style={{
                    left: selectionBox.x,
                    top: selectionBox.y,
                    width: selectionBox.width,
                    height: selectionBox.height,
                  }}
                  onMouseDown={handleSelectionMouseDown}
                >
                  {/* Corner Resize Handles */}
                  {/* Top-left */}
                  <div
                    onMouseDown={(e) => handleResizeMouseDown(e, 'nw')}
                    className="absolute -top-2 -left-2 w-5 h-5 bg-white rounded-full cursor-nw-resize shadow-md flex items-center justify-center"
                  >
                    <div className="w-2 h-2 bg-primary rounded-full" />
                  </div>
                  {/* Top-right */}
                  <div
                    onMouseDown={(e) => handleResizeMouseDown(e, 'ne')}
                    className="absolute -top-2 -right-2 w-5 h-5 bg-white rounded-full cursor-ne-resize shadow-md flex items-center justify-center"
                  >
                    <div className="w-2 h-2 bg-primary rounded-full" />
                  </div>
                  {/* Bottom-left */}
                  <div
                    onMouseDown={(e) => handleResizeMouseDown(e, 'sw')}
                    className="absolute -bottom-2 -left-2 w-5 h-5 bg-white rounded-full cursor-sw-resize shadow-md flex items-center justify-center"
                  >
                    <div className="w-2 h-2 bg-primary rounded-full" />
                  </div>
                  {/* Bottom-right */}
                  <div
                    onMouseDown={(e) => handleResizeMouseDown(e, 'se')}
                    className="absolute -bottom-2 -right-2 w-5 h-5 bg-white rounded-full cursor-se-resize shadow-md flex items-center justify-center"
                  >
                    <div className="w-2 h-2 bg-primary rounded-full" />
                  </div>

                  {/* Move indicator in center */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <FontAwesomeIcon icon={faUpDownLeftRight} className="text-white text-sm" />
                    </div>
                  </div>
                </motion.div>

                {/* Elements */}
                {elements.map((element) => (
                  <motion.div
                    key={element.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={`absolute cursor-move ${selectedElement === element.id ? "ring-2 ring-primary" : ""}`}
                    style={{
                      left: element.x,
                      top: element.y,
                      width: element.width,
                      height: element.type === "text" ? "auto" : element.height,
                      transform: `rotate(${element.rotation}deg)`,
                      zIndex: element.zIndex,
                    }}
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedElement(element.id)
                    }}
                    drag
                    dragMomentum={false}
                    onDragEnd={(_, info) => {
                      setElements(elements.map(el => 
                        el.id === element.id 
                          ? { ...el, x: el.x + info.offset.x, y: el.y + info.offset.y }
                          : el
                      ))
                    }}
                  >
                    {element.type === "image" ? (
                      <img
                        src={element.content}
                        alt=""
                        className="w-full h-full object-cover rounded-lg shadow-lg"
                        crossOrigin="anonymous"
                        draggable={false}
                      />
                    ) : (
                      <div
                        className="px-3 py-2 rounded-lg glass-strong"
                        style={element.style}
                      >
                        {element.content}
                      </div>
                    )}
                    
                    {/* Element Controls */}
                    {selectedElement === element.id && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="absolute -top-8 left-1/2 -translate-x-1/2 flex gap-1"
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setElements(elements.map(el => 
                              el.id === element.id 
                                ? { ...el, rotation: el.rotation + 15 }
                                : el
                            ))
                          }}
                          className="w-6 h-6 rounded-md bg-secondary flex items-center justify-center"
                        >
                          <FontAwesomeIcon icon={faRotate} className="text-foreground text-xs" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteElement(element.id)
                          }}
                          className="w-6 h-6 rounded-md bg-destructive flex items-center justify-center"
                        >
                          <FontAwesomeIcon icon={faTrash} className="text-destructive-foreground text-xs" />
                        </button>
                      </motion.div>
                    )}
                  </motion.div>
                ))}

                {/* Text Input Modal */}
                <AnimatePresence>
                  {showTextInput && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center p-6"
                    >
                      <div className="w-full glass-strong rounded-xl p-4">
                        <input
                          type="text"
                          value={textInput}
                          onChange={(e) => setTextInput(e.target.value)}
                          placeholder="输入文字..."
                          className="w-full px-3 py-2 bg-secondary/50 rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 mb-3"
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <motion.button
                            whileTap={{ scale: 0.95 }}
                            onClick={() => setShowTextInput(false)}
                            className="flex-1 py-2 rounded-lg bg-secondary text-foreground text-sm"
                          >
                            取消
                          </motion.button>
                          <motion.button
                            whileTap={{ scale: 0.95 }}
                            onClick={addTextElement}
                            className="flex-1 py-2 rounded-lg bg-primary text-primary-foreground text-sm"
                          >
                            添加
                          </motion.button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Scene Analysis Overlay */}
                <AnimatePresence>
                  {showSceneAnalysis && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="absolute inset-0 z-20"
                    >
                      {/* Backdrop */}
                      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={closeSceneAnalysis} />
                      
                      {/* Analysis Panel - centered over canvas */}
                      <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[85%] max-w-[280px] glass-strong rounded-2xl overflow-hidden border border-white/20 shadow-2xl"
                      >
                        {/* Header */}
                        <div className="flex items-center justify-between px-3 py-2 border-b border-white/10">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-lg bg-primary/20 flex items-center justify-center">
                              <FontAwesomeIcon icon={faLightbulb} className="text-primary text-xs" />
                            </div>
                            <span className="text-xs font-medium text-foreground">场景分析</span>
                          </div>
                          <motion.button
                            whileTap={{ scale: 0.9 }}
                            onClick={closeSceneAnalysis}
                            className="w-6 h-6 rounded-full bg-secondary/50 flex items-center justify-center"
                          >
                            <FontAwesomeIcon icon={faXmark} className="text-muted-foreground text-xs" />
                          </motion.button>
                        </div>

                        {/* Content */}
                        <div className="p-3 space-y-3 overflow-y-auto max-h-[280px]">
                          {/* Input Area */}
                          <div className="relative">
                            <textarea
                              value={sceneAnalysisInput}
                              onChange={(e) => setSceneAnalysisInput(e.target.value)}
                              placeholder="描述您想分析的场景内容..."
                              className="w-full px-3 py-2 pr-10 bg-secondary/50 rounded-xl text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                              rows={2}
                              autoFocus
                            />
                            <motion.button
                              whileTap={{ scale: 0.9 }}
                              onClick={handleSceneAnalysis}
                              disabled={isAnalyzing || !sceneAnalysisInput.trim()}
                              className="absolute right-2 bottom-2 w-7 h-7 rounded-lg bg-primary flex items-center justify-center disabled:opacity-50"
                            >
                              {isAnalyzing ? (
                                <FontAwesomeIcon icon={faSpinner} className="text-primary-foreground text-xs animate-spin" />
                              ) : (
                                <FontAwesomeIcon icon={faPaperPlane} className="text-primary-foreground text-xs" />
                              )}
                            </motion.button>
                          </div>

                          {/* Analysis Result */}
                          <AnimatePresence>
                            {isAnalyzing && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                className="flex items-center justify-center py-4"
                              >
                                <div className="flex flex-col items-center gap-2">
                                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                                    <FontAwesomeIcon icon={faSpinner} className="text-primary animate-spin" />
                                  </div>
                                  <span className="text-xs text-muted-foreground">AI 正在分析...</span>
                                </div>
                              </motion.div>
                            )}
                            
                            {analysisResult && !isAnalyzing && (
                              <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="space-y-2"
                              >
                                {/* Description */}
                                <p className="text-xs text-foreground">{analysisResult.description}</p>
                                
                                {/* Tags */}
                                <div className="flex flex-wrap gap-1">
                                  {analysisResult.tags.map((tag, i) => (
                                    <span
                                      key={i}
                                      className="px-2 py-0.5 rounded-md bg-primary/20 text-primary text-[10px] font-medium"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                                
                                {/* Suggestions */}
                                <div className="space-y-1 pt-1">
                                  {analysisResult.suggestions.map((suggestion, i) => (
                                    <div key={i} className="flex items-start gap-1.5">
                                      <FontAwesomeIcon icon={faLightbulb} className="text-accent text-[10px] mt-0.5" />
                                      <span className="text-[10px] text-muted-foreground">{suggestion}</span>
                                    </div>
                                  ))}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      </motion.div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Quick Actions - Navigate to other modules */}
              <div className="flex gap-2 mt-3">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onNavigateToModule?.("upload")}
                  className="flex-1 py-2.5 rounded-xl bg-accent/20 text-accent text-xs font-medium flex items-center justify-center gap-2 hover:bg-accent/30 transition-colors"
                >
                  <FontAwesomeIcon icon={faImage} />
                  从图片库选择
                </motion.button>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowSceneAnalysis(true)}
                  className="flex-1 py-2.5 rounded-xl bg-primary/20 text-primary text-xs font-medium flex items-center justify-center gap-2 hover:bg-primary/30 transition-colors"
                >
                  <FontAwesomeIcon icon={faShuffle} />
                  场景分析
                </motion.button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="story"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="h-full flex flex-col"
            >
              {storyCards.length > 0 ? (
                <>
                  {/* Story Preview */}
                  <div className="relative flex-1 rounded-2xl overflow-hidden bg-card">
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={storyCards[currentCardIndex]?.id || "empty"}
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -50 }}
                        className={`absolute inset-0 bg-gradient-to-br ${storyCards[currentCardIndex]?.background || MOOD_THEMES[0].gradient}`}
                      >
                        {/* Card Title */}
                        <div className="absolute top-4 left-4 right-4">
                          <h3 className="text-lg font-bold text-foreground">
                            {storyCards[currentCardIndex]?.title}
                          </h3>
                        </div>

                        {/* Card Elements Preview */}
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="flex gap-2 flex-wrap justify-center p-8">
                            {storyCards[currentCardIndex]?.elements.map((el) => (
                              el.type === "image" ? (
                                <img
                                  key={el.id}
                                  src={el.content}
                                  alt=""
                                  className="w-20 h-20 object-cover rounded-lg shadow-lg"
                                  crossOrigin="anonymous"
                                />
                              ) : (
                                <span key={el.id} className="text-foreground text-sm font-medium glass-strong px-3 py-1.5 rounded-lg">
                                  {el.content}
                                </span>
                              )
                            ))}
                          </div>
                        </div>

                        {/* Card Index */}
                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5">
                          {storyCards.map((_, i) => (
                            <div
                              key={i}
                              className={`w-2 h-2 rounded-full transition-colors ${
                                i === currentCardIndex ? "bg-foreground" : "bg-foreground/30"
                              }`}
                            />
                          ))}
                        </div>
                      </motion.div>
                    </AnimatePresence>

                    {/* Playback Controls */}
                    <div className="absolute bottom-4 right-4 flex gap-2">
                      <motion.button
                        whileTap={{ scale: 0.9 }}
                        onClick={isPlaying ? stopStoryboard : playStoryboard}
                        className="w-10 h-10 rounded-full glass flex items-center justify-center"
                      >
                        <FontAwesomeIcon
                          icon={isPlaying ? faCirclePause : faCirclePlay}
                          className="text-foreground text-lg"
                        />
                      </motion.button>
                    </div>
                  </div>

                  {/* Card Navigation */}
                  <div className="flex gap-2 mt-3 overflow-x-auto pb-1">
                    {storyCards.map((card, i) => (
                      <motion.button
                        key={card.id}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => {
                          setCurrentCardIndex(i)
                          setIsPlaying(false)
                        }}
                        className={`flex-shrink-0 px-4 py-2 rounded-lg text-xs font-medium transition-colors ${
                          i === currentCardIndex
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary/50 text-muted-foreground"
                        }`}
                      >
                        {card.title}
                      </motion.button>
                    ))}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
                  <FontAwesomeIcon icon={faWandMagicSparkles} className="text-4xl text-muted-foreground/50 mb-3" />
                  <p className="text-sm text-muted-foreground mb-4">
                    先在编辑模式添加元素
                    <br />
                    然后生成故事卡片
                  </p>
                  {elements.length > 0 && (
                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={generateStoryCards}
                      disabled={isGenerating}
                      className="px-6 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-medium glow-sm"
                    >
                      {isGenerating ? (
                        <>
                          <FontAwesomeIcon icon={faSpinner} className="animate-spin mr-2" />
                          生成中...
                        </>
                      ) : (
                        <>
                          <FontAwesomeIcon icon={faWandMagicSparkles} className="mr-2" />
                          生成故事卡片
                        </>
                      )}
                    </motion.button>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="px-3 pb-8 pt-2"
      >
        {activeTab === "edit" ? (
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={generateStoryCards}
            disabled={elements.length === 0 || isGenerating}
            className={`w-full py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 ${
              elements.length > 0
                ? "bg-primary text-primary-foreground glow-sm"
                : "bg-secondary text-muted-foreground"
            }`}
          >
            {isGenerating ? (
              <>
                <FontAwesomeIcon icon={faSpinner} className="animate-spin" />
                AI 生成故事中...
              </>
            ) : (
              <>
                <FontAwesomeIcon icon={faWandMagicSparkles} />
                生成视觉叙事卡片
              </>
            )}
          </motion.button>
        ) : storyCards.length > 0 ? (
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={handleExport}
            className="w-full py-3 rounded-xl bg-accent text-accent-foreground font-medium text-sm glow-sm flex items-center justify-center gap-2"
          >
            <FontAwesomeIcon icon={faDownload} />
            导出故事板
          </motion.button>
        ) : null}
      </motion.div>
    </div>
  )
}
