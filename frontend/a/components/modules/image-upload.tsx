"use client"

import { useState, useCallback, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome"
import {
  faUpload,
  faSearch,
  faPalette,
  faDroplet,
  faHeart,
  faFire,
  faSnowflake,
  faLeaf,
  faSun,
  faXmark,
  faCheck,
  faSpinner,
  faGripLines,
  faChevronLeft,
} from "@fortawesome/free-solid-svg-icons"

interface ImageUploadProps {
  onImageSelect?: (imageUrl: string, analysis: ImageAnalysis) => void
  onMoodExtract?: (mood: MoodData) => void
  onBack?: () => void
}

interface ImageAnalysis {
  dominantColors: string[]
  mood: string
  tags: string[]
}

interface MoodData {
  mood: string
  tags: string[]
  colors: string[]
  suggestions: string[]
}

interface UnsplashImage {
  id: string
  urls: {
    regular: string
    small: string
    thumb: string
  }
  alt_description: string
  user: {
    name: string
  }
  color: string
}

const MOOD_ICONS: Record<string, typeof faHeart> = {
  宁静: faSnowflake,
  活力: faFire,
  忧郁: faDroplet,
  温馨: faSun,
  自然: faLeaf,
  浪漫: faHeart,
}

const SEARCH_CATEGORIES = [
  { label: "自然", query: "nature landscape" },
  { label: "城市", query: "city urban" },
  { label: "人物", query: "portrait people" },
  { label: "抽象", query: "abstract minimal" },
  { label: "建筑", query: "architecture" },
  { label: "海洋", query: "ocean beach" },
]

// Demo images from Unsplash (using their demo API)
const DEMO_IMAGES: UnsplashImage[] = [
  {
    id: "1",
    urls: {
      regular: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
      small: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
      thumb: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=200",
    },
    alt_description: "Mountain landscape",
    user: { name: "Samuel Ferrara" },
    color: "#4A90A4",
  },
  {
    id: "2",
    urls: {
      regular: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800",
      small: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
      thumb: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200",
    },
    alt_description: "Portrait",
    user: { name: "Joseph Gonzalez" },
    color: "#D4A574",
  },
  {
    id: "3",
    urls: {
      regular: "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=800",
      small: "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=400",
      thumb: "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=200",
    },
    alt_description: "Lake reflection",
    user: { name: "Pietro De Grandi" },
    color: "#6B8E6B",
  },
  {
    id: "4",
    urls: {
      regular: "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=800",
      small: "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=400",
      thumb: "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=200",
    },
    alt_description: "Starry mountain",
    user: { name: "Benjamin Voros" },
    color: "#1a1a2e",
  },
  {
    id: "5",
    urls: {
      regular: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800",
      small: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=400",
      thumb: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=200",
    },
    alt_description: "Lake and mountains",
    user: { name: "Kalen Emsley" },
    color: "#87CEEB",
  },
  {
    id: "6",
    urls: {
      regular: "https://images.unsplash.com/photo-1476820865390-c52aeebb9891?w=800",
      small: "https://images.unsplash.com/photo-1476820865390-c52aeebb9891?w=400",
      thumb: "https://images.unsplash.com/photo-1476820865390-c52aeebb9891?w=200",
    },
    alt_description: "Desert sunset",
    user: { name: "Keith Hardy" },
    color: "#E8D5B7",
  },
]

export function ImageUpload({ onImageSelect, onMoodExtract, onBack }: ImageUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [images, setImages] = useState<UnsplashImage[]>(DEMO_IMAGES)
  const [selectedImage, setSelectedImage] = useState<UnsplashImage | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [moodAnalysis, setMoodAnalysis] = useState<MoodData | null>(null)
  const [activeCategory, setActiveCategory] = useState<string | null>(null)

  const searchImages = useCallback(async (query: string) => {
    if (!query.trim()) return
    setIsLoading(true)
    // Simulate API call - in production would use Unsplash API
    await new Promise((resolve) => setTimeout(resolve, 800))
    // Shuffle demo images to simulate search results
    setImages([...DEMO_IMAGES].sort(() => Math.random() - 0.5))
    setIsLoading(false)
  }, [])

  const handleCategoryClick = useCallback(
    (category: { label: string; query: string }) => {
      setActiveCategory(category.label)
      setSearchQuery(category.query)
      searchImages(category.query)
    },
    [searchImages]
  )

  const analyzeImage = useCallback(
    async (imageUrl: string) => {
      setIsLoading(true)
      // Simulate AI analysis
      await new Promise((resolve) => setTimeout(resolve, 1000))

      const moods = ["宁静", "活力", "忧郁", "温馨", "自然", "浪漫"]
      const randomMood = moods[Math.floor(Math.random() * moods.length)]
      const analysis: MoodData = {
        mood: randomMood,
        tags: ["风景", "自然", "宁静"],
        colors: ["#4A90A4", "#D4A574", "#6B8E6B", "#E8D5B7"],
        suggestions: ["适合旅行主题", "可用于背景", "建议搭配暖色文字"],
      }

      setMoodAnalysis(analysis)
      onMoodExtract?.(analysis)
      onImageSelect?.(imageUrl, {
        dominantColors: analysis.colors,
        mood: analysis.mood,
        tags: analysis.tags,
      })
      setIsLoading(false)
    },
    [onImageSelect, onMoodExtract]
  )

  const handleImageSelect = useCallback(
    (image: UnsplashImage) => {
      setSelectedImage(image)
      setUploadedImage(null)
      analyzeImage(image.urls.regular)
    },
    [analyzeImage]
  )

  const handleFileUpload = useCallback(
    (file: File) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string
        setUploadedImage(dataUrl)
        setSelectedImage(null)
        analyzeImage(dataUrl)
      }
      reader.readAsDataURL(file)
    },
    [analyzeImage]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files[0]
      if (file && file.type.startsWith("image/")) {
        handleFileUpload(file)
      }
    },
    [handleFileUpload]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragging(false)
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedImage(null)
    setUploadedImage(null)
    setMoodAnalysis(null)
  }, [])

  const currentImageUrl = uploadedImage || selectedImage?.urls.regular

  return (
    <div className="flex flex-col h-full">
      {/* Search Bar with Back Button */}
      <div className="px-3 pt-3">
        <div className="flex items-center gap-2">
          {onBack && (
            <motion.button
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              whileTap={{ scale: 0.9 }}
              onClick={onBack}
              className="w-10 h-10 rounded-xl bg-secondary/50 flex items-center justify-center flex-shrink-0"
            >
              <FontAwesomeIcon icon={faChevronLeft} className="text-foreground text-sm" />
            </motion.button>
          )}
          <div className="relative flex-1">
            <FontAwesomeIcon
              icon={faSearch}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchImages(searchQuery)}
              placeholder="搜索 Unsplash 图库..."
              className="w-full pl-9 pr-4 py-2.5 bg-secondary/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>

        {/* Categories */}
        <div className="flex gap-2 mt-2 overflow-x-auto pb-1">
          {SEARCH_CATEGORIES.map((cat) => (
            <motion.button
              key={cat.label}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleCategoryClick(cat)}
              className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeCategory === cat.label
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary/50 text-muted-foreground hover:bg-secondary"
              }`}
            >
              {cat.label}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 px-3 py-3 overflow-hidden">
        <AnimatePresence mode="wait">
          {currentImageUrl ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex flex-col"
            >
              {/* Selected Image Preview */}
              <div className="relative flex-1 rounded-2xl overflow-hidden bg-card">
                <img
                  src={currentImageUrl}
                  alt="Selected"
                  className="w-full h-full object-cover"
                  crossOrigin="anonymous"
                />

                {/* Close Button */}
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={clearSelection}
                  className="absolute top-3 right-3 w-8 h-8 rounded-full glass flex items-center justify-center"
                >
                  <FontAwesomeIcon icon={faXmark} className="text-foreground text-sm" />
                </motion.button>

                {/* Loading Overlay */}
                <AnimatePresence>
                  {isLoading && (
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
                      <p className="text-sm text-foreground">分析图片中...</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Mood Analysis Result */}
                <AnimatePresence>
                  {moodAnalysis && !isLoading && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 20 }}
                      className="absolute inset-x-0 bottom-0 p-3"
                    >
                      <div className="glass-strong rounded-xl p-3">
                        {/* Mood Tag */}
                        <div className="flex items-center gap-2 mb-3">
                          <div className="px-3 py-1.5 rounded-lg bg-primary/20 flex items-center gap-2">
                            <FontAwesomeIcon
                              icon={MOOD_ICONS[moodAnalysis.mood] || faHeart}
                              className="text-primary text-sm"
                            />
                            <span className="text-sm font-medium text-foreground">{moodAnalysis.mood}</span>
                          </div>
                          {moodAnalysis.tags.map((tag) => (
                            <span key={tag} className="px-2 py-1 rounded-md bg-secondary/50 text-xs text-muted-foreground">
                              {tag}
                            </span>
                          ))}
                        </div>

                        {/* Colors */}
                        <div className="flex items-center gap-2 mb-3">
                          <FontAwesomeIcon icon={faPalette} className="text-muted-foreground text-xs" />
                          <span className="text-xs text-muted-foreground">主色调</span>
                          <div className="flex gap-1.5 ml-1">
                            {moodAnalysis.colors.map((color, i) => (
                              <div
                                key={i}
                                className="w-6 h-6 rounded-lg border border-border/50 shadow-sm"
                                style={{ backgroundColor: color }}
                              />
                            ))}
                          </div>
                        </div>

                        {/* Suggestions */}
                        <div className="space-y-1">
                          {moodAnalysis.suggestions.map((suggestion, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                              <FontAwesomeIcon icon={faCheck} className="text-primary text-[10px]" />
                              <span>{suggestion}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="gallery"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex flex-col"
            >
              {/* Upload Area */}
              <motion.div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
                className={`relative p-4 rounded-xl border-2 border-dashed transition-colors cursor-pointer mb-3 ${
                  isDragging ? "border-primary bg-primary/10" : "border-border bg-card hover:border-primary/50"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                  className="hidden"
                />
                <div className="flex flex-col items-center gap-2">
                  <FontAwesomeIcon
                    icon={isDragging ? faGripLines : faUpload}
                    className={`text-2xl ${isDragging ? "text-primary" : "text-muted-foreground"}`}
                  />
                  <p className="text-xs text-muted-foreground text-center">
                    {isDragging ? "释放以上传图片" : "拖拽或点击上传本地图片"}
                  </p>
                </div>
              </motion.div>

              {/* Image Gallery */}
              <div className="flex-1 overflow-y-auto">
                {isLoading && !currentImageUrl ? (
                  <div className="flex items-center justify-center h-full">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    >
                      <FontAwesomeIcon icon={faSpinner} className="text-primary text-2xl" />
                    </motion.div>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-2">
                    {images.map((image, index) => (
                      <motion.div
                        key={image.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleImageSelect(image)}
                        className="relative aspect-square rounded-xl overflow-hidden cursor-pointer bg-card"
                      >
                        <img
                          src={image.urls.small}
                          alt={image.alt_description || ""}
                          className="w-full h-full object-cover"
                          crossOrigin="anonymous"
                          loading="lazy"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-background/60 to-transparent opacity-0 hover:opacity-100 transition-opacity">
                          <div className="absolute bottom-2 left-2 right-2">
                            <p className="text-xs text-foreground truncate">{image.user.name}</p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Actions */}
      {currentImageUrl && moodAnalysis && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-3 pb-8 pt-2"
        >
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={() => onImageSelect?.(currentImageUrl, {
              dominantColors: moodAnalysis.colors,
              mood: moodAnalysis.mood,
              tags: moodAnalysis.tags,
            })}
            className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-medium text-sm glow-sm"
          >
            <FontAwesomeIcon icon={faCheck} className="mr-2" />
            应用此图片
          </motion.button>
        </motion.div>
      )}
    </div>
  )
}
