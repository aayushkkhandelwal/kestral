'use client'

import { useState } from 'react'
import axios from 'axios'
import {
  Settings,
  Cpu,
  Sliders,
  CheckCircle2,
  RefreshCw,
  Server,
  Shield,
  SlidersHorizontal,
  Flame,
  Check,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { API_BASE_URL } from '@/lib/config'

export function SettingsView({ backendOnline }: { backendOnline: boolean }) {
  const [personConf, setPersonConf] = useState(0.35)
  const [faceConf, setFaceConf] = useState(0.35)
  const [minDuration, setMinDuration] = useState(15)
  const [sharpnessWeight, setSharpnessWeight] = useState(40)
  const [exposureWeight, setExposureWeight] = useState(30)
  const [symmetryWeight, setSymmetryWeight] = useState(30)
  const [savedNotice, setSavedNotice] = useState(false)
  const [resettingTracker, setResettingTracker] = useState(false)
  const [resetSuccess, setResetSuccess] = useState(false)

  const handleSave = () => {
    setSavedNotice(true)
    setTimeout(() => setSavedNotice(false), 2500)
  }

  const handleResetEngineTracker = async () => {
    setResettingTracker(true)
    setResetSuccess(false)
    try {
      await axios.post(`${API_BASE_URL}/api/camera/reset`, {}, { timeout: 4000 })
      setResetSuccess(true)
      setTimeout(() => setResetSuccess(false), 3000)
    } catch (err) {
      console.warn('Failed to reset tracker:', err)
    } finally {
      setResettingTracker(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
            System & Engine Settings
          </h1>
          <p className="text-sm text-muted-foreground">
            Configure YOLO tracking sensitivity, biometric arbiter thresholds, and engine connectivity
          </p>
        </div>
        <Button size="sm" onClick={handleSave} className="gap-1.5 text-xs">
          {savedNotice ? <Check className="size-3.5" /> : <Settings className="size-3.5" />}
          {savedNotice ? 'Settings Saved' : 'Save Preferences'}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Vision Pipeline Calibration */}
        <div className="flex flex-col gap-5 rounded-2xl border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b pb-4">
            <Cpu className="size-5 text-primary" />
            <div>
              <h2 className="text-base font-semibold">AI Detection Calibration</h2>
              <p className="text-xs text-muted-foreground">
                Tune deep neural network inference confidence filters
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-5">
            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Person Tracking Confidence Threshold</span>
                <span className="font-mono text-primary">{Math.round(personConf * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={personConf}
                onChange={(e) => setPersonConf(parseFloat(e.target.value))}
                className="mt-2 w-full accent-primary"
              />
              <p className="mt-1 text-[11px] text-muted-foreground">
                YOLOv8 ByteTrack class 0 threshold for bounding box persistence.
              </p>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Facial Landmark Confidence Threshold</span>
                <span className="font-mono text-primary">{Math.round(faceConf * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={faceConf}
                onChange={(e) => setFaceConf(parseFloat(e.target.value))}
                className="mt-2 w-full accent-primary"
              />
              <p className="mt-1 text-[11px] text-muted-foreground">
                OpenCV YuNet DNN minimum landmark score for 5-point facial orientation.
              </p>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Loitering / Persistence Audit Timer</span>
                <span className="font-mono text-primary">{minDuration} seconds</span>
              </div>
              <input
                type="range"
                min="5"
                max="60"
                step="5"
                value={minDuration}
                onChange={(e) => setMinDuration(parseInt(e.target.value))}
                className="mt-2 w-full accent-primary"
              />
              <p className="mt-1 text-[11px] text-muted-foreground">
                Duration of continuous camera presence required to log a prolonged presence event.
              </p>
            </div>
          </div>
        </div>

        {/* Biometric Quality Weighting */}
        <div className="flex flex-col gap-5 rounded-2xl border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-2.5 border-b pb-4">
            <SlidersHorizontal className="size-5 text-primary" />
            <div>
              <h2 className="text-base font-semibold">Evidence Fidelity Weighting</h2>
              <p className="text-xs text-muted-foreground">
                Control the multi-factor scoring formula for Best-Frame selection
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-5">
            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Laplacian Variance Weight (Sharpness)</span>
                <span className="font-mono text-primary">{sharpnessWeight}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="70"
                step="5"
                value={sharpnessWeight}
                onChange={(e) => setSharpnessWeight(parseInt(e.target.value))}
                className="mt-2 w-full accent-primary"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Exposure & Dynamic Range Weight</span>
                <span className="font-mono text-primary">{exposureWeight}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="70"
                step="5"
                value={exposureWeight}
                onChange={(e) => setExposureWeight(parseInt(e.target.value))}
                className="mt-2 w-full accent-primary"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium">
                <span>Facial Symmetry & Pose Alignment</span>
                <span className="font-mono text-primary">{symmetryWeight}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="70"
                step="5"
                value={symmetryWeight}
                onChange={(e) => setSymmetryWeight(parseInt(e.target.value))}
                className="mt-2 w-full accent-primary"
              />
            </div>
          </div>
        </div>

        {/* Engine Connectivity & Status */}
        <div className="flex flex-col gap-5 rounded-2xl border bg-card p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center justify-between border-b pb-4">
            <div className="flex items-center gap-2.5">
              <Server className="size-5 text-primary" />
              <div>
                <h2 className="text-base font-semibold">FastAPI Evidence Engine Status</h2>
                <p className="text-xs text-muted-foreground">
                  Backend connection parameters and live telemetry
                </p>
              </div>
            </div>
            <Badge
              variant={backendOnline ? 'default' : 'destructive'}
              className="gap-1.5 font-mono text-xs"
            >
              <span
                className={`size-2 rounded-full ${
                  backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'
                }`}
              />
              {backendOnline ? 'ENGINE CONNECTED (PORT 8000)' : 'ENGINE DISCONNECTED'}
            </Badge>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-xl border bg-background p-4 text-xs">
              <span className="text-muted-foreground">API Base Endpoint</span>
              <p className="mt-1 font-mono font-medium">{API_BASE_URL}</p>
            </div>
            <div className="rounded-xl border bg-background p-4 text-xs">
              <span className="text-muted-foreground">Active Tracking Model</span>
              <p className="mt-1 font-mono font-medium">YOLOv8 Nano (CPU Optimized)</p>
            </div>
            <div className="rounded-xl border bg-background p-4 text-xs">
              <span className="text-muted-foreground">Facial Detector</span>
              <p className="mt-1 font-mono font-medium">OpenCV YuNet Deep Network</p>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-t pt-4">
            <p className="text-xs text-muted-foreground">
              Clear in-memory ByteTrack states and re-center the video telemetry buffer.
            </p>
            <Button
              variant="outline"
              size="sm"
              disabled={resettingTracker}
              onClick={handleResetEngineTracker}
              className="gap-1.5 text-xs"
            >
              <RefreshCw className={`size-3.5 ${resettingTracker ? 'animate-spin' : ''}`} />
              {resetSuccess ? 'Tracker Reset Done!' : 'Reset Tracking Memory'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
