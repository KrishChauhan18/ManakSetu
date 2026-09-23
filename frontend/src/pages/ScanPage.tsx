import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Camera,
  UploadCloud,
  X,
  RotateCw,
  Crop,
  Eye,
  Trash2,
  CheckCircle2,
  MapPin,
  Clock3,
  Smartphone,
  Hash,
  Sparkles,
} from "lucide-react";

import { useToast } from "../hooks/useToast";
import { cn } from "../utils/cn";
import { apiUploadScan } from "../services/api";

const SLOTS = ["FRONT", "BACK", "SIDE", "TOP", "BOTTOM"] as const;

const SAMPLE_IMAGES = [
  "https://images.unsplash.com/photo-1584473457406-6240486418e9?w=500&q=80",
  "https://images.unsplash.com/photo-1601599963565-b7f49deb4a86?w=500&q=80",
  "https://images.unsplash.com/photo-1620574387735-3624d75b2dbc?w=500&q=80",
  "https://images.unsplash.com/photo-1610725664285-7c57e6eeac3f?w=500&q=80",
  "https://images.unsplash.com/photo-1583947581924-860bda6a26df?w=500&q=80",
];

interface Shot {
  slot: string;
  url: string;
  publicId?: string;
  quality: {
    brightness: number;
    sharpness: number;
    perspective: number;
  };
}

