"use client"

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { IPhoneContainer } from "@/components/phone/iphone-container"
import { SceneAnalysis } from "@/components/modules/scene-analysis"
import { ImageUpload } from "@/components/modules/image-upload"
import { CreativeCollage } from "@/components/modules/creative-collage"
import "@/lib/fontawesome"

type ActiveModule = "scene" | "upload" | "collage"

export function MultiModalDemo() {
  const [activeModule, setActiveModule] = useState<ActiveModule>("collage")
  const [backgroundImage, setBackgroundImage] = useState<string | null>(null)
  const [currentFilter, setCurrentFilter] = useState<string | null>(null)
  const [moodData, setMoodData] = useState<{ mood: string; tags: string[]; colors: string[] } | null>(null)

  const handleImageSelect = useCallback((imageUrl: string, analysis: { dominantColors: string[]; mood: string; tags: string[] }) => {
    setBackgroundImage(imageUrl)
    setMoodData({ mood: analysis.mood, tags: analysis.tags, colors: analysis.dominantColors })
  }, [])

  const handleFilterApply = useCallback((filter: string) => {
    setCurrentFilter(filter)
  }, [])

  const handleMoodExtract = useCallback((data: { mood: string; tags: string[]; colors: string[] }) => {
    setMoodData(data)
  }, [])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      {/* iPhone Container Only */}
      <IPhoneContainer>
        <AnimatePresence mode="wait">
          {activeModule === "scene" && (
            <motion.div
              key="scene"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="h-full"
            >
              <SceneAnalysis
                currentImage={backgroundImage}
                onFilterApply={handleFilterApply}
                onBack={() => setActiveModule("collage")}
                onAnalysisComplete={(result) => {
                  setMoodData({
                    mood: result.mood,
                    tags: result.objects,
                    colors: result.colors,
                  })
                }}
              />
            </motion.div>
          )}
          {activeModule === "upload" && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="h-full"
            >
              <ImageUpload
                onImageSelect={handleImageSelect}
                onMoodExtract={handleMoodExtract}
                onBack={() => setActiveModule("collage")}
              />
            </motion.div>
          )}
          {activeModule === "collage" && (
            <motion.div
              key="collage"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="h-full"
            >
              <CreativeCollage
                backgroundImage={backgroundImage}
                moodKeywords={moodData?.tags || []}
                onNavigateToModule={(module) => setActiveModule(module)}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </IPhoneContainer>
    </div>
  )
}