export default function ScanPage() {
  const navigate = useNavigate();
  const { push } = useToast();

  const fileRef = useRef<HTMLInputElement>(null);

  const [shots, setShots] = useState<Shot[]>([]);
  const [dragging, setDragging] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState("");

  const category = "all";

  // Upload image to FastAPI /api/v1/scan/upload
  const uploadAndScan = async (file: File) => {
    // Upload + run full OCR/rule pipeline, returns ScanRecord
    return apiUploadScan(file, category);
  };

  // Add image preview to the page (no upload yet — upload happens on Analyze)
  const addShot = async (file?: File) => {
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      push("error", "Invalid file", "Please select a JPG, PNG, or WebP image.");
      return;
    }

    const slot = SLOTS[shots.length % SLOTS.length];
    const url = URL.createObjectURL(file);

    setShots((prev) => [
      ...prev,
      {
        slot,
        url,
        quality: { brightness: 90, sharpness: 90, perspective: 90 },
        _file: file,
      } as Shot & { _file: File },
    ]);

    push("success", "Image added", `${slot} view ready for analysis`);
  };

  // Drag and drop
  const handleDrop = (
    e: React.DragEvent
  ) => {
    e.preventDefault();

    setDragging(false);

    const file =
      e.dataTransfer.files?.[0];

    if (file) {
      void addShot(file);
    }
  };

  const removeShot = (idx: number) => {
    setShots((prev) =>
      prev.filter(
        (_, i) => i !== idx
      )
    );
  };

  const overallQuality = (
    q: Shot["quality"]
  ) =>
    Math.round(
      (q.brightness +
        q.sharpness +
        q.perspective) /
        3
    );

  // Upload to real backend and navigate to report
  const startAnalysis = async () => {
    if (shots.length === 0) {
      push("error", "No images captured", "Add at least one image before starting analysis.");
      return;
    }

    const firstShot = shots[0] as Shot & { _file?: File };
    if (!firstShot._file) {
      push("error", "No file", "Please add an image using the upload button.");
      return;
    }

    try {
      setAnalyzing(true);
      setProgress(10);
      setProgressLabel("Uploading image to backend…");

      // Simulate progress stages while backend processes
      const stages: [number, number, string][] = [
        [10, 30, "Uploading image to backend…"],
        [30, 60, "Running OCR extraction…"],
        [60, 80, "Evaluating compliance rules…"],
        [80, 95, "Generating report…"],
      ];

      let stageIdx = 0;

      const advanceProgress = () => {
        if (stageIdx >= stages.length) return;
        const [from, to, label] = stages[stageIdx];
        setProgressLabel(label);
        let p = from;
        const iv = setInterval(() => {
          p += 1;
          setProgress(Math.min(p, to - 1));
          if (p >= to - 2) {
            clearInterval(iv);
          }
        }, 60);
        stageIdx++;
      };

      advanceProgress();

      // Real backend call — runs OCR + rule engine synchronously
      const scanResult = await uploadAndScan(firstShot._file);

      setProgress(100);
      setProgressLabel("Complete!");

      push("success", "Scan complete", `Compliance: ${scanResult.compliance_pct?.toFixed(1)}%`);

      setTimeout(() => {
        navigate(`/report/${scanResult.id}`);
      }, 400);
    } catch (error) {
      console.error("Scan error:", error);
      setAnalyzing(false);
      push(
        "error",
        "Scan failed",
        error instanceof Error ? error.message : "Could not process the image."
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="font-display text-2xl font-bold text-text-1">
          Start New Inspection
        </h1>

        <p className="mt-1 text-sm text-text-2">
          Capture or upload a packaged commodity label for AI-assisted
          verification.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left side */}
        <div className="space-y-6 lg:col-span-2">
          {/* Upload area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() =>
              setDragging(false)
            }
            onDrop={handleDrop}
            className={cn(
              "flex flex-col items-center justify-center rounded-xl border-2 border-dashed bg-paper-card px-6 py-12 text-center transition-colors",
              dragging
                ? "border-cyan-500 bg-cyan-50/40"
                : "border-line"
            )}
          >
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500/15 to-violet-500/15">
              <UploadCloud
                size={26}
                className="text-cyan-600"
              />
            </div>

            <p className="mt-4 font-display text-base font-bold text-text-1">
              Drag &amp; drop a label image here
            </p>

            <p className="mt-1 text-sm text-text-2">
              Supports JPG, PNG, WebP · Multiple images allowed
              for different sides
            </p>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={() =>
                  setCameraOpen(true)
                }
                className="flex items-center gap-2 rounded-lg bg-ink-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-ink-800"
              >
                <Camera size={16} />
                Capture with Camera
              </button>

              <button
                type="button"
                onClick={() =>
                  fileRef.current?.click()
                }
                className="flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2.5 text-sm font-semibold text-text-1 hover:bg-paper"
              >
                <UploadCloud size={16} />
                Upload Image
              </button>

              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file =
                    e.target.files?.[0];

                  if (file) {
                    void addShot(file);
                  }

                  e.target.value = "";
                }}
              />
            </div>
          </div>

          {/* Images */}
          {shots.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {shots.map(
                (shot, idx) => {
                  const q =
                    overallQuality(
                      shot.quality
                    );

                  return (
                    <div
                      key={`${shot.publicId ?? shot.url}-${idx}`}
                      className="animate-fade-up overflow-hidden rounded-xl border border-line bg-paper-card"
                    >
                      <div className="relative">
                        <img
                          src={shot.url}
                          alt={shot.slot}
                          className="h-40 w-full object-cover"
                        />

                        <span className="absolute left-2 top-2 rounded-md bg-ink-900/80 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-white">
                          {shot.slot}
                        </span>

                        <div className="absolute right-2 top-2 flex gap-1">
                          <button
                            type="button"
                            className="rounded-md bg-white/90 p-1.5 text-text-2 hover:text-text-1"
                          >
                            <Eye
                              size={13}
                            />
                          </button>

                          <button
                            type="button"
                            className="rounded-md bg-white/90 p-1.5 text-text-2 hover:text-text-1"
                          >
                            <Crop
                              size={13}
                            />
                          </button>

                          <button
                            type="button"
                            className="rounded-md bg-white/90 p-1.5 text-text-2 hover:text-text-1"
                          >
                            <RotateCw
                              size={13}
                            />
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              removeShot(
                                idx
                              )
                            }
                            className="rounded-md bg-white/90 p-1.5 text-bad-600 hover:text-bad-700"
                          >
                            <Trash2
                              size={13}
                            />
                          </button>
                        </div>
                      </div>

                      <div className="p-3.5">
                        <div className="mb-2 flex items-center justify-between">
                          <p className="text-xs font-semibold text-text-2">
                            Image Quality
                          </p>

                          <span
                            className={cn(
                              "text-xs font-bold",
                              q >= 90
                                ? "text-ok-600"
                                : q >= 75
                                ? "text-warn-600"
                                : "text-bad-600"
                            )}
                          >
                            {q >= 90
                              ? "Excellent"
                              : q >= 75
                              ? "Good"
                              : "Needs Retake"}
                          </span>
                        </div>

                        {(
                          [
                            "brightness",
                            "sharpness",
                            "perspective",
                          ] as const
                        ).map(
                          (k) => (
                            <div
                              key={k}
                              className="mb-1.5 flex items-center gap-2 text-[11px]"
                            >
                              <span className="w-20 capitalize text-text-3">
                                {k}
                              </span>

                              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-paper">
                                <div
                                  className="h-full rounded-full bg-cyan-500"
                                  style={{
                                    width: `${shot.quality[k]}%`,
                                  }}
                                />
                              </div>

                              <span className="w-8 text-right font-tabular text-text-2">
                                {shot
                                  .quality[
                                  k
                                  ]}
                                %
                              </span>
                            </div>
                          )
                        )}

                        <div className="mt-2 flex items-center gap-1.5 text-xs font-medium text-ok-600">
                          <CheckCircle2
                            size={13}
                          />
                          Image uploaded and suitable for analysis
                        </div>
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          )}
        </div>

        {/* Right side */}
        <div className="space-y-4">
          {/* Metadata */}
          <div className="rounded-xl border border-line bg-paper-card p-5">
            <h3 className="font-display text-sm font-bold text-text-1">
              Scan metadata
            </h3>

            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center gap-2.5">
                <Hash
                  size={15}
                  className="text-text-3"
                />

                <div>
                  <p className="text-xs text-text-3">
                    Scan ID
                  </p>

                  <p className="font-code text-xs font-medium text-text-1">
                    Pending — assigned on submit
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <Clock3
                  size={15}
                  className="text-text-3"
                />

                <div>
                  <p className="text-xs text-text-3">
                    Date &amp; time
                  </p>

                  <p className="text-xs font-medium text-text-1">
                    {new Date().toLocaleString(
                      "en-IN"
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <MapPin
                  size={15}
                  className="text-text-3"
                />

                <div>
                  <p className="text-xs text-text-3">
                    Location (GPS)
                  </p>

                  <p className="text-xs font-medium text-text-1">
                    30.3165° N, 78.0322° E · Dehradun
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <Smartphone
                  size={15}
                  className="text-text-3"
                />

                <div>
                  <p className="text-xs text-text-3">
                    Device
                  </p>

                  <p className="text-xs font-medium text-text-1">
                    Field Tablet · MANAK SETU App v2.4
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Analysis */}
          <div className="rounded-xl border border-line bg-gradient-to-br from-ink-900 to-ink-800 p-5 text-white">
            <div className="flex items-center gap-2">
              <Sparkles
                size={16}
                className="text-cyan-400"
              />

              <h3 className="font-display text-sm font-bold">
                Ready to analyze
              </h3>
            </div>

            <p className="mt-2 text-xs leading-relaxed text-ink-600">
              {shots.length} image
              {shots.length !== 1
                ? "s"
                : ""}{" "}
              captured. AI will run OCR, extract mandatory
              declarations, and match findings against active
              Legal Metrology rules.
            </p>

            <button
              type="button"
              onClick={startAnalysis}
              disabled={analyzing}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-500 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {analyzing
                ? `${progressLabel} ${progress}%`
                : "Analyze Product"}
            </button>

            {analyzing && (
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-400 transition-all"
                  style={{
                    width: `${progress}%`,
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Camera modal */}
      {cameraOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/70 p-4">
          <div className="w-full max-w-md animate-fade-up rounded-xl bg-ink-900 p-4 text-white">
            <div className="flex items-center justify-between">
              <p className="font-display text-sm font-bold">
                Camera capture (simulated)
              </p>

              <button
                type="button"
                onClick={() =>
                  setCameraOpen(false)
                }
              >
                <X size={18} />
              </button>
            </div>

            <div className="relative mt-3 flex h-64 items-center justify-center overflow-hidden rounded-lg bg-ink-950">
              <Camera
                size={40}
                className="text-ink-600"
              />

              <div className="absolute inset-x-6 top-0 h-0.5 animate-scan-sweep bg-cyan-400" />

              <div className="absolute inset-6 rounded-lg border-2 border-dashed border-cyan-400/50" />
            </div>

            <button
              type="button"
              onClick={() => {
                // Camera remains simulated for now
                const slot =
                  SLOTS[
                    shots.length %
                      SLOTS.length
                  ];

                const url =
                  SAMPLE_IMAGES[
                    shots.length %
                      SAMPLE_IMAGES.length
                  ];

                const quality = {
                  brightness: 90,
                  sharpness: 90,
                  perspective: 90,
                };

                setShots((prev) => [
                  ...prev,
                  {
                    slot,
                    url,
                    quality,
                  },
                ]);

                push(
                  "success",
                  "Photo captured",
                  `${slot} view captured (simulated camera)`
                );

                setCameraOpen(false);
              }}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-500 py-2.5 text-sm font-semibold text-ink-950 hover:bg-cyan-400"
            >
              <Camera size={16} />
              Capture Photo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}